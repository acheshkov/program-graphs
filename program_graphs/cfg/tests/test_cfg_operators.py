
from unittest import TestCase, main
from program_graphs import CFG
from program_graphs.cfg.operators import mk_empty_cfg, combine, reduce_redundant_exit_nodes
from program_graphs.cfg.edge_contraction import edge_contraction
import networkx as nx  # type: ignore


class TestCFGOperators(TestCase):

    def test_mk_empty_cfg(self):
        cfg_empty = mk_empty_cfg()
        self.assertEqual(len(cfg_empty.entry_nodes()), 1)
        self.assertEqual(len(cfg_empty.exit_nodes()), 1)

    def test_combine_two_empty(self):
        cfg_empty_1 = mk_empty_cfg()
        cfg_empty_2 = mk_empty_cfg()
        cfg_empty = combine(cfg_empty_1, cfg_empty_2)
        self.assertEqual(len(cfg_empty.entry_nodes()), 1)
        self.assertEqual(len(cfg_empty.exit_nodes()), 1)

    def test_combine_with_empty(self):
        cfg = CFG()
        node_1 = cfg.add_node([None])
        node_2 = cfg.add_node([None])
        node_3 = cfg.add_node([None])
        node_4 = cfg.add_node([None])
        cfg.add_edges_from([
            (node_1, node_2), (node_1, node_3), (node_2, node_4), (node_3, node_4)
        ])
        cfg_empty = mk_empty_cfg()

        self.assertEqual(
            len(combine(cfg, cfg_empty).nodes()),
            len(cfg.nodes())
        )
        self.assertEqual(
            len(combine(cfg_empty, cfg).nodes()),
            len(cfg.nodes())
        )

    def test_combine_2(self):
        cfg_1 = CFG()
        node_1 = cfg_1.add_node([1])
        node_2 = cfg_1.add_node([2])
        node_3 = cfg_1.add_node([3])
        node_4 = cfg_1.add_node([4])
        cfg_1.add_edges_from([
            (node_1, node_2), (node_1, node_3), (node_2, node_4), (node_3, node_4)
        ])

        cfg_2 = CFG()
        cfg_2.add_node([5])
        cfg = combine(cfg_1, cfg_2)
        self.assertIn([4, 5], cfg.node_id_2_block)

    def test_edge_contraction(self):
        cfg = CFG()
        node_1 = cfg.add_node([1, 2], 'A-1')
        node_2 = cfg.add_node([3, 4], 'A-2')
        cfg = edge_contraction(cfg, [(node_1, node_2)])
        self.assertEqual(len(cfg.nodes()), 1)

    def test_reduce_redundant_exit_nodes_1(self):
        g = CFG()
        node_1 = g.add_node([1])
        node_2 = g.add_node([2])
        node_3 = g.add_node([])
        node_4 = g.add_node([])
        g.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4)])
        g = reduce_redundant_exit_nodes(g)
        self.assertTrue(
            nx.algorithms.is_isomorphic(g, nx.DiGraph([("A", "C"), ("B", "C")]))
        )

    def test_reduce_redundant_exit_nodes_2(self):
        g = CFG()
        node_1 = g.add_node([1])
        node_2 = g.add_node([])
        node_3 = g.add_node([2])
        g.add_edges_from([(node_1, node_2), (node_2, node_3)])
        g = reduce_redundant_exit_nodes(g)
        self.assertTrue(
            nx.algorithms.is_isomorphic(g, nx.DiGraph([("A", "B")]))
        )


if __name__ == '__main__':
    main()
