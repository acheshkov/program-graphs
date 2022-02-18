from unittest import TestCase, main
from program_graphs.adg.parser.java.parser import parse
from program_graphs.adg.adg import ADG
# from program_graphs.ddg.ddg import DDG, mk_ddg
import networkx as nx  # type: ignore


class TestDDG(TestCase):

    def mk_ddg_from_source(self, code: str) -> ADG:
        adg = parse(code)
        return adg.to_ddg()

    def test_ddg_for(self) -> None:
        code = '''
            for (int i=0; i < 10; i++){
            }
        '''
        ddg = self.mk_ddg_from_source(code)
        self.assertTrue(nx.algorithms.is_isomorphic(
            ddg, nx.DiGraph([
                ("i=0", "i<10"),
                ("i=0", "i++"),
                ("i++", "i<10"),
                ("i++", "i++")
            ])
        ))

    def test_ddg_simple(self) -> None:
        code = '''
            int a = 0;
            int b = a;
        '''
        ddg = self.mk_ddg_from_source(code)
        self.assertTrue(nx.algorithms.is_isomorphic(
            ddg, nx.DiGraph([
                ("a=0", "b=a")
            ])
        ))

    def test_ddg_multiple_vars_from_the_same_node(self) -> None:
        code = '''
            int a = 0, b = 0;
            int c = a + b;
        '''
        ddg = self.mk_ddg_from_source(code)
        for _, _, vars in ddg.edges(data='vars'):
            self.assertIsNotNone(vars)
            self.assertEqual(vars, set(['a', 'b']))

    def test_ddg_nodes_has_vars_attribute(self) -> None:
        code = '''
            int a = 0;
            int b = a;
        '''
        ddg = self.mk_ddg_from_source(code)
        for _, ddep in ddg.nodes(data='read_vars'):
            self.assertIsNotNone(ddep)
        for _, ddep in ddg.nodes(data='write_vars'):
            self.assertIsNotNone(ddep)

    def test_ddg_edge_has_vars_attribute(self) -> None:
        code = '''
            int a = 0;
            int b = a;
        '''
        ddg = self.mk_ddg_from_source(code)
        self.assertEqual(1, len(ddg.edges()))
        for _, _, vars in ddg.edges(data='vars'):
            self.assertIsNotNone(vars)
            self.assertEqual(vars, set(['a']))

    def test_ddg_without_edges(self) -> None:
        code = '''
            int a;
            a = 1;
        '''
        ddg = self.mk_ddg_from_source(code)
        self.assertEqual(0, len(ddg.edges()))


if __name__ == '__main__':
    main()
