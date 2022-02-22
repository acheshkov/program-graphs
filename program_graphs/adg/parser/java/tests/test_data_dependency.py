
from unittest import TestCase, main
from program_graphs.adg.parser.java.data_dependency import set_diff, merge_var_table_if_requried, update_var_table
from program_graphs.adg.parser.java.data_dependency import create_or_update_data_depependency_link
import networkx as nx  # type: ignore


class TestDataDependency(TestCase):

    def test_set_diff(self) -> None:
        self.assertIsNone(set_diff(set([]), set([])))  # type: ignore
        self.assertIsNone(set_diff(set([1]), set([])))  # type: ignore
        self.assertSetEqual(set_diff(set([]), set([1])), set([1]))  # type: ignore
        self.assertSetEqual(set_diff(set([1, 2]), set([1, 3])), set([1, 2, 3]))  # type: ignore

    def test_merge_var_table_if_requried(self) -> None:
        self.assertIsNone(merge_var_table_if_requried({}, {}))  # type: ignore
        self.assertIsNone(merge_var_table_if_requried({'a': {1, 2}}, {'a': {1, 2}}))  # type: ignore
        self.assertIsNone(merge_var_table_if_requried({'a': {1, 2}}, {'a': {1}}))  # type: ignore
        self.assertDictEqual(merge_var_table_if_requried({'a': {1, 2}}, {'a': {3}}), {'a': {1, 2, 3}})  # type: ignore
        self.assertDictEqual(merge_var_table_if_requried({}, {'b': {1}}), {'b': {1}})  # type: ignore
        self.assertDictEqual(merge_var_table_if_requried({'a': {1}}, {'b': {1}}), {'a': {1}, 'b': {1}})  # type: ignore

    def test_update_var_table(self) -> None:
        var_table = {"a": {1}}
        update_var_table(var_table, 'a', {2})
        self.assertDictEqual(var_table, {'a': {2}})

        update_var_table(var_table, 'b', {3})
        self.assertDictEqual(var_table, {'a': {2}, 'b': {3}})

    def test_create_or_update_data_depependency_link(self) -> None:
        g = nx.DiGraph()
        create_or_update_data_depependency_link(g, 1, 2, "a")
        edge = g.get_edge_data(1, 2, None)
        self.assertIsNotNone(edge)
        self.assertTrue(edge['ddep'])
        self.assertSetEqual(edge['vars'], {'a'})

        create_or_update_data_depependency_link(g, 1, 2, "b")
        edge = g.get_edge_data(1, 2, None)
        self.assertSetEqual(edge['vars'], {'a', 'b'})


if __name__ == '__main__':
    main()
