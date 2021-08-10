
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_if, mk_cfg_if_else
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

    def test_cfg_if(self) -> None:
        parser = self.get_parser()
        bts = b"""
            if (a > 1) {
                a = 9;
            }
        """
        if_node = parser.parse(bts).root_node.children[0]
        assert if_node.type == 'if_statement'
        cfg = mk_cfg_if(if_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('condition', 'true'), ('condition', 'exit'), ('true', 'exit')
            ])
        ))

    def test_cfg_if_else(self) -> None:
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
        cfg = mk_cfg_if_else(if_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('condition', 'true'), ("condition", 'false'), ('true', 'exit'), ('false', 'exit')
            ])
        ))


if __name__ == '__main__':
    main()
