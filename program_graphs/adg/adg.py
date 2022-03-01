from typing import List, Mapping, Optional, Tuple, Any, Dict, Optional
import networkx as nx  # type: ignore
from tabulate import tabulate
from program_graphs.types import NodeID, ASTNode

Label = str

class ADG(nx.DiGraph):
    'Any Dependency Graph'

    def __init__(self) -> None:
        super().__init__()
        self._continue_nodes: Dict[NodeID, Optional[Label]] = {}
        self._break_nodes: Dict[NodeID, Optional[Label]] = {}
        self._return_nodes: List[NodeID] = []

    def add_ast_node(self, ast_node: ASTNode, name: str = None, **kwargs: Any) -> NodeID:
        node = self.add_node(name, **kwargs)
        nx.set_node_attributes(self, {node: {'ast_node': ast_node}})
        return node

    def add_node(self, name: str = None, **kwargs: Any) -> NodeID:
        next_id = len(self.nodes()) + 1
        super().add_node(next_id, **kwargs)
        if name is not None:
            nx.set_node_attributes(self, {next_id: {'name': name}})
        return next_id

    def push_return_node(self, node: NodeID) -> None:
        self._return_nodes.append(node)

    def push_break_node(self, node: NodeID, label: Label = None) -> None:
         self._break_nodes[node] = label
        # self._break_nodes.append((node, label))

    def push_continue_node(self, node: NodeID, label: Label = None) -> None:
        self._continue_nodes[node] = label
        # self._continue_nodes.append((node, label))

    def pop_continue_node(self) -> Optional[Tuple[NodeID, Label]]:
        if len(self._continue_nodes) == 0:
            return None
        first_key, first_value = list(self._continue_nodes.items())[0]
        del self._continue_nodes[first_key]
        return first_key, first_value

    def pop_break_node(self) -> Optional[NodeID]:
        if len(self._break_nodes) == 0:
            return None
        first_key, first_value = list(self._break_nodes.items())[0]
        del self._break_nodes[first_key]
        return first_key, first_value

    def rewire_break_nodes(self, target_node: NodeID, label: Optional[Label] = None) -> None:
        break_nodes = list(self._break_nodes.keys())
        for node in break_nodes:
            if self._break_nodes[node] != label:
                continue
            self.remove_edges_from([e for e in self.out_edges(node)])
            self.add_edge(node, target_node, cflow=True)
            del self._break_nodes[node]

    def rewire_continue_nodes(self, target_node: NodeID, label: Optional[Label] = None) -> None:
        continue_nodes = list(self._continue_nodes.keys())
        for node in continue_nodes:
            if self._continue_nodes[node] != label:
                continue
            self.remove_edges_from([e for e in self.out_edges(node)])
            self.add_edge(node, target_node, cflow=True)
            del self._continue_nodes[node]

    def get_entry_node(self) -> NodeID:
        return 1

    def get_exit_node(self) -> NodeID:
        exit_candidates_l1: List[NodeID] = [n for n in self.nodes if self.out_degree(n) == 0 and self.in_degree(n) > 0]
        exit_candidates_l2 = []
        for candidate in exit_candidates_l1:
            if len([1 for (_, _, cflow) in self.in_edges(candidate, data='cflow') if cflow is True]) == 0:
                continue
            exit_candidates_l2.append(candidate)

        assert len(exit_candidates_l2) == 1
        return exit_candidates_l2[0]

    def wire_return_nodes(self) -> None:
        if len(self._return_nodes) == 0:
            return
        exit_node = self.get_exit_node()
        while len(self._return_nodes) > 0:
            return_node = self._return_nodes.pop()
            self.remove_edges_from([(a, b) for (a, b, cflow) in self.out_edges(return_node, data='cflow') if cflow is True])
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

    def to_ast(self) -> nx.DiGraph:
        copy = self.copy()
        copy.remove_edges_from([(a, b) for (a, b, syntax) in self.edges(data='syntax') if syntax is not True])
        copy.remove_nodes_from(list(nx.isolates(copy)))
        return copy

    def _node_to_label(self, node: NodeID) -> str:
        if self.nodes[node].get('name') is not None:
            return f'{self.nodes[node].get("name")}:{node}'
        if self.nodes[node].get('ast_node') is not None:
            return f'{self.nodes[node].get("ast_node").type}:{node}'
        return str(node)

    def _edge_data_to_label(self, dict: Mapping[str, Any]) -> str:
        labels = []
        if dict.get('syntax', False) is True:
            labels.append('syntax')
        if dict.get('cflow', False) is True:
            labels.append('control-flow')
        # if dict.get('cdep', False) is True:
        #     labels.append('control-dep')
        if dict.get('ddep', False) is True:
            labels.append('data-dep')
        return ','.join(labels)

    def _edge_to_table_row(self, node_from: NodeID, node_to: NodeID) -> Tuple[str, str, str, str]:
        edge_data = self.get_edge_data(node_from, node_to)
        return (self._node_to_label(node_from), '->', self._node_to_label(node_to), self._edge_data_to_label(edge_data))

    def __str__(self) -> str:
        table = [
            self._edge_to_table_row(a, b) for (a, b) in self.edges()]
        headers = ['From', '', 'To', 'Dependencies']
        return tabulate(
            table,
            headers=headers
        )


def mk_empty_adg() -> ADG:
    return ADG()
