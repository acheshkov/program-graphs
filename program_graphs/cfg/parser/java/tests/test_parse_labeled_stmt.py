
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_labeled_statement, mk_cfg
import networkx as nx  # type: ignore


class TestParseLabeled(TestCase):

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

    def test_cfg_labeled_statement_break_to_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            goto: {
                break goto;
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'labeled_statement'
        cfg = mk_cfg_labeled_statement(node, source=bts)
        self.assertEqual(len(cfg.break_nodes), 0)
        self.assertEqual(len(cfg.possible_jumps), 0)

    def test_cfg_labeled_statement_with_continue_to_other_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            goto: {
                continue goto;
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'labeled_statement'
        cfg = mk_cfg_labeled_statement(node, source=bts)
        assert len(cfg.continue_nodes) == 1
        assert len(cfg.possible_jumps) == 1
        assert nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ("continue", "exit")
            ])
        )

    def test_cfg_nested_for_with_break_to_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            goto:{
                for (int i = 0; i < 10; i++) {
                    for (int i = 0; i < 10; i++) {
                        break goto;
                    }
            }
        """
        node = parser.parse(bts).root_node
        cfg = mk_cfg(node, source=bts)
        assert nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('init_1', 'condition_1'),
                ('condition_1', 'exit'),
                ('update_1', 'condition_1'),
                ('condition_1', 'init_2'),
                ('init_2', 'condition_2'),
                ('condition_2', 'update_1'),
                ('condition_2', 'break'),
                ('update_2', 'condition_2'),
                ('break', 'exit'),
            ])
        )

    def test_cfg_nested_for_with_continue_to_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            goto:{
                for (int i = 0; i < 10; i++) {
                    for (int i = 0; i < 10; i++) {
                        continue goto;
                    }
                }
            }
        """
        node = parser.parse(bts).root_node
        cfg = mk_cfg(node, source=bts)
        assert nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('init_1', 'condition_1'),
                ('condition_1', 'exit'),
                ('update_1', 'condition_1'),
                ('condition_1', 'init_2'),
                ('init_2', 'condition_2'),
                ('condition_2', 'update_1'),
                ('condition_2', 'continue'),
                ('update_2', 'condition_2'),
                ('continue', 'update_1'),
            ])
        )


if __name__ == '__main__':
    main()
