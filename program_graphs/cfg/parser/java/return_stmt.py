from program_graphs.cfg import CFG
from program_graphs.cfg.types import Node


def mk_cfg_return(node: Node) -> CFG:
    cfg = CFG()
    stmt = cfg.add_node([node], 'return')
    exit = cfg.add_node([], 'exit')
    cfg.add_edge(stmt, exit)
    cfg.add_return_node(stmt)
    return cfg
