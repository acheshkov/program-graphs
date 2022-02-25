
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import mk_adg_while
from program_graphs.adg.adg import mk_empty_adg
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

    def test_adg_while(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                i++;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        adg = mk_empty_adg()
        mk_adg_while(while_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('entry', 'condition'),
                ('condition', 'body_start'),
                ('body_start', 'i++'),
                ('i++', 'body_end'),
                ('body_end', 'condition'),
                ('condition', 'exit')
            ])
        ))

        # self.assertTrue(nx.algorithms.is_isomorphic(
        #     adg.to_cdg(), nx.DiGraph([
        #         ('entry', 'condition'),
        #         ('entry', 'exit'),
        #         ('condition', 'body_start'),
        #         ('condition', 'condition'),
        #         ('body_start', 'i++'),
        #         ('body_start', 'body_end')
        #     ])
        # ))

    def test_adg_while_with_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                continue;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        assert while_node.type == 'while_statement'
        adg = mk_empty_adg()
        mk_adg_while(while_node, adg)

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('entry', 'condition'),
                ('condition', 'body_start'),
                ('body_start', 'continue'),
                ('continue', 'condition'),
                ('body_end', 'condition'),
                ('condition', 'exit')
            ])
        ))

        # self.assertTrue(nx.algorithms.is_isomorphic(
        #     adg.to_cdg(), nx.DiGraph([
        #         ('entry', 'condition'),
        #         ('entry', 'exit'),
        #         ('condition', 'body_start'),
        #         ('condition', 'condition'),
        #         ('body_start', 'i++'),
        #         ('body_start', 'body_end')
        #     ])
        # ))

    def test_adg_while_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            while (i < 5) {
                break;
            }
        """
        while_node = parser.parse(bts).root_node.children[0]
        adg = mk_empty_adg()
        mk_adg_while(while_node, adg)

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('entry', 'condition'),
                ('condition', 'body_start'),
                ('body_start', 'break'),
                ('break', 'exit'),
                ('body_end', 'condition'),
                ('condition', 'exit')
            ])
        ))

    def test_adg_while_nested_break(self) -> None:
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
        adg = mk_empty_adg()
        mk_adg_while(while_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('while_outer', 'condition_out'),
                ('condition_out', 'body_out_start'),
                ('condition_out', 'while_outer_exit'),

                ('body_out_start', 'while_inner'),
                ('while_inner', 'condition_inner'),
                ('condition_inner', 'body_inner_start'),
                ('condition_inner', 'while_inner_exit'),

                ('body_inner_start', 'break'),
                ('break', 'while_inner_exit'),
                ('body_inner_end', 'condition_inner'),

                ('while_inner_exit', 'body_out_end'),
                ('body_out_end', 'condition_out')
            ])
        ))

        # self.assertTrue(nx.algorithms.is_isomorphic(
        #     adg.to_cdg(), nx.DiGraph([
        #         ('while_outer', 'condition_out'),
        #         ('while_outer', 'while_outer_exit'),
        #         ('condition_out', 'body_out_start'),
        #         ('condition_out', 'condition_out'),
        #         ('body_out_start', 'while_inner'),
        #         ('body_out_start', 'body_out_end'),
        #         ('while_inner', 'condition_inner'),
        #         ('while_inner', 'while_inner_exit'),
        #         ('condition_inner', 'body_inner_start'),
        #         ('condition_inner', 'condition_inner'),  # it's incorrect
        #         ('body_inner_start', 'break'),
        #         ('body_inner_start', 'body_inner_end')
        #     ])
        # ))

    def test_adg_while_nested_continue(self) -> None:
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
        adg = mk_empty_adg()
        mk_adg_while(while_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('while_outer', 'condition_out'),
                ('condition_out', 'body_out_start'),
                ('condition_out', 'while_outer_exit'),

                ('body_out_start', 'while_inner'),
                ('while_inner', 'condition_inner'),
                ('condition_inner', 'body_inner_start'),
                ('condition_inner', 'while_inner_exit'),

                ('body_inner_start', 'continue'),
                ('continue', 'condition_inner'),
                ('body_inner_end', 'condition_inner'),

                ('while_inner_exit', 'body_out_end'),
                ('body_out_end', 'condition_out')

            ])
        ))


if __name__ == '__main__':
    main()
