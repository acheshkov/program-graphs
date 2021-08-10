from typing import Any
from program_graphs.cfg import CFG
from program_graphs.cfg.parser.java.utils import get_identifier
from program_graphs.cfg.types import Node


def mk_cfg_continue(node: Node, **kwargs: Any) -> CFG:
    cfg = CFG()
    stmt = cfg.add_node([node], 'continue')
    exit = cfg.add_node([], 'exit')
    cfg.add_edge(stmt, exit)
    maybe_label = get_identifier(node, source=kwargs.get('source'))
    cfg.add_continue_node(stmt, maybe_label)
    return cfg
