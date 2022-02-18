
from unittest import TestCase, main
from program_graphs.adg.adg import ADG
import networkx as nx
# from program_graphs.cfg.types import JumpKind


class TestADGClass(TestCase):

    def test_adg_constructor(self):
        adg = ADG()
        self.assertIsNotNone(adg)
        self.assertIsInstance(adg, nx.DiGraph)
        node = adg.add_node('new_node')
        self.assertIsNotNone(node)


if __name__ == '__main__':
    main()
