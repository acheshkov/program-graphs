
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.adg import mk_empty_adg
from program_graphs.adg.parser.java.parser import mk_adg_switch_case_group, mk_adg_switch_default_group, mk_adg_switch
import networkx as nx  # type: ignore


class TestParseSwitch(TestCase):

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

    def test_adg_switch_case_group(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                case 1:  a = 3;
            }
        """
        node = parser.parse(bts).root_node.children[0].child_by_field_name("body").children[1]
        assert node.type == 'switch_block_statement_group'
        adg = mk_empty_adg()
        mk_adg_switch_case_group(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ("case", "condition"),
                ("condition", "a = 3;"),
                ("condition", "exit"),
                ("a = 3;", "exit")
            ])
        ))

    def test_adg_switch_default_group(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                default:  a = 3;
            }
        """
        node = parser.parse(bts).root_node.children[0].child_by_field_name("body").children[1]
        assert node.type == 'switch_block_statement_group'
        adg = mk_empty_adg()
        mk_adg_switch_default_group(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ("case", "a = 3;"),
                ("a = 3;", "exit")
            ])
        ))

    def test_adg_switch(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                case 1:  a = 1;
                case 2:  a = 2;
                default: a = 0;
            }
        """
        switch_node = parser.parse(bts).root_node.children[0]
        assert switch_node.type == 'switch_expression'
        adg = mk_empty_adg()
        mk_adg_switch(switch_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ("switch", "case_1"),
                ("case_1", "case_1_condition"),
                ("case_1_condition", "a = 1;"),
                ("a = 1;", 'case_1_exit'),
                ("case_1_exit", "case_2"),
                ("case_1_condition", "case_1_exit"),

                ("case_2", "case_2_condition"),
                ("case_2_condition", "a = 2;"),
                ('a = 2;', 'case_2_exit'),
                ("case_2_exit", "default"),
                ("case_2_condition", "case_2_exit"),

                ("default", "a = 0;"),
                ("a = 0;", "default_exit"),
                ("default_exit", 'exit')

            ])
        ))

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cdg(),
            nx.DiGraph([
                ("switch", "case_1"),
                ("case_1", "case_1_condition"),
                ("case_1_condition", "a = 1"),
                ("case_1_condition", "case_1_exit"),

                ("switch", "case_2"),
                ("case_2", "case_2_condition"),
                ("case_2_condition", "a = 2"),
                ("case_2_condition", "case_2_exit"),

                ("switch", "default"),
                ("default", "a = 0"),
                ("default", "default_exit")
            ])
        ))

    # def test_adg_switch_with_break(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         switch (i) {
    #             case 1: break;
    #             case 2: break;
    #         }
    #     """
    #     switch_node = parser.parse(bts).root_node.children[0]
    #     assert switch_node.type == 'switch_expression'
    #     cfg = mk_cfg_switch(switch_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ("case_1", "break_1"),
    #             ("break_1", "exit"),
    #             ("case_1", "case_2"),
    #             ("case_2", "break_2"),
    #             ("break_2", 'exit'),
    #             ("case_2", "exit")
    #         ])
    #     ))


if __name__ == '__main__':
    main()
