
from typing import List
from program_graphs.cfg.types import NodeID, Edge
from program_graphs.cfg import CFG


def has_common_predecessors(g: CFG, node_1: NodeID, node_2: NodeID) -> bool:
    return len(set(g.predecessors(node_1)) & set(g.predecessors(node_2))) > 0


def has_common_successors(g: CFG, node_1: NodeID, node_2: NodeID) -> bool:
    return len(set(g.successors(node_1)) & set(g.successors(node_2))) > 0


def is_edge_contraction_possible(cfg: CFG, node_1: NodeID, node_2: NodeID) -> bool:
    if has_common_predecessors(cfg, node_1, node_2):
        return False
    if has_common_successors(cfg, node_1, node_2):
        return False
    # if cfg.get_label_by_node(node_1) is not None and cfg.get_label_by_node(node_2) is not None:
    #     print("both nodes has labels!")
    #     return False
    return True


def rewire_predecessors(cfg: CFG, from_node: NodeID, to_node: NodeID) -> None:
    for node in cfg.predecessors(from_node):
        cfg.add_edge(node, to_node)


def rewire_successors(cfg: CFG, from_node: NodeID, to_node: NodeID) -> None:
    for node in cfg.successors(from_node):
        cfg.add_edge(to_node, node)


def move_special_nodes(cfg: CFG, nodes_from: List[NodeID], target_node: NodeID) -> None:
    for node in nodes_from:
        for continue_node, label in cfg.continue_nodes:
            if continue_node != node:
                continue
            cfg.add_continue_node(target_node, label)

        for break_node, label in cfg.break_nodes:
            if break_node != node:
                continue
            cfg.add_break_node(target_node, label)

        for jump_node, label, kind in cfg.possible_jumps:
            if jump_node != node:
                continue
            cfg.add_possible_jump(target_node, label, kind)


def edge_contraction(cfg: CFG, edges: List[Edge]) -> CFG:
    cfg, map_old_2_new = cfg.copy()
    for edge in edges:
        exit_node, entry_node = map_old_2_new[edge[0]], map_old_2_new[edge[1]]
        if not is_edge_contraction_possible(cfg, exit_node, entry_node):
            print('edge contraction is not possible. Nodes:', exit_node, entry_node)
            continue
        exit_block, entry_block = cfg.get_block(exit_node), cfg.get_block(entry_node)
        block = exit_block + entry_block
        merged_node_id = cfg.add_node(block, cfg.get_node_name(entry_node))
        rewire_predecessors(cfg, exit_node, merged_node_id)
        rewire_successors(cfg, entry_node, merged_node_id)
        move_special_nodes(cfg, [exit_node, entry_node], merged_node_id)
        cfg.remove_nodes_from([exit_node, entry_node])
    return cfg
