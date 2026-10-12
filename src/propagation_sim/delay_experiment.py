"""Sweep intervention delay and compare containment mechanisms."""

import argparse
import json
import math
import statistics

from .graph import preferential_attachment
from .time_aware import simulate_with_intervention


def _summary(values):
    return {
        "mean": statistics.mean(values),
        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def _aggregate(results):
    metrics = ("ever_infected", "infected_fraction", "peak_infected", "duration")
    return {metric: _summary([result[metric] for result in results]) for metric in metrics}


def _paired_difference(changed, baseline, metric):
    differences = [
        changed_result[metric] - baseline_result[metric]
        for changed_result, baseline_result in zip(changed, baseline)
    ]
    mean = statistics.mean(differences)
    stdev = statistics.stdev(differences) if len(differences) > 1 else 0.0
    margin = 1.96 * stdev / math.sqrt(len(differences))
    return {
        "mean": mean,
        "stdev": stdev,
        "approximate_95_percent_ci": [mean - margin, mean + margin],
    }


def run(
    trials=200,
    nodes=120,
    delays=(0, 2, 4, 6, 8, 10, 12),
    interventions=("split", "quarantine", "rate_limit"),
    hubs=3,
    replicas=3,
    transmission=0.16,
    recovery=0.20,
    steps=40,
    seed=7,
):
    graph = preferential_attachment(nodes, 2, seed)
    protected = set(sorted(graph, key=lambda node: (-len(graph[node]), str(node)))[:hubs])
    candidates = [node for node in graph if node not in protected]
    baseline_trials = []
    trial_inputs = []
    for trial in range(trials):
        source = candidates[(trial * 37 + seed) % len(candidates)]
        trial_seed = seed + trial
        trial_inputs.append((source, trial_seed))
        baseline_trials.append(
            simulate_with_intervention(
                graph,
                [source],
                intervention="none",
                transmission=transmission,
                recovery=recovery,
                steps=steps,
                seed=trial_seed,
            )
        )

    baseline = _aggregate(baseline_trials)
    comparisons = []
    for intervention in interventions:
        for delay in delays:
            results = [
                simulate_with_intervention(
                    graph,
                    [source],
                    intervention=intervention,
                    intervention_delay=delay,
                    hubs=hubs,
                    replicas=replicas,
                    transmission=transmission,
                    recovery=recovery,
                    steps=steps,
                    seed=trial_seed,
                )
                for source, trial_seed in trial_inputs
            ]
            aggregate = _aggregate(results)
            baseline_fraction = baseline["infected_fraction"]["mean"]
            changed_fraction = aggregate["infected_fraction"]["mean"]
            comparisons.append(
                {
                    "intervention": intervention,
                    "delay_steps": delay,
                    "results": aggregate,
                    "relative_change_infected_fraction_percent": (
                        100 * (changed_fraction - baseline_fraction) / baseline_fraction
                    ),
                    "paired_difference": {
                        metric: _paired_difference(results, baseline_trials, metric)
                        for metric in ("infected_fraction", "peak_infected", "duration")
                    },
                    "intervention_application_rate": statistics.mean(
                        result["intervention_applied"] for result in results
                    ),
                    "mean_disrupted_edges": statistics.mean(
                        result["disrupted_edges"] for result in results
                    ),
                }
            )

    return {
        "question": (
            "How does intervention delay change the containment benefit of "
            "topology restructuring?"
        ),
        "configuration": {
            "trials": trials,
            "nodes": nodes,
            "delays": list(delays),
            "interventions": list(interventions),
            "split_hubs": hubs,
            "replicas_per_hub": replicas,
            "transmission": transmission,
            "recovery": recovery,
            "steps": steps,
            "seed": seed,
        },
        "measurement_note": (
            "Virtual replicas are counted as their original logical node. Delay "
            "is measured in simulation steps, not wall-clock controller time."
        ),
        "baseline": baseline,
        "comparisons": comparisons,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Measure how delayed topology interventions affect propagation."
    )
    parser.add_argument("--trials", type=int, default=200)
    parser.add_argument("--nodes", type=int, default=120)
    parser.add_argument("--delays", type=int, nargs="+", default=[0, 2, 4, 6, 8, 10, 12])
    parser.add_argument("--hubs", type=int, default=3)
    parser.add_argument("--replicas", type=int, default=3)
    parser.add_argument("--transmission", type=float, default=0.16)
    parser.add_argument("--recovery", type=float, default=0.20)
    parser.add_argument("--steps", type=int, default=40)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run(
        trials=args.trials,
        nodes=args.nodes,
        delays=tuple(args.delays),
        hubs=args.hubs,
        replicas=args.replicas,
        transmission=args.transmission,
        recovery=args.recovery,
        steps=args.steps,
        seed=args.seed,
    )
    rendered = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
