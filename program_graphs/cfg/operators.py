from typing import Tuple
# from program_graphs.cfg.types import NodeID
from program_graphs.cfg.cfg import CFG, merge_cfg


def mk_empty_cfg() -> CFG:
    cfg = CFG()
    cfg.add_node([])
    return cfg


def merge_cfgs(*cfgs: CFG) -> Tuple[CFG, ...]:
    cfg = CFG()
    maps = [merge_cfg(cfg, _cfg) for _cfg in cfgs]
    return (cfg,) + tuple(maps)
