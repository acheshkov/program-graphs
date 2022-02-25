
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import mk_adg_if
from program_graphs.adg.adg import mk_empty_adg
import networkx as nx  # type: ignore


class TestParseIF(TestCase):

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

    def test_adg_if(self) -> None:
        parser = self.get_parser()
        bts = b"""
            if (a > 1) {
                a = 9;
            }
        """
        if_node = parser.parse(bts).root_node.children[0]
        assert if_node.type == 'if_statement'
        adg = mk_empty_adg()
        mk_adg_if(if_node, adg)

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('if', 'condition'),
                ('condition', 'body'),
                ('body', 'stmt'),
                ('stmt', 'body_exit'),
                ('condition', 'exit'),
                ('body_exit', 'exit')
            ])
        ))
        # self.assertTrue(nx.algorithms.is_isomorphic(
        #     adg.to_cdg(),
        #     nx.DiGraph([
        #         ('if', 'condition'), ('condition', 'body'), ('body', 'stmt'), ('body', 'body_exit'), ('if', 'exit')
        #     ])
        # ))

    def test_adg_if_else(self) -> None:
        parser = self.get_parser()
        bts = b"""
            if (a > 1) {
                a = 9;
            } else {
                a = 2;
            }
        """
        if_node = parser.parse(bts).root_node.children[0]
        assert if_node.type == 'if_statement'
        adg = mk_empty_adg()
        mk_adg_if(if_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('if', 'condition'),
                ('condition', 'body_true_block'),
                ("condition", 'body_false_block'),
                ('body_true_block', 'stmt_1'),
                ('body_false_block', 'stmt_2'),
                ('stmt_1', 'body_true_block_exit'),
                ('stmt_2', 'body_false_block_exit'),
                ('body_true_block_exit', 'exit'),
                ('body_false_block_exit', 'exit')
            ])
        ))

        # self.assertTrue(nx.algorithms.is_isomorphic(
        #     adg.to_cdg(),
        #     nx.DiGraph([
        #         ('if', 'condition'),
        #         ('condition', 'body_true'),
        #         ('condition', 'body_false'),
        #         ('body_true', 'stmt_1'),
        #         ('body_true', 'body_true_exit'),
        #         ('body_false', 'stmt_2'),
        #         ('body_false', 'body_false_exit'),
        #         ('if', 'exit')
        #     ])
        # ))


if __name__ == '__main__':
    main()
