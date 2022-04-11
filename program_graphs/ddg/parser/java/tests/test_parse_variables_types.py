from tree_sitter import Language, Parser  # type: ignore
from unittest import TestCase, main
from tree_sitter import Node as Statement
from program_graphs.ddg.parser.java.utils import get_type, write_read_identifiers


class TestParseVariableTypes(TestCase):

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

    def test_identifier_type_primitive_int(self) -> None:
        code = b'''
            int a = c;
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_type = get_type(write_identifiers[0], code)
        self.assertEqual(var_type, "int")

    def test_identifier_type_primitive_boolean(self) -> None:
        code = b'''
            boolean hasReported = false;
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_type = get_type(write_identifiers[0], code)
        self.assertEqual(var_type, "boolean")

    def test_identifier_type_primitive_long(self) -> None:
        code = b'''
            long a = 0xFFFFFFFFL;
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_type = get_type(write_identifiers[0], code)
        self.assertEqual(var_type, "long")

    def test_identifier_type_generic(self) -> None:
        code = b'''
            T<P> a = new T<P>();
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_type = get_type(write_identifiers[0], code)
        self.assertEqual(var_type, "T,P")

    def test_identifier_object_type(self) -> None:
        code = b'''
            T a = new T();
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_type = get_type(write_identifiers[0], code)
        self.assertEqual(var_type, "T")

    def test_identifier_type_method_declaration(self) -> None:
        code = b'''
            public class A {
                static void foo(int a, T b) {
                    ;
                }
            }
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_types = [get_type(var_identifier, code) for var_identifier in write_identifiers]
        self.assertEqual(var_types, ["int", "T"])

    def test_identifier_type_catch(self) -> None:
        code = b'''
           try {
                ;
            } catch (T1 | T2 e) {
                ;
            }
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_types = [get_type(var_identifier, code) for var_identifier in write_identifiers]
        self.assertEqual(var_types, ['T1,T2'])

    def test_typed_avr_enhanced_for_with_type(self) -> None:
        code = b'''
            for (T v: list) {
            }
        '''
        ast = self.parse(code)
        write_identifiers, _ = write_read_identifiers(ast, code)
        var_types = [get_type(var_identifier, code) for var_identifier in write_identifiers]
        self.assertEqual(var_types, ['T'])


if __name__ == '__main__':
    main()
