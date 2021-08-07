from program_graphs.cfg import CFG
from tree_sitter import Language, Parser


def parse_java(source_code: str) -> CFG:
    Language.build_library(
        # Store the library in the `build` directory
        'build/my-languages.so',

        # Include one or more languages
        [
            './tree-sitter-java'
        ]
    )
    JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(JAVA_LANGUAGE)
    ast = parser.parse(bytes(source_code, 'utf-8'))
    return CFG(ast.root_node)
