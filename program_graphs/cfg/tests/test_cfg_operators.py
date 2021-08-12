
from unittest import TestCase, main
from program_graphs import CFG
from program_graphs.cfg.cfg import merge_cfg
from program_graphs.cfg.operators import mk_empty_cfg, combine, find_redundant_exit_nodes
from program_graphs.cfg.operators import remove_empty_node, remove_empty_nodes
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

    def test_combine_adds_edge(self):
        cfg = CFG([1])
        cfg = combine(cfg, CFG([2]))
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([("A", "B")])
        ))

    def test_combine_adds_edge_2(self):
        cfg_1 = CFG()
        node_1 = cfg_1.add_node([])
        node_2 = cfg_1.add_node([])
        node_3 = cfg_1.add_node([])
        cfg_1.add_edges_from([(node_1, node_3), (node_2, node_3)])

        cfg_2 = CFG()
        node_4 = cfg_2.add_node([])
        node_5 = cfg_2.add_node([])
        cfg_2.add_edges_from([(node_4, node_5)])

        cfg = combine(cfg_1, cfg_2, node_1, node_4)
        self.assertTrue(nx.algorithms.is_isomorphic(
            cfg,
            nx.DiGraph([("A", "C"), ("B", "C"), ("A", "D"), ("D", "E")])
        ))

    def test_merge_keeps_names_and_ids(self):
        cfg_1 = CFG()
        cfg_1.add_node([1], "A", "ID-A")
        cfg_2 = CFG()
        cfg_1.add_node([2], "B", "ID-B")
        merge_cfg(cfg_1, cfg_2)
        self.assertIsNotNone(cfg_1.find_node_by_id('ID-A'))
        self.assertIsNotNone(cfg_1.find_node_by_id('ID-B'))
        self.assertIn('A', [name for _, name in cfg_1.nodes(data='name')])
        self.assertIn('B', [name for _, name in cfg_1.nodes(data='name')])

    def test_remove_node(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([])
        node_4 = cfg.add_node([3])
        cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4)])
        remove_empty_node(cfg, node_3)
        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "C"), ("B", "C")]))
        )

    def test_reduce_redundant_exit_nodes_1(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([])
        node_4 = cfg.add_node([])
        cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4)])

        exit_nodes = find_redundant_exit_nodes(cfg)
        self.assertEqual(exit_nodes, [node_3])
        cfg = remove_empty_nodes(cfg, exit_nodes)

        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "C"), ("B", "C")]))
        )

    def test_reduce_redundant_exit_nodes_2(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([])
        node_3 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2), (node_2, node_3)])
        exit_nodes = find_redundant_exit_nodes(cfg)
        self.assertEqual(exit_nodes, [node_2])
        cfg = remove_empty_nodes(cfg, exit_nodes)

        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "B")]))
        )

    def test_reduce_redundant_exit_nodes_abstain(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([])
        node_4 = cfg.add_node([3])
        node_5 = cfg.add_node([4])
        cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4), (node_3, node_5)])
        exit_nodes = find_redundant_exit_nodes(cfg)
        self.assertEqual(exit_nodes, [])

    def test_reduce_redundant_exit_nodes_3(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([])
        node_4 = cfg.add_node([])
        node_5 = cfg.add_node([3])
        node_6 = cfg.add_node([4])
        cfg.add_edges_from([
            (node_1, node_3),
            (node_2, node_3),
            (node_3, node_4),
            (node_4, node_5),
            (node_4, node_6),
        ])
        exit_nodes = find_redundant_exit_nodes(cfg)
        self.assertEqual(exit_nodes, [node_3, node_4])
        remove_empty_nodes(cfg, exit_nodes)
        self.assertTrue(
            nx.algorithms.is_isomorphic(
                cfg,
                nx.DiGraph([("A", "C"), ("B", "C"), ("C", "D"), ("C", "E")])
            )
        )


if __name__ == '__main__':
    main()
