import unittest

from propagation_sim.graph import edge_count, preferential_attachment, split_high_degree_nodes
from propagation_sim.simulation import simulate
from propagation_sim.delay_experiment import run as run_delay_experiment
from propagation_sim.time_aware import (
    quarantine_high_degree_nodes,
    simulate_with_intervention,
)


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

    def test_delayed_split_preserves_logical_population_denominator(self):
        graph = preferential_attachment(40, 2, 3)
        result = simulate_with_intervention(
            graph,
            [20],
            intervention="split",
            intervention_delay=2,
            transmission=0.0,
            recovery=0.0,
            steps=4,
            seed=9,
        )
        self.assertTrue(result["intervention_applied"])
        self.assertEqual(result["ever_infected"], 1)
        self.assertEqual(result["infected_fraction"], 1 / len(graph))

    def test_late_intervention_is_not_applied_after_simulation_ends(self):
        graph = preferential_attachment(30, 2, 5)
        result = simulate_with_intervention(
            graph,
            [12],
            intervention="split",
            intervention_delay=10,
            transmission=0.0,
            recovery=1.0,
            steps=4,
            seed=2,
        )
        self.assertFalse(result["intervention_applied"])

    def test_quarantine_removes_selected_hub_edges_symmetrically(self):
        graph = preferential_attachment(50, 2, 6)
        changed, selected = quarantine_high_degree_nodes(graph, count=2)
        for node in selected:
            self.assertEqual(changed[node], set())
            for neighbors in changed.values():
                self.assertNotIn(node, neighbors)

    def test_time_aware_simulation_is_reproducible(self):
        graph = preferential_attachment(50, 2, 10)
        kwargs = {
            "intervention": "rate_limit",
            "intervention_delay": 3,
            "seed": 14,
        }
        self.assertEqual(
            simulate_with_intervention(graph, [22], **kwargs),
            simulate_with_intervention(graph, [22], **kwargs),
        )

    def test_delay_experiment_reports_paired_uncertainty(self):
        result = run_delay_experiment(
            trials=5,
            nodes=30,
            delays=(0,),
            interventions=("split",),
            steps=5,
            seed=4,
        )
        comparison = result["comparisons"][0]
        interval = comparison["paired_difference"]["infected_fraction"][
            "approximate_95_percent_ci"
        ]
        self.assertEqual(len(interval), 2)
        self.assertLessEqual(interval[0], interval[1])


if __name__ == "__main__":
    unittest.main()
