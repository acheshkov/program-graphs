
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_for
import networkx as nx  # type: ignore


class TestParseFOR(TestCase):

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

    def test_cfg_for(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                a = 9;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('init', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'condition')
            ])
        ))

    def test_cfg_for_without_init(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (; i < 10; i++) {
                a = 9;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'condition')
            ])
        ))

    def test_cfg_for_without_update(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10;) {
                a = 9;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'condition')
            ])
        ))

    def test_cfg_for_without_init_and_update(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (; i < 10;) {
                a = 9;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('start', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'condition')
            ])
        ))

    def test_cfg_for_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                break;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('init', 'condition'),
                ('condition', 'break'),
                ('break', 'exit'),
                ('condition', 'exit'),
                ('update', 'condition')
            ])
        ))

    def test_cfg_for_with_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                continue;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ("init", "condition"),
                ("condition", "continue"),
                ("continue", "condition"),
                # ("update", "condition"),
                ("condition", "exit")
            ])
        ))

    def test_cfg_nested_for_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                for (int i = 0; i < 10; i++) {
                    break;
                }
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        assert nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('init_1', 'condition_1'),
                ('condition_1', 'exit'),
                ('update_1', 'condition_1'),
                ('condition_1', 'init_2'),
                ('init_2', 'condition_2'),
                ('condition_2', 'break'),
                ('condition_2', 'update_1'),
                ('break', 'update_1'),
                ('update_2', 'condition_2'),
            ])
        )

    def test_cfg_for_and_continue_inside_if(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                if (i > 2) {
                    continue;
                }
                b = 2;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('init', 'condition'),
                ('condition', 'if'),
                ('if', 'continue'),
                ('continue', 'update'),
                ('if', 'statement'),
                ('statement', 'update'),
                ('update', 'condition'),
                ('condition', 'exit')
            ])
        ))

    def test_cfg_for_without_init_and_continue_inside_if(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10;) {
                if (i > 2) {
                    continue;
                }
                b = 2;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        cfg = mk_cfg_for(for_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg, nx.DiGraph([
                ('init', 'condition'),
                ('condition', 'if'),
                ('if', 'continue'),
                ('continue', 'condition'),
                ('if', 'statement'),
                ('statement', 'condition'),
                ('condition', 'exit')
            ])
        ))


if __name__ == '__main__':
    main()
