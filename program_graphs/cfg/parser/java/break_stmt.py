from typing import Dict, Any
from program_graphs.cfg import CFG
from program_graphs.cfg.parser.java.utils import get_identifier
from program_graphs.cfg.types import Node


def mk_cfg_break(node: Node, **kwargs: Dict[str, Any]) -> CFG:
    cfg = CFG()
    stmt = cfg.add_node([node])
    exit = cfg.add_node([])
    cfg.add_edge(stmt, exit)
    maybe_label = get_identifier(node, **kwargs)
    cfg.add_break_node(stmt, maybe_label)
    return cfg
