
from unittest import TestCase, main
import networkx as nx  # type: ignore
from program_graphs import CFG
from program_graphs.cfg.fcfg import mk_fcfg_from_cfg


class TestFCFGMaker(TestCase):

    def test_fcfg_make_empty(self):
        cfg = CFG()
        fcfg = mk_fcfg_from_cfg(cfg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            fcfg, nx.DiGraph([])
        ))

    def test_fcfg_make_single_block(self):
        cfg = CFG()
        cfg.add_node([None, None])
        fcfg = mk_fcfg_from_cfg(cfg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            fcfg, nx.DiGraph([
                (1, 2)
            ])
        ))

    def test_fcfg_make_simple_branch(self):
        cfg = CFG()
        bb_1 = cfg.add_node([None])
        bb_2 = cfg.add_node([None])
        bb_3 = cfg.add_node([None])
        cfg.add_edges_from([(bb_1, bb_2), (bb_1, bb_3)])
        fcfg = mk_fcfg_from_cfg(cfg)
        self.assertTrue(nx.algorithms.is_isomorphic(
            fcfg, nx.DiGraph([
                ("b1", "b2"),
                ("b1", "b3")
            ])
        ))

    def test_fcfg_make_simple_loop(self):
        cfg = CFG()
        start = cfg.add_node([])
        bb_1 = cfg.add_node([None])
        bb_2 = cfg.add_node([None])
        bb_3 = cfg.add_node([None])
        bb_4 = cfg.add_node([None])
        cfg.add_edges_from([(start, bb_1), (bb_1, bb_2), (bb_2, bb_3), (bb_1, bb_4), (bb_3, bb_1)])
        fcfg = mk_fcfg_from_cfg(cfg)
        print(nx.get_edge_attributes(fcfg, 'flow'))
        self.assertTrue(nx.algorithms.is_isomorphic(
            fcfg, nx.DiGraph([
                ("start", "b1"),
                ("b1", "b2"),
                ("b1", "b4"),
                ("b1", "b2"),
                ("b2", "b3"),
                ("b3", "b1"),
            ])
        ))

    def test_fcfg_make_stmt_attribute(self):
        cfg = CFG()
        cfg.add_node(["stmt1", "stmt2"])
        fcfg = mk_fcfg_from_cfg(cfg)

        self.assertEqual(
            nx.get_node_attributes(fcfg, 'statement'),
            {0: "stmt1", 1: "stmt2"}
        )


if __name__ == '__main__':
    main()
