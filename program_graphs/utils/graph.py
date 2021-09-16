from typing import List
from tree_sitter import Node as Statement  # type: ignore
from itertools import chain


def filter_nodes(node: Statement, node_types: List[str]) -> List[Statement]:
    if node is None:
        return []
    nodes = list(chain.from_iterable(
        [filter_nodes(ch, node_types) for ch in node.children]
    ))
    if node.type in node_types:
        return [node] + nodes
    return nodes
