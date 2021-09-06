
from typing import List, Optional
from program_graphs.types import NodeID, Edge
from program_graphs.cfg import CFG
import networkx as nx  # type: ignore


def find_edge_to_contract(cfg: CFG) -> Optional[Edge]:
    for edge in cfg.edges():
        if is_possible_to_contract(cfg, edge):
            return edge  # type: ignore
    return None


def edge_contraction_all(cfg: CFG) -> CFG:
    mb_edge = find_edge_to_contract(cfg)
    if mb_edge is None:
        return cfg
    cfg = edge_contraction(cfg, mb_edge)
    return edge_contraction_all(cfg)


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

        if node in cfg.return_nodes:
            cfg.add_return_node(target_node)


def is_possible_to_contract(cfg: CFG, edge: Edge) -> bool:
    entry = cfg.entry_node()
    exit = cfg.exit_node()
    (node_from, node_to) = edge

    out_deg_exit = len(list(cfg.successors(node_from)))
    in_deg_entry = len(list(cfg.predecessors(node_to)))
    if out_deg_exit != 1 or in_deg_entry != 1:
        return False

    for node, _ in cfg.continue_nodes + cfg.break_nodes:
        if node == node_from:
            return False

    for node in cfg.return_nodes:
        if node == node_from:
            return False

    all_paths = nx.all_simple_paths(cfg, entry, exit)
    for path in all_paths:
        if node_from in path and node_to not in path:
            return False
        if node_to in path and node_from not in path:
            return False
    return True


def edge_contraction(cfg: CFG, edge: Edge) -> CFG:
    exit_node, entry_node = edge
    exit_block, entry_block = cfg.get_block(exit_node), cfg.get_block(entry_node)
    block = exit_block + entry_block
    merged_node_id = cfg.add_node(block, cfg.get_node_name(entry_node) or cfg.get_node_name(exit_node))
    rewire_predecessors(cfg, exit_node, merged_node_id)
    rewire_successors(cfg, entry_node, merged_node_id)
    move_special_nodes(cfg, [exit_node, entry_node], merged_node_id)
    cfg.remove_nodes_from([exit_node, entry_node])
    cfg, _ = cfg.copy()
    return cfg
