from program_graphs.types import ASTNode
from typing import List


def get_switch_label(node: ASTNode) -> ASTNode:
    label_nodes = [n for n in node.children if n.type == 'switch_label']
    assert len(label_nodes) == 1
    return label_nodes[0]


def get_switch_block_label(node: ASTNode) -> str:
    label = get_switch_label(node)
    return label.children[0].type  # type: ignore


def get_nodes_after_colon(node: ASTNode) -> List[ASTNode]:
    colon_pos = [pos for pos, node in enumerate(node.children) if node.type == ':'][0]
    return node.children[colon_pos + 1:]  # type: ignore
