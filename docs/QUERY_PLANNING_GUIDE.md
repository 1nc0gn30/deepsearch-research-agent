# Autonomous Query Planning & Tree-of-Thought Decomposition Guide

This guide details the internal mechanics of the **DeepSearch Autonomous Query Planner**, responsible for translating high-level, ambiguous human research queries into precise, multi-branch information retrieval graphs.

---

## 1. The Tree-of-Thought (ToT) Query Decomposition Strategy

Standard search workflows perform naive string matching. Complex questions (e.g. *"What are the trade-offs between neutral atom and superconducting architectures for fault-tolerant quantum computing in 2026?"*) require hierarchical multi-dimensional exploration.

```
                     [ Root Research Goal ]
                                |
       +------------------------+------------------------+
       |                                                 |
[ Branch A: Superconducting ]                  [ Branch B: Neutral Atoms ]
       |                                                 |
  +----+----+                                       +----+----+
  |         |                                       |         |
[ A1: T1 ] [ A2: Gate Errors ]                 [ B1: Tweezer ] [ B2: Coherence ]
```

### The 4 Core Decomposition Angles:
1. **Architectural & Theoretical Foundations**: Fundamental physical, mathematical, or algorithmic principles.
2. **Empirical Benchmarks & Experimental Results**: Measured laboratory or production performance numbers.
3. **Contradictions & Open Questions**: Divergent claims, unverified assumptions, scaling limits.
4. **Economic, Supply Chain & Ecosystem Implications**: Fabrication costs, hardware requirements, market adoption.

---

## 2. Advanced Search Operator Engineering

The Query Planner automatically constructs Google- and Bing-compatible Boolean queries tailored to the target domain:

### Academic & Scientific Papers
```text
(site:arxiv.org OR site:nature.com OR site:science.org OR site:aps.org) AND ("fault tolerant" OR "quantum error correction") AND ("surface code" OR "qLDPC") AND filetype:pdf
```

### Official Regulatory & Government Standards
```text
(site:gov OR site:nist.gov OR site:europa.eu) AND intitle:("standard" OR "framework" OR "guidance") AND ("autonomous agent" OR "risk management")
```

### Financial & Market Data
```text
(site:sec.gov/edgar OR site:bloomberg.com OR site:reuters.com) AND ("TAM" OR "CAGR" OR "market size" OR "10-K") AND ("AI agents" OR "enterprise automation")
```

### Code Repositories & Implementations
```text
site:github.com ("implementation" OR "benchmark" OR "reproducibility") AND ("transversal gates" OR "magic state distillation")
```

---

## 3. Recursive Branching & Dynamic Beam Pruning

During multi-stage execution, not every query branch yields fruitful evidence. DeepSearch applies **Dynamic Beam Pruning** to prevent exponential explosion:

```
[ Stage N Queries Executed ]
             |
             v
   [ Evidence Evaluation ]
             |
   +---------+---------+
   | Score >= Threshold| ---> [ Generate Sub-Queries for Stage N+1 ]
   | (High Information |
   |  Gain > 0.65)     |
   +-------------------+
   | Score < Threshold | ---> [ Prune Branch from Tree ]
   | (Redundant / Low  |
   |  Relevance)       |
   +-------------------+
```

### Information Gain Metric ($IG$):
$$IG(q) = H(Context) - H(Context \mid D_q) - \lambda_{redundancy} \cdot Sim(D_q, \mathcal{D}_{harvested})$$

Where:
- $H(Context)$ is the entropy (information gap) of the current knowledge state.
- $Sim(D_q, \mathcal{D}_{harvested})$ measures cosine similarity against previously collected documents to prevent circular research loops.

---

## 4. Query Planning API Example

### Python Programmatic Usage
```python
from deepsearch_research_agent.planner import AutonomousQueryPlanner

planner = AutonomousQueryPlanner(max_depth=3, max_breadth=4)

query_tree = planner.generate_plan(
    topic="CRISPR-Cas12 vs Cas9 Off-Target Editing Rates",
    angles=["biochemical mechanism", "in vivo clinical trials", "delivery vectors"],
)

print(query_tree.to_json(indent=2))
```

### Output JSON Representation
```json
{
  "root_topic": "CRISPR-Cas12 vs Cas9 Off-Target Editing Rates",
  "total_planned_queries": 9,
  "nodes": [
    {
      "node_id": "q1_mech",
      "angle": "biochemical mechanism",
      "search_string": "(site:nature.com OR site:cell.com) CRISPR Cas12a vs Cas9 PAM recognition off-target cleavage specificity filetype:pdf",
      "priority": 1.0
    },
    {
      "node_id": "q2_clinical",
      "angle": "in vivo clinical trials",
      "search_string": "site:clinicaltrials.gov (\"Cas12\" OR \"Cas9\") off-target sequencing GUIDE-seq DISCOVER-seq",
      "priority": 0.95
    }
  ]
}
```
