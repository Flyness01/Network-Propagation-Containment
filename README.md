# Network Propagation & Time-Bounded Containment

An ongoing systems research project asking whether a system can predict propagation risk, choose a structural intervention, and carry it out quickly enough to matter during an active malware outbreak.

This work grew from supervised undergraduate research that began with infectious-disease transmission and possible interventions. The investigation later moved toward computer-virus propagation, connecting mathematical models of spread with a systems question: **does a theoretically helpful intervention remain useful after prediction, coordination, and reconfiguration costs are included?**

This repository contains a safe, transparent simulation baseline. It does **not** create, execute, or analyze real malware.

## Research question

> Can a distributed system identify propagation risk and restructure its communication topology before malware spreads beyond the point where the intervention is useful?

The proposed research direction combines:

1. propagation prediction,
2. selection of highly connected or high-risk nodes,
3. a node-splitting intervention that redistributes their connections across virtual nodes, and
4. a controller capable of coordinating that change in a running network.

I proposed investigating a neural network trained with a Levenberg–Marquardt approach to predict propagation and guide the intervention. That learned predictor and a real Software-Defined Networking deployment remain under investigation; they are not presented here as completed components.

## Why this is a systems problem

Prediction accuracy alone is insufficient. A useful containment system must operate under a deadline while managing several costs:

- inference latency,
- controller decision latency,
- rule-installation delay,
- state migration and synchronization,
- communication and control-plane overhead,
- service disruption during restructuring, and
- the possibility that the network changes while the intervention is being computed.

The eventual evaluation therefore needs to measure the complete response path, not only the propagation model or classifier in isolation.

## Implemented baseline

Before adding a learned model, this repository isolates the proposed topology mechanism with an interpretable baseline:

- preferential-attachment network generation,
- seeded SIR-style propagation,
- degree centrality as a transparent hub-selection heuristic,
- virtual-node splitting that preserves edge count while changing topology,
- paired baseline/intervention trials using identical random seeds,
- JSON result export, and
- tests for graph invariants, reproducibility, and zero-transmission behavior.

Degree centrality is a heuristic, not AI. It provides a baseline against which a learned risk predictor can later be evaluated.

## Run

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m propagation_sim.experiment --trials 100 --output results/baseline.json
PYTHONPATH=src python3 -m propagation_sim.delay_experiment --trials 200 --output results/delay_sweep.json
```

## First controlled experiment

A 200-trial seeded comparison used a 120-node preferential-attachment graph, a transmission probability of 0.16, and a recovery probability of 0.20. The intervention split the three highest-degree nodes into three isolated virtual nodes each, preserving all 237 edges while increasing the representation to 126 nodes.

| Metric | Baseline | Node splitting |
| --- | ---: | ---: |
| Mean peak infection | 27.13 nodes | 21.49 nodes |
| Mean infected fraction | 53.33% | 50.92% |
| Mean duration | 25.47 steps | 27.07 steps |

The infected fraction changed by -4.50% relative to the baseline. Variance remained high, and the intervention changed the represented node count, so this is a baseline observation rather than evidence of a general containment effect.

## Time-aware containment experiment

The second experiment lets propagation run for a configurable number of steps before applying an intervention. It compares node splitting with quarantine and rate limiting. For split nodes, all virtual replicas are mapped back to the original logical node when outcomes are counted, so the result is not distorted by a larger represented population.

Across 200 paired trials:

| Intervention | Delay | Relative change in infected fraction | Mean disrupted edges |
| --- | ---: | ---: | ---: |
| Node splitting | 0 steps | -5.31% | 0 |
| Node splitting | 2 steps | -3.46% | 0 |
| Node splitting | 4 steps | +2.14% | 0 |
| Rate limiting | 0 steps | -42.33% | 56 |
| Rate limiting | 6 steps | -16.84% | 42.84 |
| Quarantine | 0 steps | -65.28% | 83 |
| Quarantine | 6 steps | -30.77% | 63.49 |

The paired mean change in infected fraction for immediate node splitting was -0.0283, with an approximate 95% confidence interval of [-0.0580, +0.0014]. The interval includes zero. Under this configuration, the evidence does not establish that splitting reduces total infection, and its small apparent benefit disappeared after a short delay.

Quarantine and rate limiting produced larger reductions whose paired intervals did not include zero in this sweep, but they removed many connections. That makes the systems trade-off visible: aggressive containment can reduce propagation while also imposing substantial disruption. The next model must attach traffic, availability, and reconfiguration costs to those removed or redistributed connections.

Delay is currently measured in simulation steps rather than wall-clock controller time. Runs in which propagation ended before the scheduled delay correctly record that no intervention was applied.

## Interpretation boundary

The current graph transformation models segmentation, not transparent virtualization. Virtual replicas are isolated from one another. The simulation does not yet include:

- predictor runtime,
- controller or rule-installation latency,
- state migration,
- traffic capacity,
- failures,
- application semantics, or
- disruption caused by reconfiguration.

Accordingly, these results show how the graph-level mechanism behaves under one controlled setup. They do not establish that a deployed SDN system could apply the intervention safely, cheaply, or in time.

## Systems evaluation plan

The next stage is organized around end-to-end usefulness:

1. Define the prediction target and compare any learned model with degree-based and non-learned baselines.
2. Measure prediction, controller-decision, rule-installation, and migration latency separately and end to end.
3. Sweep network size, density, transmission probability, recovery probability, workload skew, and intervention timing.
4. Compare node splitting with quarantine and rate limiting.
5. Report containment benefit together with coordination overhead and service disruption.
6. Determine the response-time threshold beyond which the intervention no longer improves the outcome.

## Research status

**Ongoing.** The safe simulator and paired baseline experiment are implemented. The Levenberg–Marquardt predictor, controller integration, and time-bounded end-to-end evaluation are research directions still being investigated.

## Author

Flyness Namatama
