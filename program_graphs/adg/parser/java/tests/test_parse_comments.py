
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import parse_from_ast


class TestParseComments(TestCase):

    def get_parser(self) -> Parser:
        Language.build_library(
            'build/my-languages.so',
            [
                './tree-sitter-java'
            ]
        )
        JAVA_LANGUAGE = Language('build/my-languages.so', 'java')
        parser = Parser()
        parser.set_language(JAVA_LANGUAGE)
        return parser

    def test_adg_comemnts(self) -> None:
        parser = self.get_parser()
        bts = b"""
            // comment
            stmt();
            /* block
               comments
            */
            stmt();
        """

        ast = parser.parse(bts).root_node
        adg = parse_from_ast(ast, bts)
        nodes = [(node, ast_node) for (node, ast_node) in adg.nodes(data='ast_node') if ast_node is not None]
        node_comments = [(node, ast_node) for node, ast_node in nodes if ast_node.type in ['line_comment', 'block_comment']]
        self.assertEqual(len(node_comments), 2, 'Comments are present in the graph')
        for node, _ in node_comments:
            self.assertEqual(
                len([1 for (_, syntax) in adg.out_edges(node, data='syntax') if syntax is True]),
                0,
                'Comments do not have syntax out relations'
            )


if __name__ == '__main__':
    main()
