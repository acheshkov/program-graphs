from collections import defaultdict
from typing import Iterable, Tuple, Mapping, Set, Optional, Dict
import networkx as nx  # type: ignore
from program_graphs.types import NodeID
from program_graphs.ddg.parser.java.utils import VarName, VarType, Variable, read_write_variables_with_types
from program_graphs.adg.adg import ADG
from sys import setrecursionlimit

setrecursionlimit(5000)

VarTable = Dict[VarName, Set[NodeID]]  # Mapping from variable name to list of nodes that wrote this variable recently


def bind_variables(g: ADG, source_code: bytes) -> Tuple[Mapping[NodeID, Set[Variable]], Mapping[NodeID, Set[Variable]]]:
    node2read_vars: Mapping[NodeID, Set[Variable]] = defaultdict(set)
    node2write_vars: Mapping[NodeID, Set[Variable]] = defaultdict(set)
    for node, ast_node in g.nodes(data='ast_node'):
        if ast_node is None:
            continue
        if len([1 for (_, _, syntax) in g.out_edges(node, data='syntax') if syntax is True]) > 0:
            continue
        read_vars, write_vars = read_write_variables_with_types(ast_node, source_code)
        node2read_vars[node].update(read_vars)
        node2write_vars[node].update(write_vars)
        nx.set_node_attributes(g, {node: {'read_vars': read_vars, 'write_vars': write_vars}})
    return node2read_vars, node2write_vars


def _fst(ss: Iterable[Tuple[VarName, VarType]]) -> Iterable[VarName]:
    return [fst for fst, _ in ss]


def add_data_dependency_layer(g: ADG, source_code: bytes) -> None:
    ''' Figure out and add Data Dependency relations to ADG graph '''
    node2read_var, _ = bind_variables(g, source_code)
    data_dependencies: Mapping[NodeID, VarTable] = kuzma_blud(g.to_cfg(), g.get_entry_node())

    for node, var_table in data_dependencies.items():
        for var_name, write_nodes in var_table.items():
            if var_name not in _fst(node2read_var[node]):
                continue
            for write_node in write_nodes:
                create_or_update_data_depependency_link(g, write_node, node, var_name)


def create_or_update_data_depependency_link(g: nx.DiGraph, node_from: NodeID, node_to: NodeID, var: VarName) -> None:
    edge_data = g.get_edge_data(node_from, node_to, None)
    if edge_data is None or edge_data.get('ddep', None) is None:
        g.add_edge(node_from, node_to, ddep=True, vars=set([var]))
    else:
        vars = edge_data['vars']
        vars.add(var)


def set_diff(s1: Set[int], s2: Set[int]) -> Optional[Set[int]]:
    ''' if first set entirely contains second set then return None, else return union of both'''
    union = s1 | s2
    if len(union) == len(s1):
        return None
    return union


def merge_var_table_if_requried(t1: VarTable, t2: VarTable) -> Optional[VarTable]:
    ''' Merge tables difference to t1 (update in place). If t2 has no new information then return None'''
    new_information = False
    for k, v in t2.items():
        if k not in t1:
            t1[k] = v
            new_information = True
        else:
            diff = set_diff(t1[k], t2[k])
            if diff is None:
                continue
            t1[k] = diff
            new_information = True

    if not new_information:
        return None
    return t1


def update_var_table(tb: VarTable, var_name: VarName, nodes: Set[NodeID]) -> None:
    tb[var_name] = nodes


def copy_and_update_var_table(tb: VarTable, g: ADG, node: NodeID) -> VarTable:
    new_table: VarTable = tb.copy()
    write_vars = g.nodes[node].get('write_vars')
    for (var_name, _) in (write_vars or []):
        update_var_table(new_table, var_name, set([node]))
    return new_table


def kuzma_blud(
    g: ADG,
    node: NodeID,
    parent_var_table: VarTable = defaultdict(set),
    global_state: Mapping[NodeID, VarTable] = None
) -> Mapping[NodeID, VarTable]:
    global_state = (global_state or defaultdict(lambda: defaultdict(set)))

    if merge_var_table_if_requried(global_state[node], parent_var_table) is not None:
        current_var_table = copy_and_update_var_table(parent_var_table, g, node)
        for s in g.successors(node):
            kuzma_blud(g, s, current_var_table, global_state)
    else:
        not_visited_successors = [s for s in g.successors(node) if global_state.get(s) is None]
        current_var_table = copy_and_update_var_table(parent_var_table, g, node)
        for s in not_visited_successors:
            kuzma_blud(g, s, current_var_table, global_state)

    return global_state
