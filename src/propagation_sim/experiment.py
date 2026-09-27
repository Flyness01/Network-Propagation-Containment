import argparse
import json
import statistics

from .graph import edge_count, preferential_attachment, split_high_degree_nodes
from .simulation import simulate


def summarize(values):
    return {"mean": statistics.mean(values), "stdev": statistics.stdev(values) if len(values) > 1 else 0.0}


def run(trials=100, nodes=120, hubs=3, replicas=3, transmission=0.16, recovery=0.20, seed=7):
    graph = preferential_attachment(nodes, 2, seed)
    intervention, mapping = split_high_degree_nodes(graph, hubs, replicas)
    protected = set(mapping)
    candidates = [node for node in graph if node not in protected]
    baseline_results, intervention_results = [], []
    for trial in range(trials):
        source = candidates[(trial * 37 + seed) % len(candidates)]
        baseline_results.append(simulate(graph, [source], transmission, recovery, seed=seed + trial))
        intervention_results.append(simulate(intervention, [source], transmission, recovery, seed=seed + trial))

    output = {
        "configuration": {"trials": trials, "nodes": nodes, "split_hubs": hubs, "replicas_per_hub": replicas, "transmission": transmission, "recovery": recovery, "seed": seed},
        "topology": {"baseline_nodes": len(graph), "intervention_nodes": len(intervention), "baseline_edges": edge_count(graph), "intervention_edges": edge_count(intervention), "split_nodes": sorted(protected)},
        "baseline": {metric: summarize([result[metric] for result in baseline_results]) for metric in ("ever_infected", "peak_infected", "duration")},
        "intervention": {metric: summarize([result[metric] for result in intervention_results]) for metric in ("ever_infected", "peak_infected", "duration")},
    }
    baseline = output["baseline"]["ever_infected"]["mean"]
    changed = output["intervention"]["ever_infected"]["mean"]
    output["relative_change_ever_infected_percent"] = 100 * (changed - baseline) / baseline
    output["baseline"]["infected_fraction"] = baseline / len(graph)
    output["intervention"]["infected_fraction"] = changed / len(intervention)
    output["relative_change_infected_fraction_percent"] = 100 * (
        output["intervention"]["infected_fraction"] - output["baseline"]["infected_fraction"]
    ) / output["baseline"]["infected_fraction"]
    return output


def main():
    parser = argparse.ArgumentParser(description="Compare baseline propagation with degree-based hub splitting.")
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--nodes", type=int, default=120)
    parser.add_argument("--hubs", type=int, default=3)
    parser.add_argument("--replicas", type=int, default=3)
    parser.add_argument("--transmission", type=float, default=0.16)
    parser.add_argument("--recovery", type=float, default=0.20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = run(args.trials, args.nodes, args.hubs, args.replicas, args.transmission, args.recovery, args.seed)
    rendered = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered + "\n")
    print(rendered)


if __name__ == "__main__":
    main()
