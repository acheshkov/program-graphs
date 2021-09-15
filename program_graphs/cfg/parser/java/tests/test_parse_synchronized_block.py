
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_synchronized


class TestParseSynchronizedBlock(TestCase):

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

    def test_cfg_synchronized(self) -> None:
        parser = self.get_parser()
        bts = b"""
            synchronized(this){
                stmt();
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'synchronized_statement'
        cfg = mk_cfg_synchronized(node)
        self.assertEqual(len(cfg.nodes()), 1)
        nodes = list(cfg.nodes())
        self.assertEqual(len(cfg.get_block(nodes[0])), 1)

    def test_cfg_synchronized_nested(self) -> None:
        parser = self.get_parser()
        bts = b"""
            synchronized(a){
                stmt();
                synchronized(b){
                    stmt();
                }
            }
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'synchronized_statement'
        cfg = mk_cfg_synchronized(node)
        self.assertEqual(len(cfg.nodes()), 1)
        nodes = list(cfg.nodes())
        self.assertEqual(len(cfg.get_block(nodes[0])), 2)


if __name__ == '__main__':
    main()
