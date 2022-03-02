
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import mk_adg_labeled_statement
from program_graphs.adg.adg import mk_empty_adg
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

    def test_adg_labeled_loop_statement_break_to_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            label:
            for (;;){
                for (;;){
                    break label;
                }
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'labeled_statement'
        adg = mk_empty_adg()
        mk_adg_labeled_statement(node, adg, source=bts)
        cfg = adg.to_cfg()
        self.assertEqual(cfg.in_degree(cfg.get_exit_node()), 2)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('for_1', 'for_init_1'),
                ('for_init_1', 'for_condition_1'),
                ('for_condition_1', 'for_exit_1'),
                ('for_update_1', 'for_condition_1'),
                ('for_condition_1', 'for_body_entry_1'),
                ('for_body_entry_1', 'for_2'),
                ('for_2', 'for_init_2'),
                ('for_init_2', 'for_condition_2'),
                ('for_condition_2', 'for_exit_2'),
                ('for_update_2', 'for_condition_2'),
                ('for_condition_2', 'for_body_entry_2'),
                ('for_body_entry_2', 'break'),
                ('break', 'for_exit_1'),
                ('for_body_exit_2', 'for_update_2'),
                ('for_exit_2', 'for_body_exit_1'),
                ('for_body_exit_1', 'for_update_1')
            ])
        ))

    def test_adg_labeled_loop_statement_continue_to_label(self) -> None:
        parser = self.get_parser()
        bts = b"""
            label:
            for (;;){
                for (;;){
                    continue label;
                }
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'labeled_statement'
        adg = mk_empty_adg()
        mk_adg_labeled_statement(node, adg, source=bts)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('for_1', 'for_init_1'),
                ('for_init_1', 'for_condition_1'),
                ('for_condition_1', 'for_exit_1'),
                ('for_update_1', 'for_condition_1'),
                ('for_condition_1', 'for_body_entry_1'),
                ('for_body_entry_1', 'for_2'),
                ('for_2', 'for_init_2'),
                ('for_init_2', 'for_condition_2'),
                ('for_condition_2', 'for_exit_2'),
                ('for_update_2', 'for_condition_2'),
                ('for_condition_2', 'for_body_entry_2'),
                ('for_body_entry_2', 'continue'),
                ('continue', 'for_update_1'),
                ('for_body_exit_2', 'for_update_2'),
                ('for_exit_2', 'for_body_exit_1'),
                ('for_body_exit_1', 'for_update_1')
            ])
        ))

    # def test_adg_labeled_statement_with_not_used_continue(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         goto: {
    #             continue goto;
    #         }
    #     """
    #     node = parser.parse(bts).root_node.children[0]
    #     assert node.type == 'labeled_statement'
    #     adg = mk_empty_adg()
    #     mk_adg_labeled_statement(node, adg)
    #     print(adg.to_cfg())
    #     self.assertEqual(len(adg._continue_nodes), 1)

    # def test_adg_nested_for_with_break_to_label(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         goto:{
    #             for (int i = 0; i < 10; i++) {
    #                 for (int j = 0; j < 10; j++) {
    #                     break goto;
    #                 }
    #         }
    #     """
    #     node = parser.parse(bts).root_node
    #     cfg = mk_cfg(node, source=bts)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('init_1', 'condition_1'),
    #             ('condition_1', 'exit'),
    #             ('update_1', 'condition_1'),
    #             ('condition_1', 'init_2'),
    #             ('init_2', 'condition_2'),
    #             ('condition_2', 'update_1'),
    #             ('condition_2', 'break'),
    #             ('break', 'exit'),
    #             ('update_2', 'condition_2')
    #         ])
    #     ))

    # def test_cfg_nested_for_with_continue_to_label(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         goto:{
    #             for (int i = 0; i < 10; i++) {
    #                 for (int j = 0; j < 10; i++) {
    #                     continue goto;
    #                 }
    #             }
    #         }
    #     """
    #     node = parser.parse(bts).root_node
    #     cfg = mk_cfg(node, source=bts)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('init_1', 'condition_1'),
    #             ('condition_1', 'exit'),
    #             ('update_1', 'condition_1'),
    #             ('condition_1', 'init_2'),
    #             ('init_2', 'condition_2'),
    #             ('condition_2', 'update_1'),
    #             ('condition_2', 'continue'),
    #             ('update_2', 'condition_2'),
    #             ('continue', 'update_1'),
    #         ])
    #     ))

    # def test_cfg_nested_while_with_break_to_label(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         goto:{
    #             while (i < 10) {
    #                 while (j < 10) {
    #                     break goto;
    #                 }
    #         }
    #     """
    #     node = parser.parse(bts).root_node
    #     cfg = mk_cfg(node, source=bts)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('start', 'condition_1'),
    #             ('condition_1', 'exit'),
    #             ('condition_1', 'condition_2'),
    #             ('condition_2', 'condition_1'),
    #             ('condition_2', 'break'),
    #             ('break', 'exit')
    #         ])
    #     ))

    # def test_cfg_nested_while_with_continue_to_label(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         goto:{
    #             while (i < 10) {
    #                 while (j < 10) {
    #                     continue goto;
    #                 }
    #         }
    #     """
    #     node = parser.parse(bts).root_node
    #     cfg = mk_cfg(node, source=bts)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('start', 'condition_1'),
    #             ('condition_1', 'exit'),
    #             ('condition_1', 'condition_2'),
    #             ('condition_2', 'condition_1'),
    #             ('condition_2', 'continue'),
    #             ('continue', 'condition_1')
    #         ])
    #     ))


if __name__ == '__main__':
    main()
