
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_method_declaration


class TestMethodDeclaration(TestCase):

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

    def test_method_declaration_params(self) -> None:
        parser = self.get_parser()
        bts = b"""
            public class Main {
                static void myMethod(int a, int b) {
                }
            }
        """
        node = parser.parse(bts).root_node.children[0].children[-1].children[1]
        assert node.type == 'method_declaration'
        cfg = mk_cfg_method_declaration(node)
        self.assertEqual(len(cfg.nodes()), 1)
        nodes = list(cfg.nodes())
        self.assertEqual(len(cfg.get_block(nodes[0])), 2)

    def test_method_declaration_with_body(self) -> None:
        parser = self.get_parser()
        bts = b"""
            public class Main {
                static void myMethod(int a, int b) {
                    if (a > 1){
                        b = 2;
                    }
                }
            }
        """
        node = parser.parse(bts).root_node.children[0].children[-1].children[1]
        assert node.type == 'method_declaration'
        cfg = mk_cfg_method_declaration(node)
        self.assertEqual(len(cfg.nodes()), 3)
        nodes = list(cfg.nodes())
        self.assertEqual(len(cfg.get_block(nodes[cfg.entry_node()])), 3)


if __name__ == '__main__':
    main()
