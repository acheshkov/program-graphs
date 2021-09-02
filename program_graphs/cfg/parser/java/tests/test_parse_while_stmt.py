
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_while
import networkx as nx  # type: ignore


class TestParseWhile(TestCase):

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

    def test_cfg_while(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                i++;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        cfg = mk_cfg_while(while_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition'),
                ('condition', 'body'),
                ('body', 'condition'),
                ('condition', 'exit')
            ])
        ))

    def test_cfg_while_with_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                continue;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        cfg = mk_cfg_while(while_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition'),
                ('condition', 'body'),
                ('body', 'condition'),
                ('condition', 'exit')
            ])
        ))

    def test_cfg_while_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                break;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        cfg = mk_cfg_while(while_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('condition', 'body'),
                ('body', 'exit'),
                ('condition', 'exit')
            ])
        ))

    def test_cfg_while_nested_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                while (j < 5) {
                    break;
                }
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        cfg = mk_cfg_while(while_node)
        print(cfg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition_1'),
                ('condition_1', 'exit'),
                ('condition_1', 'condition_2'),
                ('condition_2', 'break'),
                ('condition_2', 'condition_1'),
                ('break', 'condition_1')
            ])
        ))

    def test_cfg_while_nested_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                while (j < 5) {
                    continue;
                }
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        cfg = mk_cfg_while(while_node)
        print(cfg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition_1'),
                ('condition_1', 'exit'),
                ('condition_1', 'condition_2'),
                ('condition_2', 'continue'),
                ('continue', 'condition_2'),
                ('condition_2', 'condition_1')
            ])
        ))


if __name__ == '__main__':
    main()
