
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.adg import mk_empty_adg
from program_graphs.adg.parser.java.parser import mk_adg_try_catch
import networkx as nx  # type: ignore


class TestParseTryCatch(TestCase):

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

    def test_adg_try_catch_trivial(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
            } catch (Exception e) {
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'try-block-empty'),
                ('try-block-empty', 'catch-block'),
                ('catch-block', 'formal-parameters'),
                ('formal-parameters', 'catch-body-empty')
            ])
        ))

    def test_adg_try_catch(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                stmt();
            } catch (Exception e) {
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'try-block-entry'),
                ('try-block-entry', 'stmt_1'),
                ('stmt_1', 'try-block-exit'),
                ('try-block-exit', 'catch-block'),
                ('catch-block', 'formal-parameters'),
                ('formal-parameters', 'catch-body-exit'),
                ('formal-parameters', 'catch-body-entry'),
                ('catch-body-entry', 'stmt_2'),
                ('stmt_2', 'catch-body-exit')
            ])
        ))

    def test_adg_try_catch_finally(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                stmt();
            } catch (Exception e) {
                stmt();
            } finally{
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'try-block-entry'),
                ('try-block-entry', 'stmt_1'),
                ('stmt_1', 'try-block-exit'),
                ('try-block-exit', 'catch-block'),
                ('catch-block', 'formal-parameters'),
                ('formal-parameters', 'catch-body-entry'),
                ('formal-parameters', 'catch-body-exit'),
                ('catch-body-entry', 'stmt_2'),
                ('stmt_2', 'catch-body-exit'),
                ('catch-body-exit', 'finally-block-entry'),
                ('finally-block-entry', 'stmt3'),
                ('stmt3', 'finally-block-exit')
            ])
        ))

    # def test_cfg_try_catch_finally_nested(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         try {
    #             try {
    #                 stmt();
    #             } catch (Exception e) {
    #                 stmt();
    #             } finally{
    #                 stmt();
    #             }
    #         } catch (Exception e) {
    #             stmt();
    #         } finally{
    #             stmt();
    #         }
    #     """
    #     node = parser.parse(bts).root_node.children[0]
    #     assert node.type == 'try_statement'
    #     cfg = mk_cfg_try_catch(node)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('try_1_2', 'catch_2'),
    #             ('try_1_2', 'finally_2'),
    #             ('catch_2', 'finally_2'),
    #             ('finally_2', 'catch_1'),
    #             ('catch_1', 'finally_1'),
    #             ('finally_2', 'finally_1'),
    #         ])
    #     ))

    def test_adg_try_multiple_catch_finally(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                stmt();
            } catch (Exception e) {
                stmt();
            } catch (Exception e) {
                stmt();
            } finally{
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'try-block-entry'),
                ('try-block-entry', 'stmt_1'),
                ('stmt_1', 'try-block-exit'),
                ('try-block-exit', 'catch-block'),
                ('catch-block', 'formal-parameters'),
                ('formal-parameters', 'catch-body-entry'),
                ('formal-parameters', 'catch-body-exit'),
                ('catch-body-entry', 'stmt_2'),
                ('stmt_2', 'catch-body-exit'),
                ('catch-body-exit', 'catch-block_2'),
                ('catch-block_2', 'formal-parameters_2'),
                ('formal-parameters_2', 'catch-body-entry_2'),
                ('formal-parameters_2', 'catch-body-exit_2'),
                ('catch-body-entry_2', 'stmt_3'),
                ('stmt_3', 'catch-body-exit_2'),
                ('catch-body-exit_2', 'finally-block-entry'),
                ('finally-block-entry', 'stmt4'),
                ('stmt4', 'finally-block-exit')
            ])
        ))

    def test_adg_try_finally(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                stmt();
            } finally{
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'try-block-entry'),
                ('try-block-entry', 'stmt_1'),
                ('stmt_1', 'try-block-exit'),
                ('try-block-exit', 'finally-block-entry'),
                ('finally-block-entry', 'stmt_2'),
                ('stmt_2', 'finally-block-exit')
            ])
        ))

    # def test_cfg_try_catch_finally_content(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         try {
    #             stmt();
    #             stmt();
    #         } catch (Exception e) {
    #             stmt();
    #             stmt();
    #         } finally{
    #             stmt();
    #             stmt();
    #         }
    #     """
    #     node = parser.parse(bts).root_node.children[0]
    #     assert node.type == 'try_statement'
    #     cfg = mk_cfg_try_catch(node)
    #     for node in cfg.nodes():
    #         self.assertGreaterEqual(len(cfg.get_block(node)), 2)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([
    #             ('try', 'catch'), ('catch', 'finally'), ('try', 'finally')
    #         ])
    #     ))

    # def test_cfg_catch_has_formal_parameters(self) -> None:
    #     parser = self.get_parser()
    #     bts = b"""
    #         try {
    #         } catch (Exception e) {
    #         }
    #     """
    #     node = filter_nodes(parser.parse(bts).root_node, ['catch_clause'])[0]
    #     assert node.type == 'catch_clause'
    #     cfg = mk_cfg_catch(node)
    #     for block_id in cfg.nodes():
    #         for node in cfg.get_block(block_id):
    #             self.assertTrue(node.type, 'catch_formal_parameter')

    def test_adg_try_with_resources_has_resources(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try (T1 a = mk1(); T2 b = mk2()) {
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_with_resources_statement'
        adg = mk_empty_adg()
        mk_adg_try_catch(node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(),
            nx.DiGraph([
                ('try', 'T1 a = mk1();'),
                ('T1 a = mk1();', 'T2 b = mk2()'),
                ('T2 b = mk2()', 'try-block-entry'),
                ('try-block-entry', 'stmt'),
                ('stmt', 'try-block-exit')
            ])
        ))


if __name__ == '__main__':
    main()
