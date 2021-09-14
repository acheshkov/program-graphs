from unittest import TestCase, main
from program_graphs.cfg.parser.java import parse
from program_graphs.ddg.ddg import DDG, mk_ddg
import networkx as nx  # type: ignore


class TestDDG(TestCase):

    def mk_ddg_from_source(self, code: str) -> DDG:
        cfg = parse(code)
        return mk_ddg(cfg, code)

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
                ("i++", "i<10")
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
            self.assertEqual(vars, set([('a', 'int'), ('b', 'int')]))

    def test_ddg_nodes_has_statments_attribute(self) -> None:
        code = '''
            int a = 0;
            int b = a;
        '''
        ddg = self.mk_ddg_from_source(code)
        for _, stmt in ddg.nodes(data='statement'):
            self.assertIsNotNone(stmt)

    def test_ddg_edge_has_var_attribute(self) -> None:
        code = '''
            int a = 0;
            int b = a;
        '''
        ddg = self.mk_ddg_from_source(code)
        for _, _, vars in ddg.edges(data='vars'):
            self.assertIsNotNone(vars)
            self.assertEqual(vars, set([('a', 'int')]))


if __name__ == '__main__':
    main()
