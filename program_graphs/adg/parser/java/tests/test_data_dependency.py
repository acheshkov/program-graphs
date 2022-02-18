
from unittest import TestCase, main
from program_graphs import CFG
from program_graphs.cfg.cfg import merge_cfg
from program_graphs.cfg.operators import mk_empty_cfg, combine, find_redundant_exit_nodes
from program_graphs.cfg.operators import remove_empty_node, remove_empty_nodes
from program_graphs.adg.parser.java.data_dependency import set_diff, merge_var_table_if_requried, update_var_table
from program_graphs.adg.parser.java.data_dependency import create_or_update_data_depependency_link
import networkx as nx  # type: ignore


class TestDataDependency(TestCase):

    def test_set_diff(self):
        self.assertIsNone(set_diff(set([]), set([])))
        self.assertIsNone(set_diff(set([1]), set([])))
        self.assertSetEqual(set_diff(set([]), set([1])), set([1]))
        self.assertSetEqual(set_diff(set([1, 2]), set([1, 3])), set([1, 2, 3]))

    def test_merge_var_table_if_requried(self):
        self.assertIsNone(merge_var_table_if_requried({}, {}))
        self.assertIsNone(merge_var_table_if_requried({'a': {1, 2}}, {'a': {1, 2}}))
        self.assertIsNone(merge_var_table_if_requried({'a': {1, 2}}, {'a': {1}}))
        self.assertDictEqual(merge_var_table_if_requried({'a': {1, 2}}, {'a': {3}}), {'a': {1, 2, 3}})
        self.assertDictEqual(merge_var_table_if_requried({}, {'b': {1}}), {'b': {1}})
        self.assertDictEqual(merge_var_table_if_requried({'a': {1}}, {'b': {1}}), {'a': {1}, 'b': {1}})

    def test_update_var_table(self):
        var_table = {"a": {1}}
        update_var_table(var_table, 'a', {2})
        self.assertDictEqual(var_table, {'a': {2}})

        update_var_table(var_table, 'b', {3})
        self.assertDictEqual(var_table, {'a': {2}, 'b': {3}})

        update_var_table(var_table, 'a', {})
        self.assertDictEqual(var_table, {'a': {}, 'b': {3}})

    def test_create_or_update_data_depependency_link(self):
        g = nx.DiGraph()
        create_or_update_data_depependency_link(g, 1, 2, "a")
        edge = g.get_edge_data(1, 2, None)
        self.assertIsNotNone(edge)
        self.assertTrue(edge['ddep'])
        self.assertSetEqual(edge['vars'], {'a'})

        create_or_update_data_depependency_link(g, 1, 2, "b")
        edge = g.get_edge_data(1, 2, None)
        self.assertSetEqual(edge['vars'], {'a', 'b'})

    # def test_mk_empty_cfg(self):
    #     cfg_empty = mk_empty_cfg()
    #     self.assertEqual(len(cfg_empty.entry_nodes()), 1)
    #     self.assertEqual(len(cfg_empty.exit_nodes()), 1)

    # def test_combine_two_empty(self):
    #     cfg_empty_1 = mk_empty_cfg()
    #     cfg_empty_2 = mk_empty_cfg()
    #     cfg_empty = combine(cfg_empty_1, cfg_empty_2)
    #     self.assertEqual(len(cfg_empty.entry_nodes()), 1)
    #     self.assertEqual(len(cfg_empty.exit_nodes()), 1)

    # def test_combine_adds_edge(self):
    #     cfg = CFG([1])
    #     cfg = combine(cfg, CFG([2]))
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([("A", "B")])
    #     ))

    # def test_combine_adds_edge_2(self):
    #     cfg_1 = CFG()
    #     node_1 = cfg_1.add_node([])
    #     node_2 = cfg_1.add_node([])
    #     node_3 = cfg_1.add_node([])
    #     cfg_1.add_edges_from([(node_1, node_3), (node_2, node_3)])

    #     cfg_2 = CFG()
    #     node_4 = cfg_2.add_node([])
    #     node_5 = cfg_2.add_node([])
    #     cfg_2.add_edges_from([(node_4, node_5)])

    #     cfg = combine(cfg_1, cfg_2, node_1, node_4)
    #     self.assertTrue(nx.algorithms.is_isomorphic(
    #         cfg,
    #         nx.DiGraph([("A", "C"), ("B", "C"), ("A", "D"), ("D", "E")])
    #     ))

    # def test_merge_keeps_names_and_ids(self):
    #     cfg_1 = CFG()
    #     cfg_1.add_node([1], "A", "ID-A")
    #     cfg_2 = CFG()
    #     cfg_1.add_node([2], "B", "ID-B")
    #     merge_cfg(cfg_1, cfg_2)
    #     self.assertIsNotNone(cfg_1.find_node_by_id('ID-A'))
    #     self.assertIsNotNone(cfg_1.find_node_by_id('ID-B'))
    #     self.assertIn('A', [name for _, name in cfg_1.nodes(data='name')])
    #     self.assertIn('B', [name for _, name in cfg_1.nodes(data='name')])

    # def test_remove_node(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([1])
    #     node_2 = cfg.add_node([2])
    #     node_3 = cfg.add_node([])
    #     node_4 = cfg.add_node([3])
    #     cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4)])
    #     remove_empty_node(cfg, node_3)
    #     self.assertTrue(
    #         nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "C"), ("B", "C")]))
    #     )

    # def test_reduce_redundant_exit_nodes_1(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([1])
    #     node_2 = cfg.add_node([2])
    #     node_3 = cfg.add_node([])
    #     node_4 = cfg.add_node([])
    #     cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4)])

    #     exit_nodes = find_redundant_exit_nodes(cfg)
    #     self.assertEqual(exit_nodes, [node_3])
    #     cfg = remove_empty_nodes(cfg, exit_nodes)

    #     self.assertTrue(
    #         nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "C"), ("B", "C")]))
    #     )

    # def test_reduce_redundant_exit_nodes_2(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([1])
    #     node_2 = cfg.add_node([])
    #     node_3 = cfg.add_node([2])
    #     cfg.add_edges_from([(node_1, node_2), (node_2, node_3)])
    #     exit_nodes = find_redundant_exit_nodes(cfg)
    #     self.assertEqual(exit_nodes, [node_2])
    #     cfg = remove_empty_nodes(cfg, exit_nodes)

    #     self.assertTrue(
    #         nx.algorithms.is_isomorphic(cfg, nx.DiGraph([("A", "B")]))
    #     )

    # def test_reduce_redundant_exit_nodes_abstain(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([1])
    #     node_2 = cfg.add_node([2])
    #     node_3 = cfg.add_node([])
    #     node_4 = cfg.add_node([3])
    #     node_5 = cfg.add_node([4])
    #     cfg.add_edges_from([(node_1, node_3), (node_2, node_3), (node_3, node_4), (node_3, node_5)])
    #     exit_nodes = find_redundant_exit_nodes(cfg)
    #     self.assertEqual(exit_nodes, [])

    # def test_reduce_redundant_exit_nodes_abstain_to_remove_entry_node(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([])
    #     node_2 = cfg.add_node([2])
    #     node_3 = cfg.add_node([3])
    #     node_4 = cfg.add_node([3])
    #     cfg.add_edges_from([(node_1, node_2), (node_2, node_3), (node_3, node_4), (node_4, node_2)])
    #     exit_nodes = find_redundant_exit_nodes(cfg)
    #     self.assertEqual(exit_nodes, [])

    # def test_reduce_redundant_exit_nodes_3(self):
    #     cfg = CFG()
    #     node_1 = cfg.add_node([1])
    #     node_2 = cfg.add_node([2])
    #     node_3 = cfg.add_node([])
    #     node_4 = cfg.add_node([])
    #     node_5 = cfg.add_node([3])
    #     node_6 = cfg.add_node([4])
    #     cfg.add_edges_from([
    #         (node_1, node_3),
    #         (node_2, node_3),
    #         (node_3, node_4),
    #         (node_4, node_5),
    #         (node_4, node_6),
    #     ])
    #     exit_nodes = find_redundant_exit_nodes(cfg)
    #     self.assertEqual(exit_nodes, [node_3, node_4])
    #     remove_empty_nodes(cfg, exit_nodes)
    #     self.assertTrue(
    #         nx.algorithms.is_isomorphic(
    #             cfg,
    #             nx.DiGraph([("A", "C"), ("B", "C"), ("C", "D"), ("C", "E")])
    #         )
    #     )


if __name__ == '__main__':
    main()
