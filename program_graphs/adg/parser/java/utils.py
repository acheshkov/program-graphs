from program_graphs.types import ASTNode
from typing import List, Optional
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.utils import get_project_root
import os

Label = str


def parse_ast_tree_sitter(source_code: str) -> ASTNode:
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            os.path.join(get_project_root(), "tree-sitter-java")
        ]
    )
    JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    source_code_bytes = bytes(source_code, 'utf-8')
    ast = parser.parse(source_code_bytes)
    return ast.root_node


def extract_code(start_byte: int, end_byte: int, code: bytes) -> str:
    return code[start_byte: end_byte].decode()


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


def get_identifier(node: ASTNode, source: Optional[bytes]) -> Optional[Label]:
    # mb_source: Optional[bytes] = kwargs.get('source')
    if source is None:
        return None
    matches: List[ASTNode] = [n for n in node.children if n.type == 'identifier']
    if len(matches) == 0:
        return None
    identifier_node = matches[0]
    return extract_code(identifier_node.start_byte, identifier_node.end_byte, source)
