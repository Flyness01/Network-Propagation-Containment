import random


def simulate(graph, initial_infected, transmission=0.16, recovery=0.20, steps=40, seed=0):
    rng = random.Random(seed)
    susceptible = set(graph) - set(initial_infected)
    infected = set(initial_infected)
    recovered = set()
    ever_infected = set(infected)
    peak = len(infected)
    timeline = [len(infected)]

    for _ in range(steps):
        if not infected:
            break
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
        ever_infected |= new_infected
        peak = max(peak, len(infected))
        timeline.append(len(infected))

    return {"ever_infected": len(ever_infected), "peak_infected": peak, "duration": len(timeline) - 1, "timeline": timeline}
