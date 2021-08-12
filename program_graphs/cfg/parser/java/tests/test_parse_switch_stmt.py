
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_switch_case_group, mk_cfg_switch_default_group, mk_cfg_switch
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

    def test_cfg_switch_case_group(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                case 1:  a = 3;
            }
        """
        node = parser.parse(bts).root_node.children[0].child_by_field_name("body").children[1]
        assert node.type == 'switch_block_statement_group'
        cfg = mk_cfg_switch_case_group(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([("case", "body"), ("body", "exit"), ("case", "exit")])
        ))

    def test_cfg_switch_default_group(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                default:  a = 3;
            }
        """
        node = parser.parse(bts).root_node.children[0].child_by_field_name("body").children[1]
        assert node.type == 'switch_block_statement_group'
        cfg = mk_cfg_switch_default_group(node)
        self.assertEqual(len(cfg.nodes()), 1)

    def test_cfg_switch(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (a) {
                case 1:  a = 1;
                case 2:  a = 2;
                default: a = 0;
                default: b = 0;
            }
        """
        switch_node = parser.parse(bts).root_node.children[0]
        assert switch_node.type == 'switch_expression'
        cfg = mk_cfg_switch(switch_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ("case_1", "body_1"),
                ("body_1", "case_2"),
                ("case_1", "case_2"),
                ("case_2", "body_2"),
                ("case_2", "exit"),
                ("body_2", "exit"),
            ])
        ))

    def test_cfg_switch_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            switch (i) {
                case 1: break;
                case 2: break;
            }
        """
        switch_node = parser.parse(bts).root_node.children[0]
        assert switch_node.type == 'switch_expression'
        cfg = mk_cfg_switch(switch_node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ("case_1", "break_1"),
                ("break_1", "exit"),
                ("case_1", "case_2"),
                ("case_2", "break_2"),
                ("break_2", 'exit'),
                ("case_2", "exit")
            ])
        ))


if __name__ == '__main__':
    main()
