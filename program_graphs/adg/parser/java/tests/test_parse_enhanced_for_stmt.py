
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.adg.parser.java.parser import mk_adg_enhanced_for
from program_graphs.adg.adg import mk_empty_adg
import networkx as nx  # type: ignore


class TestParseEnhancedFOR(TestCase):

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

    def test_adg_enhanced_for(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for(T item : array) {
                stmt();
            }
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'enhanced_for_statement'
        adg = mk_empty_adg()
        mk_adg_enhanced_for(for_node, adg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cfg(), nx.DiGraph([
                ('for', 'exit'),
                ('for', 'for_body'),
                ('for_body', 'stmt'),
                ('stmt', 'for_body_exit'),
                ('for_body_exit', 'for')
            ])
        ))

        self.assertTrue(nx.algorithms.is_isomorphic(
            adg.to_cdg(), nx.DiGraph([
                ('for', 'for_body'),
                ('for', 'exit'),
                ('for_body', 'stmt'),
                ('for_body', 'for_body_exit')
            ])
        ))

    def test_adg_enhanced_for_no_body(self) -> None:
        parser = self.get_parser()
        bts = b"""
            for(T item : array);
        """
        for_node = parser.parse(bts).root_node.children[0]
        assert for_node.type == 'enhanced_for_statement'
        adg = mk_empty_adg()
        mk_adg_enhanced_for(for_node, adg)
        self.assertEqual(len(adg.nodes()), 1)


if __name__ == '__main__':
    main()
