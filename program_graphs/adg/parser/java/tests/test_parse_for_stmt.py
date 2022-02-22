
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import mk_adg_for
from program_graphs.adg.adg import mk_empty_adg
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

    def test_adg_for(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                a = 9;
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        adg = mk_empty_adg()
        mk_adg_for(for_node, adg)
        # print(adg.to_cfg())
        # adg.remove_edges_from([(a, b) for (a, b, cflow) in adg.edges(data='cflow') if cflow is not True])
        # print(adg.nodes(), adg.edges(data='cflow'))

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('for', 'init'),
                ('init', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'stmt'),
                ('stmt', 'body_exit'),
                ('body_exit', 'update'),
                ('update', 'condition')
            ])
        ))

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cdg(), nx.DiGraph([
                ('for', 'init'),
                ('for', 'condition'),
                ('for', 'exit'),
                ('condition', 'for_body'),
                ('condition', 'update'),
                ('for_body', 'stmt'),
                ('for_body', 'for_body_exit'),
            ])
        ))

    # def test_cfg_for_without_init(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (; i < 10; i++) {
    #             a = 9;
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg, nx.DiGraph([
    #             ('start', 'condition'),
    #             ('condition', 'exit'),
    #             ('condition', 'body'),
    #             ('body', 'condition')
    #         ])
    #     ))

    # def test_cfg_for_without_update(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (int i = 0; i < 10;) {
    #             a = 9;
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg, nx.DiGraph([
    #             ('start', 'condition'),
    #             ('condition', 'exit'),
    #             ('condition', 'body'),
    #             ('body', 'condition')
    #         ])
    #     ))

    # def test_cfg_for_without_init_and_update(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (; i < 10;) {
    #             a = 9;
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg, nx.DiGraph([
    #             ('start', 'condition'),
    #             ('condition', 'exit'),
    #             ('condition', 'body'),
    #             ('body', 'condition')
    #         ])
    #     ))

    def test_adg_for_with_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                stmt();
                break;
                stmt();
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        adg = mk_empty_adg()
        mk_adg_for(for_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('for', 'init'),
                ('init', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'stmt_1'),
                ('stmt_1', 'stmt_break'),
                ('stmt_break', 'exit'),
                ('stmt_2', 'body_exit'),
                ('body_exit', 'update'),
                ('update', 'condition')
            ])
        ))

    def test_adg_for_with_continue(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for (int i = 0; i < 10; i++) {
                stmt();
                continue;
                stmt();
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'for_statement'
        adg = mk_empty_adg()
        mk_adg_for(for_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('for', 'init'),
                ('init', 'condition'),
                ('condition', 'exit'),
                ('condition', 'body'),
                ('body', 'stmt_1'),
                ('stmt_1', 'stmt_continue'),
                ('stmt_continue', 'update'),
                ('update', 'condition'),
                ('stmt_2', 'body_exit'),
                ('body_exit', 'update')
            ])
        ))

    # def test_cfg_nested_for_with_break(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (int i = 0; i < 10; i++) {
    #             for (int i = 0; i < 10; i++) {
    #                 break;
    #             }
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     assert nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('init_1', 'condition_1'),
    #             ('condition_1', 'exit'),
    #             ('update_1', 'condition_1'),
    #             ('condition_1', 'init_2'),
    #             ('init_2', 'condition_2'),
    #             ('condition_2', 'break'),
    #             ('condition_2', 'update_1'),
    #             ('break', 'update_1'),
    #             ('update_2', 'condition_2'),
    #         ])
    #     )

    # def test_cfg_for_and_continue_inside_if(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (int i = 0; i < 10; i++) {
    #             if (i > 2) {
    #                 continue;
    #             }
    #             b = 2;
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg, nx.DiGraph([
    #             ('init', 'condition'),
    #             ('condition', 'if'),
    #             ('if', 'continue'),
    #             ('continue', 'update'),
    #             ('if', 'statement'),
    #             ('statement', 'update'),
    #             ('update', 'condition'),
    #             ('condition', 'exit')
    #         ])
    #     ))

    # def test_cfg_for_without_init_and_continue_inside_if(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         for (int i = 0; i < 10;) {
    #             if (i > 2) {
    #                 continue;
    #             }
    #             b = 2;
    #         }
    #     """
    #     for_node = parser.parse(bts).root_node.children[0]
    #     assert for_node.type == 'for_statement'
    #     cfg = mk_cfg_for(for_node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg, nx.DiGraph([
    #             ('init', 'condition'),
    #             ('condition', 'if'),
    #             ('if', 'continue'),
    #             ('continue', 'condition'),
    #             ('if', 'statement'),
    #             ('statement', 'condition'),
    #             ('condition', 'exit')
    #         ])
    #     ))


if __name__ == '__main__':
    main()
