
from unittest import TestCase, main
from tree_sitter import Language, Parser  # type: ignore
from program_graphs.cfg.parser.java.parser import mk_cfg_break


class TestParseReturn(TestCase):

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

    def test_cfg_break(self) -> None:
        parser = self.get_parser()
        bts = b"""
            break;
        """
        node = parser.parse(bts).root_node
        cfg = mk_cfg_break(node)
        assert len(cfg.break_nodes) == 1


if __name__ == '__main__':
    main()
