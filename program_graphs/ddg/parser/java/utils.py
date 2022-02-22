from collections import defaultdict
from program_graphs import FCFG
from program_graphs.cfg.parser.java.utils import extract_code
from typing import Callable, Tuple, List, Mapping, Set, Iterator, Any, Optional, Iterable, Dict
from program_graphs.types import NodeID
from tree_sitter import Node as Statement  # type: ignore
import networkx as nx  # type: ignore
from itertools import chain
from program_graphs.utils.graph import filter_nodes

VarName = str
VarType = str
Variable = Tuple[VarName, VarType]
Path = List[NodeID]
DataDependency = Tuple[NodeID, NodeID, Set[Variable]]
WriteIdentifier = Any
ReadIdentifier = Any
Identifier = Any


# def filter_nodes(node: Statement, node_types: List[str]) -> List[Statement]:
#     if node is None:
#         return []
#     nodes = list(chain.from_iterable(
#         [filter_nodes(ch, node_types) for ch in node.children]
#     ))
#     if node.type in node_types:
#         return [node] + nodes
#     return nodes


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


def find_types_and_aggregate(node: Statement, source_code: bytes) -> VarType:
    var_types = filter_nodes(node, ['integral_type', 'type_identifier', 'boolean_type', 'floating_point_type'])
    return ','.join(
        map(
            lambda node: extract_code(node.start_byte, node.end_byte, source_code),
            var_types
        )
    )


def get_type(node: Identifier, source_code: bytes) -> Optional[VarType]:
    if (node.parent.type in ['formal_parameter']):
        return find_types_and_aggregate(node.parent.child_by_field_name('type'), source_code)

    if (node.parent.type in ['catch_formal_parameter', 'enhanced_for_statement']):
        return find_types_and_aggregate(node.parent, source_code)

    if (node.parent.parent.type == 'local_variable_declaration'):
        return find_types_and_aggregate(node.parent.parent.child_by_field_name('type'), source_code)

    return None


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
    identifier_is_object = lm.parent.type in ['array_access', 'field_access']
    if operator == '=' and not identifier_is_object:
        read = [s for s in l_read if s != lm] + r_read
    else:
        read = [s for s in l_read] + r_read
    return write, read


def write_read_identifiers_variable_declarator(
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


def write_read_identifiers(  # noqa
    node: Statement,
    source_code: bytes
) -> Tuple[List[WriteIdentifier], List[ReadIdentifier]]:
    # print(node)
    if node is None:
        return [], []

    if node.type in ['lambda_expression']:
        return [], []

    if node.type == 'assignment_expression':
        return write_read_identifiers_assignment_expression(node, source_code)

    if node.type == 'variable_declarator':
        return write_read_identifiers_variable_declarator(node, source_code)

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

    if node.type in ['formal_parameter', 'catch_formal_parameter', 'resource']:
        names = filter_nodes(node.child_by_field_name('name'), ['identifier'])
        return names, []

    if node.type == 'object_creation_expression':
        arguments = identifiers_df(node.child_by_field_name('arguments'))
        return [], arguments

    if node.type == 'enhanced_for_statement':
        return identifiers_df(node.child_by_field_name('name')), identifiers_df(node.child_by_field_name('value'))

    identifier_exceptions = [
        'labeled_statement', 'break_statement', 'continue_statement',
        'method_declaration', 'class_declaration'
    ]
    if node.type == 'identifier' and node.parent.type not in identifier_exceptions and node.start_byte != node.end_byte:
        return [], [node]

    return _write_read_indetifiers_of_children(node, source_code)


def statement_to_string(node: Statement, source_code: bytes) -> str:
    return extract_code(node.start_byte, node.end_byte, source_code)


def read_write_variables(node: Statement, source_code: bytes) -> Tuple[Set[VarName], Set[VarName]]:
    w, r = write_read_identifiers(node, source_code)
    w = [statement_to_string(s, source_code) for s in w]
    r = [statement_to_string(s, source_code) for s in r]
    return set(r), set(w)


def read_write_variables_with_types(node: Statement, source_code: bytes) -> Tuple[Set[Variable], Set[Variable]]:
    w, r = write_read_identifiers(node, source_code)
    w = [(statement_to_string(s, source_code), get_type(s, source_code)) for s in w]
    r = [(statement_to_string(s, source_code), None) for s in r]
    return set(r), set(w)


def get_all_variables(node: Statement, source_code: bytes) -> Set[VarName]:
    read_vars, write_vars = read_write_variables(node, source_code)
    return write_vars | read_vars


def get_all_variables_with_types(node: Statement, source_code: bytes) -> Set[Variable]:
    read_vars, write_vars = read_write_variables_with_types(node, source_code)
    return write_vars | read_vars


def get_variables_by_stmt(
    fcfg: FCFG,
    source_code: bytes
) -> Tuple[Mapping[NodeID, Set[Variable]], Mapping[NodeID, Set[Variable]]]:
    read_vars_map: Mapping[NodeID, Set[Variable]] = {}
    write_vars_map: Mapping[NodeID, Set[Variable]] = {}
    for node_id, stmt in fcfg.nodes(data='statement'):
        read_vars, write_vars = read_write_variables_with_types(stmt, source_code)
        read_vars_map[node_id] = read_vars  # type: ignore
        write_vars_map[node_id] = write_vars  # type: ignore
    return read_vars_map, write_vars_map


def group_data_dependencies_by_edges(dependencies: List[DataDependency]) -> List[DataDependency]:
    edge_to_vars: Dict[Tuple[NodeID, NodeID], Set[Variable]] = defaultdict(set)
    for node_from, node_to, vars in dependencies:
        edge_to_vars[(node_from, node_to)] |= vars
    return [(node_from, node_to, vars) for ((node_from, node_to), vars) in edge_to_vars.items()]


def get_data_dependencies(fcfg: FCFG, source_code: bytes) -> List[DataDependency]:
    read_vars_map, write_vars_map = get_variables_by_stmt(fcfg, source_code)
    data_dependencies: List[DataDependency] = list()
    for node_id in fcfg.nodes():
        for w_var, w_var_type in write_vars_map[node_id]:
            paths = all_paths_from(fcfg, node_id)
            for path in paths:
                for dependent_node in find_dependent_stmt(w_var, read_vars_map, write_vars_map, path[1:]):
                    data_dependencies.append((node_id, dependent_node, set([(w_var, w_var_type)])))
    return group_data_dependencies_by_edges(
        data_dependencies
    )


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
    var: VarName,
    read_vars_map: Mapping[NodeID, Set[Variable]],
    write_vars_map: Mapping[NodeID, Set[Variable]],
    path: List[NodeID]
) -> Iterator[NodeID]:
    fst: Callable[[Iterable[Tuple[Any, Any]]], Iterable[Any]] = lambda ss: [fst for fst, snd in ss]
    for node in path:
        if var in fst(read_vars_map[node]):
            yield node
        if var in fst(write_vars_map[node]):
            break


def get_declared_variables_nodes(node: Statement, source_code: bytes) -> List[Statement]:
    if node.type == 'variable_declarator':
        return [left_most_identifier(node)]
    if node.type in ['catch_formal_parameter', 'formal_parameter', 'resource']:
        return filter_nodes(node, ['identifier'])
    vars = list()
    for child in node.children:
        vars += get_declared_variables_nodes(child, source_code)
    return vars


def get_declared_variables(node: Statement, source_code: bytes) -> Set[VarName]:
    return set(map(
        lambda stmt: statement_to_string(stmt, source_code),
        get_declared_variables_nodes(node, source_code))
    )
