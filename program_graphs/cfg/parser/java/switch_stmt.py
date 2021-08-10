from program_graphs.cfg.types import Node


def get_switch_label(node: Node) -> Node:
    label_nodes = [n for n in node.children if n.type == 'switch_label']
    assert len(label_nodes) == 1
    return label_nodes[0]


def get_switch_block_label(node: Node) -> str:
    label = get_switch_label(node)
    return label.children[0].type  # type: ignore
