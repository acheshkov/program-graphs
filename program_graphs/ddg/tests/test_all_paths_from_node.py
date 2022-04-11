from unittest import TestCase, main
from program_graphs.cfg.fcfg import FCFG
from program_graphs.cfg.parser.java import parse
from program_graphs.cfg.fcfg import mk_fcfg_from_cfg
from program_graphs.ddg.parser.java.utils import all_paths_from
import networkx as nx  # type: ignore


class TestAllPathsFromNode(TestCase):

    def mk_fcfg(self, code: str) -> FCFG:
        cfg = parse(code)
        return mk_fcfg_from_cfg(cfg)

    def test_all_paths_from_single_node(self) -> None:
        g = nx.DiGraph()
        g.add_node(1)
        paths = all_paths_from(g, 1)
        self.assertEqual(paths, [])

    def test_all_paths_from_simple(self) -> None:
        g = nx.DiGraph([(1, 2), (2, 3)])
        paths = all_paths_from(g, 1)
        self.assertEqual(paths, [[1, 2, 3]])

    def test_all_paths_from_simple_branch(self) -> None:
        g = nx.DiGraph([(1, 2), (1, 3)])
        paths = all_paths_from(g, 1)
        self.assertEqual(paths, [[1, 2], [1, 3]])

    def test_all_paths_from_simple_loop(self) -> None:
        g = nx.DiGraph([(1, 2), (1, 3), (2, 1)])
        paths = all_paths_from(g, 1)
        self.assertEqual(paths, [[1, 2], [1, 3]])


if __name__ == '__main__':
    main()
