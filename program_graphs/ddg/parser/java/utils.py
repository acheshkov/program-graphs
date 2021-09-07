from program_graphs.cfg.parser.java.utils import extract_code
from program_graphs import FCFG
from typing import Tuple, List, Mapping, Set, Iterator
from program_graphs.types import NodeID
from tree_sitter import Node as Statement  # type: ignore
import networkx as nx  # type: ignore
from itertools import chain


Variable = str
Path = List[NodeID]
DataDependency = Tuple[NodeID, NodeID, Variable]


def get_variables_written(node: Statement, source_code: bytes) -> Set[Variable]:
    if node is None:
        return set()
    if node.type == 'lambda_expression':
        return set()
    if node.type == 'binary_expression':
        return set()
    if node.type in ['assignment_expression']:
        return get_variables_written(node.child_by_field_name('left'), source_code)
    if node.type == 'resource':
        return get_variables_written(node.child_by_field_name('name'), source_code)
    if node.type == 'variable_declarator':
        return get_variables_written(node.child_by_field_name('name'), source_code)
    if node.type == 'identifier' and node.parent.type not in ['labeled_statement', 'break_statement', 'continue_statement']:
        return set([extract_code(node.start_byte, node.end_byte, source_code)])

    variables = set()
    for child in node.children:
        variables |= get_variables_written(child, source_code)

    return variables


def get_variables_read(node: Statement, source_code: bytes) -> Set[Variable]:
    if node is None:
        return set()
    if node.type in ['lambda_expression', 'catch_formal_parameter']:
        return set()
    if node.type in ['assignment_expression']:
        return get_variables_read(node.child_by_field_name('right'), source_code)
    if node.type == 'class_body' and node.parent.type == 'object_creation_expression':
        return set()
    if node.type == 'resource':
        return get_variables_read(node.child_by_field_name('value'), source_code)
    if node.type == 'method_invocation':
        subject = get_variables_read(node.child_by_field_name('object'), source_code)
        args = get_variables_read(node.child_by_field_name('arguments'), source_code)
        return subject | args
    if node.type == 'variable_declarator':
        return get_variables_read(node.child_by_field_name('value'), source_code)
    if node.type == 'identifier' and node.parent.type not in ['labeled_statement', 'break_statement', 'continue_statement']:
        return set([extract_code(node.start_byte, node.end_byte, source_code)])

    variables = set()
    for child in node.children:
        variables |= get_variables_read(child, source_code)

    return variables


def get_all_variables(node: Statement, source_code: bytes) -> Set[Variable]:
    write_vars = get_variables_written(node, source_code)
    read_vars = get_variables_read(node, source_code)
    return write_vars | read_vars


def get_variables_by_stmt(
    fcfg: FCFG,
    source_code: bytes
) -> Tuple[Mapping[NodeID, Set[Variable]], Mapping[NodeID, Set[Variable]]]:
    read_vars_map: Mapping[NodeID, Set[Variable]] = {}
    write_vars_map: Mapping[NodeID, Set[Variable]] = {}
    for node_id, stmt in fcfg.nodes(data='statement'):
        read_vars = get_variables_read(stmt, source_code)
        write_vars = get_variables_written(stmt, source_code)
        read_vars_map[node_id] = read_vars  # type: ignore
        write_vars_map[node_id] = write_vars  # type: ignore
    return read_vars_map, write_vars_map


def get_data_dependencies(fcfg: FCFG, source_code: bytes) -> Set[DataDependency]:
    read_vars_map, write_vars_map = get_variables_by_stmt(fcfg, source_code)
    data_dependencies: Set[DataDependency] = set()
    for node_id in fcfg.nodes():
        for w_var in write_vars_map[node_id]:
            paths = all_paths_from(fcfg, node_id)
            for path in paths:
                for dependent_node in find_dependent_stmt(w_var, read_vars_map, write_vars_map, path[1:]):
                    data_dependencies.add((node_id, dependent_node, w_var))
    return data_dependencies


def all_paths_from(g: nx.DiGraph, node: NodeID, mb_visited_nodes: List[NodeID] = None) -> List[Path]:
    visited_nodes: List[NodeID] = mb_visited_nodes or []
    successors = [s for s in g.successors(node) if s not in visited_nodes]
    if len(visited_nodes) == 0 and len(successors) == 0:
        return []
    visited_nodes.append(node)
    if len(successors) == 0:
        return [[node]]
    paths = [all_paths_from(g, s, visited_nodes) for s in successors]
    flatten_paths = chain(*paths)
    return [[node] + path for path in flatten_paths]


def find_dependent_stmt(
    var: Variable,
    read_vars_map: Mapping[NodeID, Set[Variable]],
    write_vars_map: Mapping[NodeID, Set[Variable]],
    path: List[NodeID]
) -> Iterator[NodeID]:
    for node in path:
        if var in read_vars_map[node]:
            yield node
        if var in write_vars_map[node]:
            break
