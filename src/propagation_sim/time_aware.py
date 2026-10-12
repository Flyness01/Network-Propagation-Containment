"""Time-aware propagation experiments with delayed topology interventions.

This module models *when* a controller acts, without claiming to implement an
SDN controller. A delay is expressed in simulation steps. At that step the
chosen graph transformation is applied and the SIR state is transferred to the
new topology.
"""

import random

from .graph import split_high_degree_nodes


def _selected_hubs(graph, count):
    return sorted(graph, key=lambda node: (-len(graph[node]), str(node)))[:count]


def quarantine_high_degree_nodes(graph, count=3):
    """Disconnect selected hubs while retaining the original node set."""
    selected = _selected_hubs(graph, count)
    changed = {node: set(neighbors) for node, neighbors in graph.items()}
    for node in selected:
        for neighbor in list(changed[node]):
            changed[neighbor].discard(node)
        changed[node].clear()
    return changed, selected


def rate_limit_high_degree_nodes(graph, count=3, keep_fraction=0.34):
    """Retain a deterministic fraction of each selected hub's connections."""
    if not 0.0 <= keep_fraction <= 1.0:
        raise ValueError("keep_fraction must be between 0 and 1")
    selected = _selected_hubs(graph, count)
    changed = {node: set(neighbors) for node, neighbors in graph.items()}
    for node in selected:
        neighbors = sorted(changed[node], key=str)
        keep = max(1, round(len(neighbors) * keep_fraction)) if neighbors else 0
        for neighbor in neighbors[keep:]:
            changed[node].discard(neighbor)
            changed[neighbor].discard(node)
    return changed, selected


def _advance(graph, susceptible, infected, recovered, transmission, recovery, rng):
    new_infected = set()
    new_recovered = set()
    for node in sorted(infected, key=str):
        for neighbor in sorted(graph[node], key=str):
            if neighbor in susceptible and rng.random() < transmission:
                new_infected.add(neighbor)
        if rng.random() < recovery:
            new_recovered.add(node)
    susceptible -= new_infected
    infected = (infected | new_infected) - new_recovered
    recovered |= new_recovered
    return susceptible, infected, recovered, new_infected


def _transfer_split_state(compartment, mapping):
    transferred = set(compartment)
    for original, replicas in mapping.items():
        if original in transferred:
            transferred.remove(original)
            transferred.update(replicas)
    return transferred


def _logical_nodes(nodes, reverse_mapping):
    return {reverse_mapping.get(node, node) for node in nodes}


def simulate_with_intervention(
    graph,
    initial_infected,
    intervention="none",
    intervention_delay=0,
    hubs=3,
    replicas=3,
    transmission=0.16,
    recovery=0.20,
    steps=40,
    seed=0,
):
    """Run SIR propagation and apply a topology intervention after a delay.

    Node-splitting replicas are counted as one original logical node. This
    prevents the intervention from appearing better or worse merely because it
    changes the represented node count.
    """
    if intervention not in {"none", "split", "quarantine", "rate_limit"}:
        raise ValueError(f"unknown intervention: {intervention}")
    if intervention_delay < 0:
        raise ValueError("intervention_delay must be non-negative")

    rng = random.Random(seed)
    active_graph = {node: set(neighbors) for node, neighbors in graph.items()}
    susceptible = set(active_graph) - set(initial_infected)
    infected = set(initial_infected)
    recovered = set()
    reverse_mapping = {}
    ever_logical = set(initial_infected)
    peak_logical = len(_logical_nodes(infected, reverse_mapping))
    timeline = [peak_logical]
    applied = False
    disrupted_edges = 0

    for step in range(steps):
        if not applied and intervention != "none" and step == intervention_delay:
            edges_before = sum(map(len, active_graph.values())) // 2
            if intervention == "split":
                active_graph, mapping = split_high_degree_nodes(active_graph, hubs, replicas)
                susceptible = _transfer_split_state(susceptible, mapping)
                infected = _transfer_split_state(infected, mapping)
                recovered = _transfer_split_state(recovered, mapping)
                reverse_mapping = {
                    replica: original
                    for original, replica_nodes in mapping.items()
                    for replica in replica_nodes
                }
            elif intervention == "quarantine":
                active_graph, _ = quarantine_high_degree_nodes(active_graph, hubs)
            else:
                active_graph, _ = rate_limit_high_degree_nodes(active_graph, hubs)
            edges_after = sum(map(len, active_graph.values())) // 2
            disrupted_edges = edges_before - edges_after
            applied = True

        if not infected:
            break
        susceptible, infected, recovered, new_infected = _advance(
            active_graph,
            susceptible,
            infected,
            recovered,
            transmission,
            recovery,
            rng,
        )
        ever_logical.update(_logical_nodes(new_infected, reverse_mapping))
        logical_infected = len(_logical_nodes(infected, reverse_mapping))
        peak_logical = max(peak_logical, logical_infected)
        timeline.append(logical_infected)

    return {
        "ever_infected": len(ever_logical),
        "infected_fraction": len(ever_logical) / len(graph),
        "peak_infected": peak_logical,
        "duration": len(timeline) - 1,
        "timeline": timeline,
        "intervention_applied": applied,
        "intervention_delay": intervention_delay,
        "disrupted_edges": disrupted_edges,
    }
