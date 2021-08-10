
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_continue


class TestParseContinue(TestCase):

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

    def test_cfg_return(self) -> None:
        parser = self.get_parser()
        bts = b"""
            continue;
        """
        node = parser.parse(bts).root_node.children[0]
        assert node.type == 'continue_statement'
        cfg = mk_cfg_continue(node)
        assert len(cfg.continue_nodes) == 1


if __name__ == '__main__':
    main()
