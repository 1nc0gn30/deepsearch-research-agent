# DeepSearch Research Methodology & Synthesis Engine

This document provides a formal architectural and algorithmic specification of the **DeepSearch Autonomous Research Engine**. DeepSearch is engineered to replicate and exceed human research workflows across five iterative stages: Scoping & Query Decomposition, Adaptive Evidence Harvesting, Domain Credibility Calibration, Dialectical Consensus Resolution, and Multi-Perspective Grounded Synthesis.

```
+----------------------------------------------------------------------------------------------------+
|                             5-STAGE DEEP RESEARCH PIPELINE ARCHITECTURE                            |
+----------------------------------------------------------------------------------------------------+

  [ User Research Question ]
              |
              v
   +----------------------+
   | Stage 1: Scoping     |  --> Recursive Query Tree Decomposition (DAG)
   | & Decomposition      |  --> Angle Generation (Technical, Economic, Regulatory, Scientific)
   +----------+-----------+
              |
              v
   +----------------------+
   | Stage 2: Adaptive    |  --> Multi-Engine Search (`site:`, `filetype:pdf`, boolean filters)
   | Evidence Harvesting  |  --> Parallel Content Scraping & Text Chunking
   +----------+-----------+
              |
              v
   +----------------------+
   | Stage 3: Source      |  --> Domain Authority Scoring ($\alpha_{cred} \in [0, 100]$)
   | Credibility & Bias   |  --> Primary Source Verification & Recency Decay
   +----------+-----------+
              |
              v
   +----------------------+
   | Stage 4: Consensus & |  --> Cross-Reference Matrix Construction
   | Contradiction Resol. |  --> Dialectical Debate & Contra-Evidence Extraction
   +----------+-----------+
              |
              v
   +----------------------+
   | Stage 5: Grounded    |  --> Citation Graph Construction & In-Text Linking
   | Synthesis & Review   |  --> Calibrated Confidence Scoring ($C_{comp}$)
   +----------+-----------+
              |
              v
  [ Peer-Reviewed Research Paper / HTML Artifact / Machine Data Bundle ]
```

---

## 1. Stage 1: Recursive Query Decomposition & DAG Generation

When a complex research question $Q_0$ is submitted, single-hop search engines suffer from catastrophic tunnel vision. DeepSearch decomposes $Q_0$ into a Directed Acyclic Graph (DAG) of specialized sub-queries $\mathcal{T} = \{q_{i,j}\}$, where $i$ represents depth level and $j$ represents investigative angle.

### Decomposition Strategy
1. **Root Scoping**: Identifies core entities $E$, temporal boundaries $T$, and empirical metrics $M$.
2. **Angle Orthogonalization**: Generates distinct investigative branches:
   - **Architectural / Mechanistic**: How does the underlying system function?
   - **Empirical Benchmarks**: What quantitative metrics have been measured?
   - **Contested Hypotheses**: Where do domain authorities disagree?
   - **Upstream & Downstream Dependencies**: What are the supply chain, regulatory, or hardware prerequisites?

---

## 2. Stage 2: Adaptive Evidence Harvesting & Search Operators

DeepSearch converts sub-questions into search operator strings optimized across web indexes and academic repositories:

```
Search Operator Matrix:
  Academic Preprints:    site:arxiv.org OR site:nature.com OR site:science.org "query" filetype:pdf
  Government & Standards: site:gov OR site:nist.gov OR site:europa.eu intitle:"specification"
  Financial & 10-K:      site:sec.gov/edgar OR site:bloomberg.com "annual report" "TAM"
  Code & Implementations: site:github.com OR site:huggingface.co "reproducible benchmark"
```

Content extraction executes in parallel worker pools with rate-limiting, markdown cleaning, HTML boilerplate stripping, and citation footprint preservation.

---

## 3. Stage 3: Domain Authority & Credibility Scoring

Every harvested document $D_k$ receives a composite Credibility Coefficient $\alpha_{cred}(D_k) \in [0.0, 1.0]$:

$$\alpha_{cred}(D_k) = w_{auth} \cdot A(dom) + w_{peer} \cdot P(D_k) + w_{rec} \cdot R(\Delta t) - w_{bias} \cdot B(D_k)$$

Where:
- $A(dom)$: Domain Authority score (0.0 to 1.0) based on historical peer review and institutional trust (e.g., `nature.com` $= 0.98$, `nih.gov` $= 0.96$, personal blog $= 0.35$).
- $P(D_k)$: Peer-Review / Official standard indicator ($1.0$ if peer-reviewed journal or government standard, $0.5$ if corporate whitepaper, $0.2$ if unverified social post).
- $R(\Delta t)$: Recency decay factor: $R(\Delta t) = e^{-\lambda \Delta t}$, where $\lambda$ is tuned based on topic volatility (higher decay for rapid AI benchmarks, lower for fundamental mathematics).
- $B(D_k)$: Commercial or promotional bias penalty.

---

## 4. Stage 4: Dialectical Consensus & Contradiction Resolution

To eliminate confirmation bias, DeepSearch evaluates each extracted empirical claim $c_m$ across all sources.

```
                  +-----------------------+
                  | Harvested Claim: c_m  |
                  +-----------+-----------+
                              |
             +----------------+----------------+
             |                                 |
             v                                 v
   [ Corroborating Evidence ]         [ Contradicting Evidence ]
   Sources: S_1, S_2, S_3             Sources: S_4, S_5
   Weighted Sum: W_pos = \sum \alpha_i Weighted Sum: W_neg = \sum \alpha_j
             |                                 |
             +----------------+----------------+
                              |
                              v
                  +-----------+-----------+
                  | Consensus Resolution  |
                  | Agreement Ratio:      |
                  | R = W_pos / (W_pos + W_neg)
                  +-----------------------+
```

### Consensus Categorization:
- **Strong Consensus ($R \ge 0.90$, $W_{pos} \ge 2.5$)**: Claim is treated as verified fact with primary citations.
- **Moderate Consensus ($0.70 \le R < 0.90$)**: Claim is reported with caveats noting minority viewpoints.
- **Contested / Ambiguous ($0.35 \le R < 0.70$)**: Claim is explicitly presented as a contested hypothesis with balanced evidence from both sides.
- **Refuted ($R < 0.35$)**: Claim is identified as debunked or obsolete.

---

## 5. Stage 5: Multi-Perspective Synthesis & Calibrated Grounding

The final report is generated by a synthesis model constrained by strict citation grounding rules:
1. **Zero Unreferenced Claims**: Every empirical figure, date, and benchmark must carry an explicit bracketed citation link `[Source N]` mapped to the harvested source repository.
2. **Confidence Calibration Math**:
   The overall report confidence score $C_{comp}$ is computed as:

   $$C_{comp} = \frac{1}{|\mathcal{C}|} \sum_{c \in \mathcal{C}} \left( \min(1.0, \sum_{s \in S(c)} \alpha_{cred}(s)) \times (1 - \delta_{contested}(c)) \right)$$

   Where $\mathcal{C}$ is the set of verified claims, $S(c)$ is the supporting source cluster for claim $c$, and $\delta_{contested} \in [0, 0.5]$ applies a penalty if contradictory claims remain unresolved.

---

## 6. Anti-Hallucination & Verification Guardrails

| Risk Vector | Algorithmic Guardrail | Mitigation Mechanism |
| :--- | :--- | :--- |
| **Fabricated Citations** | Cryptographic URL Verification | URLs are verified during crawl; non-resolvable links or mismatched title strings are pruned. |
| **Statistical Drift** | Double-Check Numerical Matcher | Numerical regex matchers verify that numbers cited in text match raw document context. |
| **Echo Chambers** | Domain Diversity Constraint | No single domain may contribute $>25\%$ of total citations in a report. |
| **Stale Benchmarks** | Temporal Timestamp Enforcer | Sources older than the user-specified cutoff are tagged with warning indicators. |
