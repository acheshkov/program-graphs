
from unittest import TestCase, main
from program_graphs.adg.adg import ADG
import networkx as nx  # type: ignore
# from program_graphs.cfg.types import JumpKind


class TestADGClass(TestCase):

    def test_adg_constructor(self) -> None:
        adg = ADG()
        self.assertIsNotNone(adg)
        self.assertIsInstance(adg, nx.DiGraph)
        node = adg.add_node('new_node')
        self.assertIsNotNone(node)


if __name__ == '__main__':
    main()
