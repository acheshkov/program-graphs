
from unittest import TestCase, main
from program_graphs import CFG
from program_graphs.cfg.edge_contraction import is_possible_to_contract, edge_contraction_all
import networkx as nx  # type: ignore


class TestCFGEdgeContraction(TestCase):

    def test_is_contraction_possible_linear(self) -> None:
        cfg = CFG()
        cfg.add_edges_from([
            (1, 2), (2, 3)
        ])
        self.assertTrue(is_possible_to_contract(cfg, (1, 2)))
        self.assertTrue(is_possible_to_contract(cfg, (2, 3)))

    def test_is_contraction_possible_simple_cycle(self) -> None:
        cfg = CFG()
        cfg.add_edges_from([
            (1, 2), (2, 3), (3, 4), (3, 2)
        ])
        self.assertFalse(is_possible_to_contract(cfg, (1, 2)))
        self.assertTrue(is_possible_to_contract(cfg, (2, 3)))
        self.assertFalse(is_possible_to_contract(cfg, (3, 4)))
        self.assertFalse(is_possible_to_contract(cfg, (3, 2)))

    def test_is_contraction_possible_two_nested_cycles(self) -> None:
        cfg = CFG()
        cfg.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (3, 3), (4, 2)
        ])
        self.assertFalse(is_possible_to_contract(cfg, (3, 3)))
        self.assertFalse(is_possible_to_contract(cfg, (4, 2)))
        self.assertFalse(is_possible_to_contract(cfg, (1, 2)))
        self.assertFalse(is_possible_to_contract(cfg, (2, 3)))
        self.assertFalse(is_possible_to_contract(cfg, (3, 4)))
        self.assertFalse(is_possible_to_contract(cfg, (4, 5)))

    def test_is_contraction_possible_two_nested_cycles_2(self) -> None:
        cfg = CFG()
        cfg.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 5),
            (3, 2), (4, 2)
        ])
        self.assertTrue(is_possible_to_contract(cfg, (2, 3)))

    def test_is_contraction_possible_another_cycle(self) -> None:
        cfg = CFG()
        cfg.add_edges_from([
            (1, 2), (2, 3), (3, 4), (4, 2), (2, 5)
        ])
        self.assertTrue(is_possible_to_contract(cfg, (3, 4)))
        self.assertFalse(is_possible_to_contract(cfg, (2, 3)))

    def test_is_contraction_possible_return_left(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_return_node(node_1)
        self.assertFalse(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_is_contraction_possible_return_right(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_return_node(node_2)
        self.assertTrue(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_is_contraction_possible_break_node_left(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_break_node(node_1)
        self.assertFalse(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_is_contraction_possible_break_node_right(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_break_node(node_2)
        self.assertTrue(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_is_contraction_possible_continue_node_left(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_continue_node(node_1)
        self.assertFalse(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_is_contraction_possible_continue_node_right(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([(node_1, node_2)])
        cfg.add_continue_node(node_2)
        self.assertTrue(is_possible_to_contract(cfg, (node_1, node_2)))

    def test_edge_contraction_case_1(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([3])
        node_4 = cfg.add_node([4])
        cfg.add_edges_from([(node_1, node_2), (node_2, node_3), (node_3, node_4)])
        cfg = edge_contraction_all(cfg)
        self.assertEqual(len(cfg.nodes()), 1)

    def test_edge_contraction_case_cycle_of_length_one(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([3])
        node_4 = cfg.add_node([4])
        cfg.add_edges_from([(node_1, node_2), (node_2, node_3), (node_3, node_4), (node_3, node_2)])
        cfg = edge_contraction_all(cfg)
        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([(1, 2), (2, 3), (2, 2)]))
        )
    
    def test_edge_contraction_case_cycle_of_length_two(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        node_3 = cfg.add_node([3])
        node_4 = cfg.add_node([4])
        node_5 = cfg.add_node([5])
        cfg.add_edges_from([(node_1, node_2), (node_2, node_3), (node_3, node_4), (node_4, node_5), (node_4, node_2)])
        cfg = edge_contraction_all(cfg)
        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([(1, 2), (2, 3), (2, 2)]))
        )

    def test_edge_contraction_case_2(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([])
        node_2 = cfg.add_node([])
        node_3 = cfg.add_node([])
        node_4 = cfg.add_node([])
        node_5 = cfg.add_node([])
        node_6 = cfg.add_node([])
        cfg.add_edges_from([
            (node_1, node_2),
            (node_2, node_3),
            (node_3, node_4),
            (node_4, node_5),
            (node_3, node_6),
            (node_5, node_6)
        ])
        cfg = edge_contraction_all(cfg)
        self.assertTrue(
            nx.algorithms.is_isomorphic(cfg, nx.DiGraph([(1, 3), (1, 2), (2, 3)]))
        )

    def test_edge_contraction_name_assignment_left(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([], name='A')
        node_2 = cfg.add_node([])
        cfg.add_edges_from([(node_1, node_2)])
        cfg = edge_contraction_all(cfg)
        self.assertIsNotNone(cfg.find_node_by_name('A'))

    def test_edge_contraction_name_assignment_right(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([])
        node_2 = cfg.add_node([], name='B')
        cfg.add_edges_from([(node_1, node_2)])
        cfg = edge_contraction_all(cfg)
        self.assertIsNotNone(cfg.find_node_by_name('B'))

    def test_edge_contraction_name_assignment_both(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([], name='A')
        node_2 = cfg.add_node([], name='B')
        cfg.add_edges_from([(node_1, node_2)])
        cfg = edge_contraction_all(cfg)
        self.assertIsNotNone(cfg.find_node_by_name('B'))

    def test_blocks_merging(self) -> None:
        cfg = CFG()
        node_1 = cfg.add_node([1])
        node_2 = cfg.add_node([2])
        cfg.add_edges_from([
            (node_1, node_2)
        ])
        cfg = edge_contraction_all(cfg)
        self.assertIn([1, 2], cfg.node_id_2_block)


if __name__ == '__main__':
    main()
