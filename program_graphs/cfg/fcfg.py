# from __future__ import annotations
from typing import Mapping, List, Tuple, Optional
import networkx as nx  # type: ignore
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
from program_graphs.cfg.cfg import CFG
from program_graphs.types import NodeID
from tree_sitter import Node as Statement  # type: ignore

BasicBlockID = NodeID
FCFGNodeID = NodeID


class FCFG(nx.DiGraph):
    '''FullCGF is a CFG but verticies not a BasicBlocks but AST Nodes'''

    @property
    def exit_node(self) -> NodeID:
        return self._exit_node

    @exit_node.setter
    def exit_node(self, value: NodeID) -> None:
        self._exit_node = value

    @property
    def entry_node(self) -> NodeID:
        return self._entry_node

    @entry_node.setter
    def entry_node(self, value: NodeID) -> None:
        self._entry_node = value


def enumerate_cfg_nodes(cfg: CFG) -> Mapping[NodeID, List[Tuple[FCFGNodeID, Statement]]]:
    node_id_incr = 0
    blocks = [(node_id, cfg.get_block(node_id)) for node_id in list(cfg.nodes())]
    mapping = {}
    for node, bbs in blocks:
        if len(bbs) == 0:
            mapping[node] = [(node_id_incr, None)]
            node_id_incr += 1
        else:
            bbs = [(node_id_incr + i, bb) for i, bb in enumerate(bbs)]
            node_id_incr += len(bbs)
            mapping[node] = bbs
    return mapping


def add_basic_block_to_fcfg(
    fcfg: FCFG,
    bb: BasicBlockID,
    parent: Optional[FCFGNodeID],
    blocks_to_stmts: Mapping[NodeID, List[Tuple[int, Statement]]]
) -> Optional[FCFGNodeID]:
    for i, stmt in blocks_to_stmts[bb]:
        fcfg.add_node(i, statement=stmt)
        if parent is not None:
            fcfg.add_edge(parent, i, flow=True)
        parent = i
    return parent


def _mk_fcfg_from_cfg(
    bb: BasicBlockID,
    parent: Optional[FCFGNodeID],
    cfg: CFG,
    fcfg: FCFG,
    blocks_to_stmts: Mapping[NodeID, List[Tuple[int, Statement]]],
    added_basic_blocks: List[BasicBlockID]
) -> None:
    if bb in added_basic_blocks:
        fcfg.add_edge(parent, blocks_to_stmts[bb][0][0], flow=True)
        return
    last_fcfg_node = add_basic_block_to_fcfg(fcfg, bb, parent, blocks_to_stmts)
    added_basic_blocks.append(bb)
    for _bb in cfg.successors(bb):
        _mk_fcfg_from_cfg(_bb, last_fcfg_node, cfg, fcfg, blocks_to_stmts, added_basic_blocks)


def mk_fcfg_from_cfg(cfg: CFG) -> FCFG:
    fcfg = FCFG()
    if len(cfg.nodes()) == 0:
        return fcfg
    blocks_to_stmts = enumerate_cfg_nodes(cfg)
    added_basic_blocks: List[BasicBlockID] = []
    _mk_fcfg_from_cfg(cfg.entry_node(), None, cfg, fcfg, blocks_to_stmts, added_basic_blocks)
    fcfg.entry_node = blocks_to_stmts[cfg.entry_node()][0][0]
    fcfg.exit_node = blocks_to_stmts[cfg.exit_node()][-1][0]
    return fcfg
