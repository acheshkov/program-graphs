# from __future__ import annotations
import networkx as nx
# from typing import TYPE_CHECKING
# if TYPE_CHECKING:
from program_graphs.cfg.cfg import CFG


class FCFG(nx.DiGraph):
    '''FullCGF is a CFG but verticies not a BasicBlocks but Nodes'''
    pass


def mk_fcfg_from_cfg(cfg: CFG) -> FCFG:
    fcfg = FCFG()
    return fcfg
