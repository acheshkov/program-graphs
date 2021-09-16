
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_try_catch, mk_cfg_catch, mk_cfg_try_with_resources
import networkx as nx  # type: ignore
from program_graphs.utils.graph import filter_nodes


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

    def test_cfg_try_catch_trivial(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
            } catch (Exception e) {
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        cfg = mk_cfg_try_catch(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch'), ('catch', 'exit'), ('try', 'exit')
            ])
        ))

    def test_cfg_try_catch(self) -> None:
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
        cfg = mk_cfg_try_catch(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch'), ('catch', 'exit'), ('try', 'exit')
            ])
        ))

    def test_cfg_try_catch_finally(self) -> None:
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
        cfg = mk_cfg_try_catch(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch'), ('catch', 'finally'), ('try', 'finally')
            ])
        ))

    def test_cfg_try_catch_finally_nested(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                try {
                    stmt();
                } catch (Exception e) {
                    stmt();
                } finally{
                    stmt();
                }
            } catch (Exception e) {
                stmt();
            } finally{
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        cfg = mk_cfg_try_catch(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try_1_2', 'catch_2'),
                ('try_1_2', 'finally_2'),
                ('catch_2', 'finally_2'),
                ('finally_2', 'catch_1'),
                ('catch_1', 'finally_1'),
                ('finally_2', 'finally_1'),
            ])
        ))

    def test_cfg_try_multiple_catch_finally(self) -> None:
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
        cfg = mk_cfg_try_catch(node)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch_1'),
                ('try', 'catch_2'),
                ('catch_1', 'finally'),
                ('catch_2', 'finally'),
                ('try', 'finally')
            ])
        ))

    def test_cfg_try_finally(self) -> None:
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
        cfg = mk_cfg_try_catch(node)
        self.assertEqual(len(cfg.nodes()), 1)
        nodes = list(cfg.nodes())
        self.assertEqual(len(cfg.get_block(nodes[0])), 2)

    def test_cfg_try_catch_finally_content(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
                stmt();
                stmt();
            } catch (Exception e) {
                stmt();
                stmt();
            } finally{
                stmt();
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        cfg = mk_cfg_try_catch(node)
        for node in cfg.nodes():
            self.assertGreaterEqual(len(cfg.get_block(node)), 2)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch'), ('catch', 'finally'), ('try', 'finally')
            ])
        ))

    def test_cfg_catch_has_formal_parameters(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
            } catch (Exception e) {
            }
        """
        node = filter_nodes(parser.parse(bts).root_node, ['catch_clause'])[0]
        assert node.type == 'catch_clause'
        cfg = mk_cfg_catch(node)
        for block_id in cfg.nodes():
            for node in cfg.get_block(block_id):
                self.assertTrue(node.type, 'catch_formal_parameter')

    def test_cfg_try_with_resources_has_resources(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try (T1 a = mk1(); T2 b = mk2()) {
            }
        """
        node = filter_nodes(parser.parse(bts).root_node, ['try_with_resources_statement'])[0]
        assert node.type == 'try_with_resources_statement'
        cfg = mk_cfg_try_with_resources(node)
        self.assertTrue(len(cfg.get_block(cfg.entry_node())), 2)


if __name__ == '__main__':
    main()
