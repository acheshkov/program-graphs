
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
# from program_graphs.cfg.parser.java.parser import mk_cfg_return, mk_cfg
from program_graphs.adg.parser.java.parser import mk_adg_return, parse_from_ast
from program_graphs.adg.adg import mk_empty_adg
import networkx as nx  # type: ignore


class TestParseReturn(TestCase):

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

    def test_adg_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            return;
        """
        node = parser.parse(bts).root_node.children[0]
        self.assertEqual(node.type, 'return_statement')
        adg = mk_empty_adg()
        mk_adg_return(node, adg)
        self.assertEqual(len(adg.nodes()), 1)

    def test_cfg_program_only_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            return;
        """
        node = parser.parse(bts).root_node
        self.assertEqual(node.type, 'program')
        adg = parse_from_ast(node, bts)
        cfg = adg.to_cfg()
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([("entry", "return"), ("return", "exit")])
        ))

    def test_cfg_many_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            return;
            return;
        """
        node = parser.parse(bts).root_node
        self.assertEqual(node.type, 'program')
        adg = parse_from_ast(node, bts)
        cfg = adg.to_cfg()
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([('entry', 'return_1'), ("return_1", "exit"), ("return_2", "exit")])
        ))


if __name__ == '__main__':
    main()
