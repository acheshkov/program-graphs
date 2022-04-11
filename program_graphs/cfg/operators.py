from typing import Optional, List
from program_graphs.types import Edge, NodeID
from program_graphs.cfg.types import JumpKind
from program_graphs.cfg.cfg import CFG, merge_cfg
from program_graphs.cfg.edge_contraction import edge_contraction_all


def mk_empty_cfg() -> CFG:
    cfg = CFG()
    cfg.add_node([])
    return cfg


def combine_list(cfgs: List[CFG]) -> CFG:
    cfg = mk_empty_cfg()
    for _cfg in cfgs:
        cfg = combine(cfg, _cfg)
    return cfg


def combine(cfg_1: CFG, cfg_2: CFG, on_left: Optional[NodeID] = None, on_right: Optional[NodeID] = None) -> CFG:
    cfg, map_old_2_new_left = cfg_1.copy()
    map_old_2_new_right = merge_cfg(cfg, cfg_2)
    if on_left is None:
        on_left = cfg_1.exit_node()
    if on_right is None:
        on_right = cfg_2.entry_node()
    cfg.add_edge(map_old_2_new_left[on_left], map_old_2_new_right[on_right])
    return cfg


def find_redundant_exit_nodes(cfg: CFG) -> List[NodeID]:
    nodes_to_remove = []
    for node in cfg.nodes():
        if not can_empty_node_be_removed(cfg, node):
            continue
        nodes_to_remove.append(node)
    return nodes_to_remove


def can_entry_node_be_removed(cfg: CFG, node: NodeID) -> bool:
    assert cfg.entry_node() == node
    for s in cfg.successors(node):
        in_deg = len(list(cfg.predecessors(s))) - 1
        if in_deg > 0:
            return False
    return True


def can_empty_node_be_removed(cfg: CFG, node: NodeID) -> bool:
    if len(cfg.get_block(node)) != 0:
        return False
    out_deg = len(list(cfg.successors(node)))
    in_deg = len(list(cfg.predecessors(node)))
    if out_deg == 0:
        return False
    if out_deg * in_deg > max(out_deg, in_deg):
        return False

    if cfg.entry_node() == node and not can_entry_node_be_removed(cfg, node):
        return False

    return True


def remove_empty_node(cfg: CFG, node: NodeID) -> None:
    new_edges: List[Edge] = []
    for p in cfg.predecessors(node):
        for s in cfg.successors(node):
            new_edges.append((p, s))
    cfg.add_edges_from(new_edges)

    node_name = cfg.get_node_name(node)
    for _node in list(cfg.predecessors(node)) + list(cfg.successors(node)):
        if cfg.get_node_name(_node) is not None:
            continue
        cfg.set_node_name(_node, node_name)
    cfg.remove_node(node)


def remove_empty_nodes(cfg: CFG, nodes: List[NodeID]) -> CFG:
    for node in nodes:
        if not can_empty_node_be_removed(cfg, node):
            continue
        remove_empty_node(cfg, node)
    cfg, _ = cfg.copy()
    return cfg


def eliminate_redundant_nodes(cfg: CFG) -> CFG:
    cfg, _ = cfg.copy()
    exit_nodes = find_redundant_exit_nodes(cfg)
    cfg = remove_empty_nodes(cfg, exit_nodes)
    cfg = edge_contraction_all(cfg)
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


def manage_jumps(cfg: CFG) -> None:
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

    rewire_return_nodes(cfg)
