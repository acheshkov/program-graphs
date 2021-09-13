from program_graphs import FCFG
from program_graphs.cfg.parser.java.utils import extract_code
from typing import Tuple, List, Mapping, Set, Iterator, Any
from program_graphs.types import NodeID
from tree_sitter import Node as Statement  # type: ignore
import networkx as nx  # type: ignore
from itertools import chain


Variable = str
Path = List[NodeID]
DataDependency = Tuple[NodeID, NodeID, Variable]
WriteIdentifier = Any
ReadIdentifier = Any


def identifiers_df(node: Statement, depth: int = 0) -> List[Statement]:
    if node.type == 'assignment_expression' and depth > 0:
        return []
    if node.type == 'identifier':
        return [node]

    return list(chain.from_iterable(
        [identifiers_df(c, depth + 1) for c in node.children]
    ))


def left_most_identifier(node: Statement) -> Statement:
    return identifiers_df(node)[0]





def _write_read_indetifiers_of_children(
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]:
    r, w = [], []
    for child in node.children:
        _r, _w = write_read_identifiers(child, source_code)
        r += _r
        w += _w
    return r, w


def write_read_identifiers_assignment_expression(
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]:
    lm = left_most_identifier(node)
    operator_node = node.child_by_field_name('operator')
    operator = extract_code(operator_node.start_byte, operator_node.end_byte, source_code)
    l_write, l_read = write_read_identifiers(node.child_by_field_name('left'), source_code)
    r_write, r_read = write_read_identifiers(node.child_by_field_name('right'), source_code)
    write = l_write + r_write + [lm]
    if operator == '=':
        read = [s for s in l_read if s != lm] + r_read
    else:
        read = [s for s in l_read] + r_read
    return write, read


def write_read_identifiers_varaible_declarator(
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]:
    lm = left_most_identifier(node)
    l_write, l_read = write_read_identifiers(node.child_by_field_name('name'), source_code)
    r_write, r_read = write_read_identifiers(node.child_by_field_name('value'), source_code)
    write = l_write + r_write + [lm]
    read = [s for s in l_read if s != lm] + r_read
    return write, read


def write_read_identifiers_update_expression(
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]:
    lm = left_most_identifier(node)
    write, read = _write_read_indetifiers_of_children(node, source_code)
    write = write + [lm]
    return write, read


def write_read_identifiers(
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]: 
    if node is None:
        return [], []

    if node.type in ['lambda_expression']:
        return [], []

    if node.type == 'assignment_expression':
        return write_read_identifiers_assignment_expression(node, source_code)

    if node.type == 'variable_declarator':
        return write_read_identifiers_varaible_declarator(node, source_code)

    if node.type == 'update_expression':
        return write_read_identifiers_update_expression(node, source_code)

    if node.type == 'field_access':
        return write_read_identifiers(node.child_by_field_name('object'), source_code)

    if node.type == 'class_declaration':
        return write_read_identifiers(node.child_by_field_name('body'), source_code)

    if node.type == 'method_invocation':
        w_1, r_1 = write_read_identifiers(node.child_by_field_name('object'), source_code)
        w_2, r_2 = write_read_identifiers(node.child_by_field_name('arguments'), source_code)
        return w_1 + w_2, r_1 + r_2

    if node.type == 'method_declaration':
        w, r = write_read_identifiers(node.child_by_field_name('body'), source_code)
        formal_parameters = identifiers_df(node.child_by_field_name('parameters'))
        return w + formal_parameters, r

    if node.type == 'object_creation_expression':
        arguments = identifiers_df(node.child_by_field_name('arguments'))
        return [], arguments

    if node.type == 'catch_formal_parameter':
        formal_parameters = identifiers_df(node)
        return formal_parameters, []

    if node.type == 'resource':
        return identifiers_df(node.child_by_field_name('name')), []

    identifier_exceptions = [
        'labeled_statement', 'break_statement', 'continue_statement',
        'method_declaration', 'class_declaration'
    ]
    if node.type == 'identifier' and node.parent.type not in identifier_exceptions:
        return [], [node]

    return _write_read_indetifiers_of_children(node, source_code)


def statement_to_string(node: Statement, source_code: bytes) -> str:
    return extract_code(node.start_byte, node.end_byte, source_code)


def read_write_variables(node: Statement, source_code: bytes) -> Tuple[Set[Variable], Set[Variable]]:
    w, r = write_read_identifiers(node, source_code)
    w = [statement_to_string(s, source_code) for s in w]
    r = [statement_to_string(s, source_code) for s in r]
    return set(r), set(w)


def get_all_variables(node: Statement, source_code: bytes) -> Set[Variable]:
    read_vars, write_vars = read_write_variables(node, source_code)
    return write_vars | read_vars


def get_variables_by_stmt(
    fcfg: FCFG,
    source_code: bytes
) -> Tuple[Mapping[NodeID, Set[Variable]], Mapping[NodeID, Set[Variable]]]:
    read_vars_map: Mapping[NodeID, Set[Variable]] = {}
    write_vars_map: Mapping[NodeID, Set[Variable]] = {}
    for node_id, stmt in fcfg.nodes(data='statement'):
        read_vars, write_vars = read_write_variables(stmt, source_code)
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

