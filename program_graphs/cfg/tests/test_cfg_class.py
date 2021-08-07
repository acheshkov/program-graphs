
from unittest import TestCase, main
from program_graphs import CFG
from program_graphs.cfg.types import JumpKind


class TestCFGClass(TestCase):

    def test_cfg_constructor(self):
        cfg = CFG()
        node_1 = cfg.add_node([None, None])
        node_2 = cfg.add_node([None])
        cfg.add_edge(node_1, node_2)
        self.assertEqual(list(cfg.nodes()), [node_1, node_2])
        self.assertTrue(cfg.exit_node, node_2)
        self.assertTrue(cfg.entry_node, node_1)

    def test_continue_nodes(self):
        cfg = CFG()
        cfg.add_continue_node(cfg.add_node([1]))
        cfg.add_continue_node(cfg.add_node([2]))
        self.assertEqual(len(cfg.continue_nodes), 2)
        cfg.remove_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.continue_nodes), 1)
        cfg.remove_continue_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.continue_nodes), 0)

    def test_break_nodes(self):
        cfg = CFG()
        cfg.add_break_node(cfg.add_node([1]))
        cfg.add_break_node(cfg.add_node([2]))
        self.assertEqual(len(cfg.break_nodes), 2)
        cfg.remove_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.break_nodes), 1)
        cfg.remove_break_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.break_nodes), 0)

    def test_return_nodes(self):
        cfg = CFG()
        cfg.add_return_node(cfg.add_node([1]))
        cfg.add_return_node(cfg.add_node([2]))
        self.assertEqual(len(cfg.return_nodes), 2)
        cfg.remove_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.return_nodes), 1)
        cfg.remove_return_node(list(cfg.nodes())[0])
        self.assertEqual(len(cfg.return_nodes), 0)

    def test_find_break_by_label(self):
        cfg = CFG()
        node_1, node_2 = cfg.add_node([1]), cfg.add_node([2])
        cfg.add_break_node(node_1, "A")
        cfg.add_break_node(node_2, "B")
        self.assertEqual(cfg.find_break_by_label("A"), [node_1])
        self.assertEqual(cfg.find_break_by_label("B"), [node_2])

    def test_remove_node(self):
        cfg = CFG()
        node_1 = cfg.add_node([1])
        cfg.add_break_node(node_1)
        cfg.add_continue_node(node_1)
        cfg.add_return_node(node_1)
        cfg.add_possible_jump(node_1, 'L', JumpKind.CONTINUE)

        self.assertEqual(len(cfg.nodes()), 1)
        self.assertEqual(len(cfg.break_nodes), 1)
        self.assertEqual(len(cfg.continue_nodes), 1)
        self.assertEqual(len(cfg.return_nodes), 1)
        self.assertEqual(len(cfg.possible_jumps), 1)

        cfg.remove_node(node_1)

        self.assertEqual(len(cfg.nodes()), 0)
        self.assertEqual(len(cfg.break_nodes), 0)
        self.assertEqual(len(cfg.continue_nodes), 0)
        self.assertEqual(len(cfg.return_nodes), 0)
        self.assertEqual(len(cfg.possible_jumps), 0)


if __name__ == '__main__':
    main()
