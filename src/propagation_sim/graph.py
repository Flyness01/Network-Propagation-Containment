import random


def add_edge(graph, left, right):
    if left == right:
        return
    graph.setdefault(left, set()).add(right)
    graph.setdefault(right, set()).add(left)


def preferential_attachment(node_count=120, edges_per_node=2, seed=7):
    if node_count < 3 or edges_per_node < 1:
        raise ValueError("node_count must be >= 3 and edges_per_node >= 1")
    rng = random.Random(seed)
    graph = {0: set(), 1: set(), 2: set()}
    add_edge(graph, 0, 1)
    add_edge(graph, 1, 2)
    add_edge(graph, 2, 0)
    for node in range(3, node_count):
        graph[node] = set()
        candidates = list(range(node))
        weights = [max(1, len(graph[candidate])) for candidate in candidates]
        targets = set()
        while len(targets) < min(edges_per_node, len(candidates)):
            targets.add(rng.choices(candidates, weights=weights, k=1)[0])
        for target in targets:
            add_edge(graph, node, target)
    return graph


def edge_count(graph):
    return sum(len(neighbors) for neighbors in graph.values()) // 2


def split_high_degree_nodes(graph, count=3, replicas=3):
    """Split selected hubs and distribute their incident edges across replicas.

    Replicas are intentionally not linked to one another. This represents an
    SDN-style segmentation assumption, not transparent server replication.
    """
    if replicas < 2:
        raise ValueError("replicas must be >= 2")
    result = {node: set(neighbors) for node, neighbors in graph.items()}
    selected = sorted(result, key=lambda node: (-len(result[node]), str(node)))[:count]
    mapping = {}
    for node in selected:
        neighbors = sorted(result[node], key=str)
        for neighbor in neighbors:
            result[neighbor].discard(node)
        del result[node]
        virtual_nodes = [f"{node}v{index}" for index in range(replicas)]
        mapping[node] = virtual_nodes
        for virtual in virtual_nodes:
            result[virtual] = set()
        for index, neighbor in enumerate(neighbors):
            add_edge(result, virtual_nodes[index % replicas], neighbor)
    return result, mapping
