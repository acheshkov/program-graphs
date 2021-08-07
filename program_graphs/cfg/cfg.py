from typing import List, Tuple, Mapping, Set, Optional
from tree_sitter import Node  # type: ignore
import networkx as nx  # type: ignore

from program_graphs.cfg.types import JumpKind
from program_graphs.cfg.types import NodeID

# NodeID = int
# Edge = Tuple[NodeID, NodeID]
BasicBlock = List[Node]
ForNode = Node
IfElseNode = Node
BlockNode = Node
SwitchNode = Node
Label = str


class CFG(nx.DiGraph):

    def __init__(self, block: BasicBlock = None):
        super().__init__()
        self.node_id_2_block: List[BasicBlock] = list()
        self._continue_nodes: Set[Tuple[NodeID, Optional[Label]]] = set()
        self._break_nodes: Set[Tuple[NodeID, Optional[Label]]] = set()
        self._possible_to_jump: Set[Tuple[NodeID, Optional[Label], JumpKind]] = set()
        self._return_nodes: Set[NodeID] = set()
        # self._labeled_nodes: Set[Tuple[NodeID, Label]] = set()
        if block is not None:
            self.add_node(block)

    def copy(self):
        return copy_cfg(self)

    def add_node(self, block: BasicBlock, label: str = None) -> NodeID:
        self.node_id_2_block.append(block)
        super().add_node(len(self.node_id_2_block) - 1, label=label)
        return len(self.node_id_2_block) - 1

    def remove_node(self, node: NodeID) -> None:
        self.remove_nodes_from([node])

    def remove_nodes_from(self, nodes: List[NodeID]) -> None:
        super().remove_nodes_from(nodes)
        for n in nodes:
            self.remove_continue_node(n)
            self.remove_break_node(n)
            self.remove_return_node(n)
            self.remove_possible_jump(n)

    def entry_node(self) -> NodeID:
        return self.entry_nodes()[0][0]

    def exit_node(self) -> NodeID:
        return self.exit_nodes()[0][0]

    def entry_nodes(self) -> List[Tuple[NodeID, Label]]:
        return list(
            [(node, nx.get_node_attributes(self, 'label')[node]) for node, in_degre in self.in_degree() if in_degre == 0]
        )

    def exit_nodes(self) -> List[Tuple[NodeID, Label]]:
        return list(
            [(node, nx.get_node_attributes(self, 'label')[node]) for node, out_degre in self.out_degree() if out_degre == 0]
        )

    @property
    def continue_nodes(self) -> List[Tuple[NodeID, Optional[Label]]]:
        return list(self._continue_nodes)

    @property
    def break_nodes(self) -> List[Tuple[NodeID, Optional[Label]]]:
        return list(self._break_nodes)

    @property
    def return_nodes(self) -> List[NodeID]:
        return list(self._return_nodes)

    @property
    def labeled_nodes(self) -> List[Tuple[NodeID, Label]]:
        return list(self._labeled_nodes)

    @property
    def possible_jumps(self) -> List[Tuple[NodeID, Optional[Label], JumpKind]]:
        return list(self._possible_to_jump)

    def add_continue_node(self, node: NodeID, label: Optional[Label] = None) -> None:
        self._continue_nodes |= {(node, label)}

    def remove_continue_node(self, node: NodeID) -> None:
        self._continue_nodes = set([(n, l) for n, l in self._continue_nodes if n != node])

    def find_continue_by_label(self, label: Optional[Label]) -> List[NodeID]:
        if label is None:
            return [n for n, _label in self._continue_nodes if _label is None]
        return [n for n, _label in self._continue_nodes if _label == label]

    def add_break_node(self, node: NodeID, label: Optional[Label] = None) -> None:
        self._break_nodes |= {(node, label)}

    def remove_break_node(self, node: NodeID) -> None:
        self._break_nodes = set([(n, l) for n, l in self._break_nodes if n != node])

    def find_break_by_label(self, label: Optional[Label]) -> List[NodeID]:
        if label is None:
            return [n for n, _label in self._break_nodes if _label is None]
        return [n for n, _label in self._break_nodes if _label == label]

    def add_return_node(self, node: NodeID) -> None:
        self._return_nodes |= {node}

    def remove_return_node(self, node: NodeID) -> None:
        self._return_nodes -= {node}

    def add_possible_jump(self, node: NodeID, label: Optional[Label], kind: JumpKind) -> None:
        self._possible_to_jump |= {(node, label, kind)}

    def remove_possible_jump(self, node: NodeID) -> None:
        self._possible_to_jump = set([(n, l, k) for n, l, k in self._possible_to_jump if n != node])

    def get_block(self, nid: NodeID) -> BasicBlock:
        return self.node_id_2_block[nid]


def copy_cfg(cfg: CFG) -> Tuple[CFG, Mapping[NodeID, NodeID]]:
    cfg_copy = CFG()
    return cfg_copy, merge_cfg(cfg_copy, cfg)


def merge_cfg(cfg: CFG, _cfg: CFG) -> Mapping[NodeID, NodeID]:
    map_old_2_new = dict()
    for node_id, label in _cfg.nodes(data='label'):
        node_id_new = cfg.add_node(_cfg.node_id_2_block[node_id], label)
        map_old_2_new[node_id] = node_id_new

    for (node_from, node_to) in _cfg.edges():
        cfg.add_edge(map_old_2_new[node_from], map_old_2_new[node_to])

    for node, label in _cfg.continue_nodes:
        cfg.add_continue_node(map_old_2_new[node], label)

    for node, label in _cfg.break_nodes:
        cfg.add_break_node(map_old_2_new[node], label)

    for node, label, kind in _cfg.possible_jumps:
        cfg.add_possible_jump(map_old_2_new[node], label, kind)

    for node in _cfg.return_nodes:
        cfg.add_return_node(map_old_2_new[node])

    return map_old_2_new
