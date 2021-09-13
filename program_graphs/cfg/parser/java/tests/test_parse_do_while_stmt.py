
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_do_while
import networkx as nx  # type: ignore


class TestParseDoWhile(TestCase):

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

    def test_cfg_do_while(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
                i++;
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'body_and_condition'),
                ('body_and_condition', 'body_and_condition'),
                ('body_and_condition', 'exit')
            ])
        ))

    def test_cfg_do_while_nested(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
                do {
                    j++;
                } while (j < 5);
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'body_condition_2'),
                ('body_condition_2', 'body_condition_2'),
                ('body_condition_2', 'condition_1'),
                ('condition_1', 'body_condition_2'),
                ('condition_1', 'exit')
            ])
        ))

    def test_cfg_do_while_with_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
                continue;
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'body_and_condition'),
                ('body_and_condition', 'body_and_condition'),
                ('body_and_condition', 'exit')
            ])
        ))

    def test_cfg_do_while_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
                break;
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'break'),
                ('break', 'exit'),
                ('condition', 'break'),
                ('condition', 'exit')
            ])
        ))

    def test_cfg_do_while_nested_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
               do {
                    break;
                } while (j < 5);
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'merged_body_condition_break'),
                ('merged_body_condition_break', 'condition_1'),
                ('condition_2', 'merged_body_condition_break'),
                ('condition_2', 'condition_1'),
                ('condition_1', 'merged_body_condition_break'),
                ('condition_1', 'exit')
            ])
        ))

    def test_cfg_do_while_nested_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            do {
               do {
                    continue;
                } while (j < 5);
            } while (i < 5);
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'do_statement'
        cfg = mk_cfg_do_while(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'merged_body_condition_continue'),
                ('merged_body_condition_continue', 'merged_body_condition_continue'),
                ('merged_body_condition_continue', 'condition_1'),
                ('condition_1', 'merged_body_condition_continue'),
                ('condition_1', 'exit')
            ])
        ))


if __name__ == '__main__':
    main()
