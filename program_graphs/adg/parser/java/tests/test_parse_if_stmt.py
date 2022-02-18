
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
        # print(adg.to_cdg())

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('if', 'condition'), ('condition', 'body'), ('body', 'stmt'), ('condition', 'exit'), ('stmt', 'exit')
            ])
        ))
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cdg(),
            nx.DiGraph([
                ('if', 'condition'), ('condition', 'body'), ('body', 'stmt'), ('if', 'exit')
            ])
        ))

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
                ('condition', 'body_true'),
                ("condition", 'body_false'),
                ('body_true', 'stmt_1'),
                ('body_false', 'stmt_2'),
                ('stmt_1', 'exit'), 
                ('stmt_2', 'exit')
            ])
        ))

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cdg(),
            nx.DiGraph([
                ('if', 'condition'),
                ('condition', 'body_true'),
                ('condition', 'body_false'),
                ('body_true', 'stmt_1'),
                ('body_false', 'stmt_2'),
                ('if', 'exit')
            ])
        ))


if __name__ == '__main__':
    main()
