from tree_sitter import Language, Parser  # type: ignore
from unittest import TestCase, main
from tree_sitter import Node as Statement
from program_graphs.ddg.parser.java.utils import get_all_variables, get_variables_read, get_variables_written


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

    def test_variables_writes_declarations(self):
        code = b'''
            int a = c;
        '''
        ast = self.parse(code)
        variables = get_variables_written(ast, code)
        self.assertEqual(variables, set('a'))

    def test_variables_writes_assignment(self):
        code = b'''
            a = c;
        '''
        ast = self.parse(code)
        variables = get_variables_written(ast, code)
        self.assertEqual(variables, set('a'))

    def test_variables_writes_declaration_multiple(self):
        code = b'''
            int a = c, b = d;
        '''
        ast = self.parse(code)
        variables = get_variables_written(ast, code)
        self.assertEqual(variables, set(['a', 'b']))

    def test_variables_writes_syntax_sugar(self):
        code = b'''
            a++;
            b+=1;
        '''
        ast = self.parse(code)
        variables = get_variables_written(ast, code)
        self.assertEqual(variables, set(['a', 'b']))

    def test_variables_writes_declaration_for(self):
        code = b'''
            for (int i = 0; ; j++){
            }
        '''
        ast = self.parse(code)
        variables = get_variables_written(ast, code)
        self.assertEqual(variables, set(['i', 'j']))

    def test_variables_reads_declarations_empty(self):
        code = b'''
            int a;
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set())

    def test_variables_reads_declarations_non_empty_but_constant(self):
        code = b'''
            int a = 1;
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set())

    def test_variables_reads_declarations_non_empty(self):
        code = b'''
            int a = b;
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set('b'))

    def test_variables_reads_declarations_multiple(self):
        code = b'''
            int a = c, b = d;
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set(['c', 'd']))

    def test_variables_reads_declaration_for(self):
        code = b'''
            for (int i = j; ; j = k + 1){
            }
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set(['j', 'k']))

    def test_variables_reads_boolean_expression(self):
        code = b'''
            a = b == c;
        '''
        ast = self.parse(code)
        variables = get_variables_read(ast, code)
        self.assertEqual(variables, set(['b', 'c']))

    def test_all_variables(self):
        code = b'''
            int a = 1;
            int b = 2;
            int c = a + b;
        '''
        ast = self.parse(code)
        variables = get_all_variables(ast, code)
        self.assertEqual(variables, set(['a', 'b', 'c']))


if __name__ == '__main__':
    main()
