# Network Propagation & Topology-Based Containment

A safe simulation project for studying how communication structure affects malware-like propagation in a distributed network.

The original research question asked whether predicted high-risk nodes and Software-Defined Networking could be combined to respond to propagation by splitting highly connected nodes into parallel virtual nodes. This repository implements a transparent first baseline: degree centrality stands in for a learned risk model, and a graph transformation redistributes a hub's edges across isolated virtual nodes.

It does **not** create, execute, or analyze real malware.

## Systems framing

This project sits within my interest in distributed systems: it asks how communication topology and a controller's coordination decisions change system-wide behavior. The virtual-node intervention also raises a familiar question from parallel systems: does creating more independently managed paths improve resilience enough to justify added control, migration, and synchronization cost?

## What is implemented

- Preferential-attachment network generator
- Seeded SIR-style propagation simulation
- Degree-based hub selection
- Virtual-node splitting that preserves edge count while changing topology
- Paired baseline/intervention trials using the same random seeds
- JSON result export
- Unit tests for graph invariants, reproducibility, and zero-transmission behavior

## Run

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m propagation_sim.experiment --trials 100 --output results/baseline.json
```

## Interpretation boundary

Virtual replicas are not connected to one another in this model. That is an explicit segmentation assumption, not transparent virtualization. The experiment tests a graph-level mechanism; it does not show that a real SDN controller can deploy it safely or cheaply.

Degree centrality is also a heuristic, not AI. A learned predictor would require labeled temporal data, a defined prediction target, train/test separation, and comparison against simple baselines like this one.

## First controlled run

A 200-trial seeded comparison used a 120-node preferential-attachment graph, a transmission probability of 0.16, and a recovery probability of 0.20. Splitting the three highest-degree nodes into three isolated virtual nodes preserved all 237 edges while increasing the representation to 126 nodes.

- Mean peak infection fell from 27.13 to 21.49 nodes.
- Mean infected fraction fell from 53.33% to 50.92%, a relative change of -4.50%.
- Mean duration rose from 25.47 to 27.07 steps.
- Variance remained high, so this is a baseline observation rather than a general containment claim.

Raw infected counts are not directly comparable after node splitting because the intervention changes the number of represented nodes. The analysis therefore reports both counts and fractions.

## Questions to test next

1. Does the effect persist across network sizes, densities, and transmission rates?
2. How does splitting compare with quarantine or rate limiting?
3. What happens under skewed traffic and community structure?
4. What control-plane latency and migration cost would an SDN implementation add?
5. Can a learned risk score outperform degree without leaking future information?

## Author

Flyness Namatama
