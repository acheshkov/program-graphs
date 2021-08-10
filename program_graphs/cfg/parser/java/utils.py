from typing import List, Optional, Any
from program_graphs.cfg.types import Node, Label


def extract_code(start_byte: int, end_byte: int, code: bytes) -> str:
    return code[start_byte: end_byte].decode()


def get_nodes_after_colon(node: Node) -> List[Node]:
    colon_pos = [pos for pos, node in enumerate(node.children) if node.type == ':'][0]
    return node.children[colon_pos + 1:]  # type: ignore


def get_identifier(node: Node, **kwargs: Any) -> Optional[Label]:
    mb_source: Optional[bytes] = kwargs.get('source')
    if mb_source is None:
        return None
    matches: List[Node] = [n for n in node.children if n.type == 'identifier']
    if len(matches) == 0:
        return None
    identifier_node = matches[0]
    return extract_code(identifier_node.start_byte, identifier_node.end_byte, mb_source)
