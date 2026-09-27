import unittest

from propagation_sim.graph import edge_count, preferential_attachment, split_high_degree_nodes
from propagation_sim.simulation import simulate


class PropagationTests(unittest.TestCase):
    def test_graph_is_undirected(self):
        graph = preferential_attachment(40, 2, 3)
        for node, neighbors in graph.items():
            for neighbor in neighbors:
                self.assertIn(node, graph[neighbor])

    def test_split_preserves_edge_count_and_reduces_max_degree(self):
        graph = preferential_attachment(80, 2, 4)
        changed, mapping = split_high_degree_nodes(graph, 3, 3)
        self.assertEqual(edge_count(graph), edge_count(changed))
        self.assertEqual(len(mapping), 3)
        self.assertLess(max(map(len, changed.values())), max(map(len, graph.values())))

    def test_zero_transmission_does_not_spread(self):
        graph = preferential_attachment(20, 2, 2)
        result = simulate(graph, [0], transmission=0.0, recovery=1.0, seed=1)
        self.assertEqual(result["ever_infected"], 1)

    def test_seeded_simulation_is_reproducible(self):
        graph = preferential_attachment(30, 2, 8)
        self.assertEqual(simulate(graph, [4], seed=12), simulate(graph, [4], seed=12))


if __name__ == "__main__":
    unittest.main()
