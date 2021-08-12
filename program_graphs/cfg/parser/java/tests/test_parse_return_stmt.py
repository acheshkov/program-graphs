
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_return, mk_cfg
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

    def test_cfg_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            return;
        """
        node = parser.parse(bts).root_node.children[0]
        self.assertEqual(node.type, 'return_statement')
        cfg = mk_cfg_return(node)
        self.assertEqual(len(cfg.return_nodes), 1)

    def test_cfg_many_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            return;
            return;
        """
        node = parser.parse(bts).root_node
        self.assertEqual(node.type, 'program')
        cfg = mk_cfg(node)
        self.assertEqual(len(cfg.return_nodes), 2)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([("return_1", "exit"), ("return_2", "exit")])
        ))


if __name__ == '__main__':
    main()
