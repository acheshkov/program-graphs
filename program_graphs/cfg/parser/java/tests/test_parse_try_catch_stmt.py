
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_try_catch, mk_cfg_if_else
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

    def test_cfg_try_catch_trivbial(self) -> None:
        parser = self.get_parser()
        bts = b"""
            try {
            } catch (Exception e) {
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'try_statement'
        cfg = mk_cfg_try_catch(node)
        self.assertEqual(len(cfg.nodes()), 1)

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
            self.assertEqual(len(cfg.get_block(node)), 2)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([
                ('try', 'catch'), ('catch', 'finally'), ('try', 'finally')
            ])
        ))


if __name__ == '__main__':
    main()
