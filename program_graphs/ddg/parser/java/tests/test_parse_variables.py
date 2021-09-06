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

    def test_variables_with_generic_types(self):
        code = b'''
           T<P> a = new T<P>(b, c);
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set(['b', 'c']))
        self.assertEqual(write_vars, set(['a']))

    def test_variables_anonymous_class(self):
        code = b'''
           T a = new T(){
               int c = 1;
               public void foo(x, y) {
                   int d = 1;
               }
           }.init(b)
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set(['b']))
        self.assertEqual(write_vars, set(['a']))

    def test_variables_with_lambda_expression(self):
        code = b'''
           T a = ((k, v) -> v == null ? 1 : v + 1)
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set(['a']))

    def test_variables_method_invocation(self):
        code = b'''
           T a = b.m1(c).m2(d);
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set(['b', 'c', 'd']))
        self.assertEqual(write_vars, set(['a']))

    def test_variables_try_with_resources(self):
        code = b'''
           try (T1 a = mk1(); T2 b = mk2()) {
                ;
            }
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set(['a', 'b']))

    def test_variables_try_catch(self):
        code = b'''
           try {
                ;
            } catch (T1 | T2 e) {
                ;
            }
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set(['e']))

    def test_variables_labeled_stmts(self):
        code = b'''
           l1: while (true) {
                ;
            }
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set())

    def test_variables_labeled_break(self):
        code = b'''
           l1: while (true) {
                break l1;
            }
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set())

    def test_variables_labeled_continue(self):
        code = b'''
           l1: while (true) {
                continue l1;
            }
        '''
        ast = self.parse(code)
        read_vars = get_variables_read(ast, code)
        write_vars = get_variables_written(ast, code)
        self.assertEqual(read_vars, set())
        self.assertEqual(write_vars, set())

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
