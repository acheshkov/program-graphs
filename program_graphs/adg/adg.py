from collections import defaultdict
from typing import Callable, Dict, List, Tuple, Mapping, Set, Optional, Any
from tree_sitter import Node  # type: ignore
from itertools import product, chain
import networkx as nx  # type: ignore
from tabulate import tabulate
from program_graphs.types import NodeID, ASTNode
from program_graphs.ddg.parser.java.utils import VarName, Variable, read_write_variables_with_types
# from program_graphs.slicing.all_paths import only_full_paths_from_node, find

class ADG(nx.DiGraph):
    'Any Dependency Graph'

    def __init__(self):
        super().__init__()
        self._continue_nodes: List[NodeID] = []
        self._break_nodes: List[NodeID] = []
        self._return_nodes: List[NodeID] = []
    
    def add_ast_node(self, ast_node: ASTNode, name: str=None) -> NodeID:
        node = self.add_node(name)
        nx.set_node_attributes(self, {node: {'ast_node': ast_node}})
        return node

    def add_node(self, name: str=None) -> NodeID:
        next_id = len(self.nodes()) + 1
        super().add_node(next_id)
        if name is not None:
            nx.set_node_attributes(self, {next_id: {'name': name}})
        return next_id

    def push_return_node(self, node: NodeID) -> None:
        self._return_nodes.append(node)

    def push_break_node(self, node: NodeID) -> None:
        self._break_nodes.append(node)

    def push_continue_node(self, node: NodeID) -> None:
        self._continue_nodes.append(node)

    def pop_continue_node(self) -> Optional[NodeID]:
        if len(self._continue_nodes) == 0:
            return None
        return self._continue_nodes.pop()

    def pop_break_node(self) -> Optional[NodeID]:
        if len(self._break_nodes) == 0:
            return None
        return self._break_nodes.pop()

    
    def get_entry_node(self) -> NodeID:
        return 1
    
    def get_exit_node(self) -> NodeID:
        exits = [n for n in self.nodes() if self.out_degree(n) == 0 and self.in_degree(n) > 0]
        assert len(exits) == 1
        return exits[0]

    def wire_return_nodes(self) -> None:
        if len(self._return_nodes) == 0: 
            return
        exit_node = self.get_exit_node()
        while len(self._return_nodes) > 0:
            return_node = self._return_nodes.pop()
            self.add_edge(return_node, exit_node, cflow=True)


    def to_cfg(self) -> nx.DiGraph:
        copy = self.copy()
        copy.remove_edges_from([(a, b) for (a, b, cflow) in self.edges(data='cflow') if cflow is not True])
        copy.remove_nodes_from(list(nx.isolates(copy)))
        return copy
    
    def to_cdg(self) -> nx.DiGraph:
        copy = self.copy()
        copy.remove_edges_from([(a, b) for (a, b, cdep) in self.edges(data='cdep') if cdep is not True])
        copy.remove_nodes_from(list(nx.isolates(copy)))
        return copy

    def to_ddg(self) -> nx.DiGraph:
        copy = self.copy()
        copy.remove_edges_from([(a, b) for (a, b, ddep) in self.edges(data='ddep') if ddep is not True])
        copy.remove_nodes_from(list(nx.isolates(copy)))
        return copy

    def __str__(self) -> str:
        def _data_to_label(dict) -> str:
            labels = []
            if dict.get('syntax', False) is True:
                labels.append('syntax')
            if dict.get('cflow', False) is True:
                labels.append('control-flow')
            if dict.get('cdep', False) is True:
                labels.append('control-dep')
            if dict.get('ddep', False) is True:
                labels.append('data-dep')
            return ','.join(labels)
        
        def _node_label(adg: ADG, node: NodeID) -> str:
            if adg.nodes[node].get('name') is not None:
                return f'{adg.nodes[node].get("name")}:{node}'
            if adg.nodes[node].get('ast_node') is not None:
                return f'{adg.nodes[node].get("ast_node").type}:{node}'
            return str(node)

        table = [(_node_label(self, a), '->', _node_label(self, b), _data_to_label(edge_data)) for  (a, b, edge_data) in self.edges(data=True)]
        headers = ['From', '', 'To', 'Dependencies']
        return tabulate(
            table,
            headers=headers
        )




# def is_suitable_path(path, w_var_name, node2read_var, node2write_var) -> bool:
#     for n in path[1: -1]:
#         if w_var_name in node2write_var[n]:
#             return False
#     return True

# def _mk_predicate(node2write_var, node2read_var, var_name: str) -> Callable[[NodeID], Optional[bool]]:
#     fst = lambda ss: [fst for fst, _ in ss]
#     def _predicate(node) -> Optional[bool]:
#         if var_name in fst(node2read_var[node]):
#             return True
#         if var_name in fst(node2write_var[node]):
#             return False
#         return None

#     return _predicate

        
# def figure_out_data_dependencies(
#     g: ADG,
#     node2read_var: Mapping[NodeID, Set[Variable]],
#     node2write_var: Mapping[NodeID, Set[Variable]]
# ) -> Mapping[Tuple[NodeID, NodeID], Set[Variable]]:
#     print("figure_out_data_dependencies")
#     cfg = g.to_cfg()
#     data_dependency: Mapping[Tuple[NodeID, NodeID], Set[Variable]] = defaultdict(set)
#     write_operations: List[Tuple[Variable, NodeID]] = chain.from_iterable([product(vars, [node]) for node, vars in node2write_var.items()])
#     read_operations: List[Tuple[Variable, NodeID]] = chain.from_iterable([product(vars, [node]) for node, vars in node2read_var.items()])
#     # print("write_operations", list(write_operations))
#     # print("size write_operations", list(write_operations))
#     write_operations = list(write_operations)
#     read_operations = list(read_operations)


#     for ((w_var_name, w_var_type), node_w) in write_operations:
#         # print(w_var_name, w_var_type, node_w)
#         _predicate = _mk_predicate(node2write_var, node2read_var, w_var_name)
#         nodes = find(cfg, node_w, _predicate)
#         # print(list(nodes))
#         for data_dependent_node in nodes:
#             # print((node_w, data_dependent_node))
#             data_dependency[(node_w, data_dependent_node)].add((w_var_name, w_var_type))


#     # for ((w_var_name, w_var_type), node_w) in write_operations:
#     #     for ((v_var_name, v_var_type), node_r) in read_operations:
#     #         if w_var_name != v_var_name: continue
#     #         # print(node_w, node_r)
#     #         for path in nx.algorithms.all_simple_paths(cfg, node_w, node_r):
#     #             if is_suitable_path(path, w_var_name, node2read_var, node2write_var):
#     #                 print(f'node {node_w} affect {node_r} wrt {w_var_name}')
#     #                 data_dependency[(node_w, node_r)].add((w_var_name, w_var_type))
#     #                 break

    
#     # for ((var_name, var_type), node) in write_operations:
#     #     # print( ((var_name, var_type), node))
#     #     paths_from_node = only_full_paths_from_node(cfg, node)
#     #     print(f'from node {node} ,var {var_name} we have {len(paths_from_node)} paths')
#     #     for path in paths_from_node:
#     #         for data_dependent_node in find_dependent_stmt(var_name, node2read_var, node2write_var, path[1:]):
#     #             data_dependency[(node, data_dependent_node)].add((var_name, var_type))
#     return data_dependency



   

def mk_empty_adg() -> ADG:
    return ADG()







# def add_depenencies_to_graph(g: ADG, node: NodeID, var_table: VarTable, dd: Mapping[Tuple[NodeID, NodeID], Set[Variable]]):
#     read_vars = nx.get_node_attributes(g, 'read_vars')
    
#     if read_vars.get(node, None) is None:
#         return
#     # print("read_vars", node, read_vars[node])
#     # print("var_table", var_table)
#     for (var_name, var_type) in read_vars[node]:
#         for write_node in var_table[var_name]:
#             dd[(write_node, node)].add((var_name, var_type))
        


