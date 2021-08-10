from typing import Tuple, List
from program_graphs.cfg.types import JumpKind
from program_graphs.cfg.cfg import CFG, merge_cfg
from program_graphs.cfg.edge_contraction import edge_contraction


def mk_empty_cfg() -> CFG:
    cfg = CFG()
    cfg.add_node([])
    return cfg


def merge_cfgs(*cfgs: CFG) -> Tuple[CFG, ...]:
    cfg = CFG()
    maps = [merge_cfg(cfg, _cfg) for _cfg in cfgs]
    return (cfg,) + tuple(maps)


def combine_list(cfgs: List[CFG]) -> CFG:
    cfg = mk_empty_cfg()
    for _cfg in cfgs:
        cfg = combine(cfg, _cfg)
    return cfg


def combine(cfg_1: CFG, cfg_2: CFG) -> CFG:
    cfg, map_old_2_new_left = cfg_1.copy()
    map_old_2_new_right = merge_cfg(cfg, cfg_2)
    cfg = edge_contraction(cfg, [
        (map_old_2_new_left[cfg_1.exit_node()], map_old_2_new_right[cfg_2.entry_node()])
    ])
    rewire_return_nodes(cfg)
    cfg = manage_jumps(cfg)
    cfg = reduce_redundant_exit_nodes(cfg)
    return cfg


def reduce_redundant_exit_nodes(cfg: CFG) -> CFG:
    cfg_new, m = cfg.copy()
    for node in cfg.nodes():
        if len(cfg.get_block(node)) != 0:
            continue
        if len(list(cfg.successors(node))) != 1:
            continue
        successor = list(cfg.successors(node))[0]
        predecessors = cfg.predecessors(node)
        cfg_new.remove_node(m[node])
        for p in predecessors:
            cfg_new.add_edge(m[p], m[successor])
    return cfg_new


def rewire_return_nodes(cfg: CFG) -> None:
    exit_node = cfg.exit_node()
    for return_node in cfg.return_nodes:
        cfg.remove_edges_from([(return_node, s) for s in cfg.successors(return_node)])
        cfg.add_edge(return_node, exit_node)


def manage_jumps(cfg: CFG) -> CFG:
    for (node, label, kind) in cfg.possible_jumps:
        jump_nodes = []
        if kind == JumpKind.CONTINUE:
            jump_nodes = cfg.find_continue_by_label(label)

        if kind == JumpKind.BREAK:
            jump_nodes = cfg.find_break_by_label(label)

        if len(jump_nodes) == 0:
            continue
        for jn in jump_nodes:
            cfg.remove_edges_from([(jn, s) for s in cfg.successors(jn)])
            cfg.add_edge(jn, node)
            if kind == JumpKind.CONTINUE:
                cfg.remove_continue_node(jn)
            if kind == JumpKind.BREAK:
                cfg.remove_break_node(jn)

        cfg.remove_possible_jump(node)

    return cfg
