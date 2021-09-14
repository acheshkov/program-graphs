from tree_sitter import Language, Parser  # type: ignore
from unittest import TestCase, main
from tree_sitter import Node as Statement
from program_graphs.ddg.parser.java.utils import get_declared_variables


class TestParseVariables(TestCase):

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

    def parse(self, code: bytes) -> Statement:
        parser = self.get_parser()
        return parser.parse(code).root_node

    def test_var_declaration_single(self) -> None:
        code = b'''
            int a = c;
        '''
        ast = self.parse(code)
        declarations = get_declared_variables(ast, code)
        self.assertEqual(declarations, set(['a']))

    def test_var_declaration_multiple(self) -> None:
        code = b'''
            int a = c, b = d;
        '''
        ast = self.parse(code)
        declarations = get_declared_variables(ast, code)
        self.assertEqual(declarations, set(['a', 'b']))

    def test_var_method_declaration(self) -> None:
        code = b"""
            public class A {
                static void foo(int a, int b) {
                    ;
                }
            }
        """
        ast = self.parse(code)
        declarations = get_declared_variables(ast, code)
        self.assertEqual(declarations, set(['a', 'b']))

    def test_var_try_catch(self) -> None:
        code = b'''
           try {
                ;
            } catch (T1 | T2 e) {
                ;
            }
        '''
        ast = self.parse(code)
        declarations = get_declared_variables(ast, code)
        self.assertEqual(declarations, set(['e']))


if __name__ == '__main__':
    main()
