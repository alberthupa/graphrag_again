# Ontology RAG Experiments – Draft

## Table of Contents

1. [Introduction](#1-introduction)
2. [Database selection](#2-database-selection)
3. [Objectives and success criteria](#3-objectives-and-success-criteria)
4. [Requirements](#4-requirements)
    4.1 [Data layer](#41-data-layer)
    4.2 [Ontology layer](#42-ontology-layer)
    4.3 [LLM agent stack](#43-llm-agent-stack)
    4.4 [Evaluation harness](#44-evaluation-harness)
    4.5 [Compute & infra](#45-compute--infra)
    4.6 [Access & security](#46-access--security)
5. [Experiment matrix (profiles × volumes × tasks)](#5-experiment-matrix-profiles--volumes--tasks)
6. [Scenario definitions & gold answers](#6-scenario-definitions--gold-answers)
7. [Ontology architecture & modelling guidelines](#7-ontology-architecture--modelling-guidelines)
8. [System workflow](#8-system-workflow)
9. [KPI definitions & scoring formula](#9-kpi-definitions--scoring-formula)
10. [Benchmark procedure & schedule](#10-benchmark-procedure--schedule)
11. [Roles, responsibilities, review cadence & timeline](#11-roles-responsibilities-review-cadence--timeline)
12. [Final questions to agree with the client](#12-final-questions-to-agree-with-the-client)

## 1 Introduction

Large‑language‑model (LLM) assistants already generate SQL from natural‑language prompts and interpret the resulting tables. Yet advanced analytics—forecasting, what‑if simulations, statistical tests—require explicit domain semantics that today live only in analysts’ heads or brittle prompt templates. This experiment series asks: **Does embedding a formal OWL ontology in the retrieval‑and‑generation (RAG) loop lift numeric accuracy, reasoning transparency, and performance compared with our property‑graph baseline?**

We prototype on a synthetic but realistic sales/supply‑chain dataset (orders, inventory, stores, promotions) and stress numeric reasoning (sell‑through, on‑shelf availability, price elasticity, forecast). Two triple stores—**GraphDB Free** and **Apache Jena Fuseki**—will be benchmarked under identical loads.

---

## 2 Database selection

* **Best all‑around: GraphDB Free or Jena Fuseki**

  * Both are actively maintained, support standard ontologies and reasoning, expose simple HTTP/SPARQL APIs, and are easy to migrate.
  * Both allow straightforward export/import for later platform moves.
  * Both power production‑grade LLM/graph RAG pipelines today.
  * **GraphDB Free** shines for advanced reasoning and standards compliance; **Fuseki** is slightly lighter for quick Docker deployments.
* **Avoid Blazegraph** unless a legacy dependency requires it (project is no longer maintained).
* **Virtuoso** and **AllegroGraph** remain strong options, but bring licensing/maintenance caveats that outweigh benefits for this proof‑of‑concept.

---

## 3 Objectives and success criteria

| Objective                 | Target                                                       |
| ------------------------- | ------------------------------------------------------------ |
| **Accuracy uplift**       | ≥ +6 pp numeric accuracy vs. baseline bot on shared gold set |
| **Trust & transparency**  | SME explanation score ≥ 4 / 5                                |
| **Performance viability** | p95 latency < 5 s on dev (D1) and < 12 s on perf (D2)        |
| **Maintainability**       | Add new metric or dimension in < 0.5 day engineer effort     |

---

## 4 Requirements

> **Deployment flexibility** – Components may run in the client’s VPC **or** our lab; using real client use‑cases is strongly encouraged.

### 4.1 Data layer

* PostgreSQL holding ≈ 1 M order‑line rows + dimensions (product, store, calendar, promotion, inventory).
* Python data generator to scale volumes and inject anomalies.

### 4.2 Ontology layer

* OWL 2 RL core vocabulary, optional SWRL rule set (Git‑versioned).
* RDF endpoints:

  * **GraphDB Free** (Docker) with reasoning indices on.
  * **Jena Fuseki** (Docker) with rule‑based inference.

### 4.3 LLM agent stack

* GPT‑4o or equivalent model via LangChain/Semantic‑Kernel.
* Embedding store (PGVector or FAISS) for RAG on docs + ontology annotations.

### 4.4 Evaluation harness

* PyTest‑style runner issues NL prompts, captures SQL/SPARQL, compares to gold CSV.
* Superset dashboard fed by JSON logs.

### 4.5 Compute & infra

* Two 16‑core VMs (≥ 64 GB RAM) for triple stores.
* Shared GPU‑enabled VM (or API) for LLM calls.

### 4.6 Access & security

* Synthetic IDs only; all components run inside client VPC or segregated lab.

---

## 5 Experiment matrix (profiles × volumes × tasks)

| Axis                 | Levels                                                                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Ontology profile** | **P1** OWL 2 RL (no rules) · **P2** OWL 2 RL + SWRL · **P3** OWL 2 DL                                                    |
| **Data volume**      | **D1** ≈ 10 k orders (dev) · **D2** ≈ 1 M orders (perf)                                                                  |
| **Task family**      | **T1** Aggregation · **T2** Ratios · **T3** Trends · **T4** Scenario/What‑if · **T5** Forecast · **T6** Statistical test |
| **Repository**       | GraphDB Free · Fuseki                                                                                                    |

Each scenario (section 6) runs in all applicable cells; P2/P3 tasks are skipped on P1 if rules are essential.

---

## 6 Scenario definitions & gold answers

|  ID                             | Purpose                                      | Ontology feature                                | Gold answer preparation                             |
| ------------------------------- | -------------------------------------------- | ----------------------------------------------- | --------------------------------------------------- |
| **S1** Regional roll‑up revenue | hierarchy roll‑up                            | `store ⊑ location ⊑ region` (P1)                | Sum sales by region in reference SQL, export to CSV |
| **S2** Sell‑through %           | derived ratio                                | functional prop `unitsSold ÷ unitsShipped` (P1) | Compute ratio per SKU‑month                         |
| **S3** Trend gradient           | time dimension                               | SKOS calendar hierarchy (P1)                    | Linear regression slope per category‑quarter        |
| **S4** On‑shelf availability    | SWRL rule `OutOfStock → OSA<95%` (P2)        | Flag store‑days below threshold                 |                                                     |
| **S5** Price‑uplift what‑if     | elasticity rule `ΔRev = Rev·(1+ε·ΔP/P)` (P2) | Apply ε = −1.2 synthetic value                  |                                                     |
| **S6** 4‑week forecast          | DL axioms linking seasonality factors (P3)   | ARIMA‑generated baseline forecast               |                                                     |
| **S7** Promo A/B significance   | cohort mapping, t‑test (P3)                  | SciPy t‑test p‑values pre‑computed              |                                                     |

Gold CSV files live under `/gold/<scenario>/<volume>/` and include tolerance bands (e.g., ±0.5 %).

---

## 7 Ontology architecture & modelling guidelines

* **Modules** – `core` (sales fact), `product`, `time`, `geo`, `promotion`, `inventory`.
* **Reuse** – schema.org `Product`, QUDT for units, W3C/Time for intervals, PROV for lineage.
* **Patterns** –

  * SKOS concept‑scheme for hierarchies (category, geography).
  * Reified measurement pattern for numeric KPIs.
  * Annotation property `sql:column` linking to source columns.
* **Naming** – CamelCase classes, lower\_snake predicates; namespace `http://example.com/onto#`.
* **Versioning** – Git‑tagged releases `v0.1`, `v0.2`; semantic diffs via OntoMaven.
* **Reasoning** – Remain RL‑compatible unless P2/P3 scenarios need DL constructs.

---

## 8 System workflow

1. **User NL prompt** (multi‑turn, free‑form).
2. **Retriever** pulls ontology snippets + docs via embeddings.
3. **Planner** decides SQL vs. SPARQL and drafts query skeleton.
4. **Translator** fills table/column IRIs or class/property URIs.
5. **Execution layer** runs SQL (PostgreSQL) and/or SPARQL (GraphDB/Fuseki).
6. **Post‑processor** handles numeric calcs, joins, unit checks.
7. **Explainer** converts results + reasoning trace to NL.
8. **Dialog manager** returns answer, keeps context.

---

## 9 KPI definitions & scoring formula

| KPI                     | Definition                                      | Weight |                        |      |
| ----------------------- | ----------------------------------------------- | ------ | ---------------------- | ---- |
| **Numeric accuracy**    | 1 –                                             | MAPE   | across numeric answers | 0.50 |
| **Inference success**   | expected axioms fired ÷ required axioms         | 0.15   |                        |      |
| **Query validity**      | syntactically & semantically correct SQL/SPARQL | 0.10   |                        |      |
| **Latency**             | 1 – min(1, p95 / target)                        | 0.10   |                        |      |
| **Explanation clarity** | SME Likert (1‑5) normalized                     | 0.10   |                        |      |
| **Completeness**        | % prompts fully answered first try              | 0.05   |                        |      |

**Overall score = Σ(weight × normalized KPI)**; pass threshold ≥ 0.80.

---

## 10 Benchmark procedure & schedule

| Week   | Activities                                                      |
| ------ | --------------------------------------------------------------- |
| **W0** | Kick‑off, final scope sign‑off                                  |
| **W1** | Data generator & sample load (D1); ontology skeleton v0.1       |
| **W2** | Triple‑store deployment; RL profiles (P1) loaded                |
| **W3** | LLM agent integration; evaluation harness draft; S1‑S3 dev runs |
| **W4** | Add SWRL rules; run S4‑S5; collect latency stats                |
| **W5** | DL axioms; run S6‑S7 on D1 & D2; baseline bot comparison        |
| **W6** | Full perf run (D2) on both stores; metrics dashboard freeze     |
| **W7** | Analysis, SME review, final report, hand‑off workshop           |

---

## 11 Roles, responsibilities, review cadence & timeline

| Role              | Responsibility                    | Allocation       |
| ----------------- | --------------------------------- | ---------------- |
| **Project lead**  | scope, client comms, risk mgmt    | 20 %             |
| **Ontology lead** | modelling, rules, quality gates   | 50 %             |
| **Data engineer** | PostgreSQL, ETL, data generator   | 60 %             |
| **LLM engineer**  | prompt design, planner, chain     | 60 %             |
| **QA/SME panel**  | gold answers, explanation scoring | 10 % (x3 people) |
| **DevOps**        | CI/CD, Docker, cloud cost watch   | 20 %             |

### Review cadence

* **Daily stand‑up** – 15 min.
* **Weekly demo** – every Friday, show progress vs. KPIs.
* **Steering committee** – bi‑weekly with client sponsor.

### Timeline snapshot

* **Total**: 8 weeks including buffer.
* **Gate checkpoints**: end W3 (P1 complete), end W5 (P2/3 complete), W7 (final report).

---

## 12 Final questions to agree with the client

1. **Data source** – Shall we execute the experiments on **genuine client data** (anonymized as needed) or rely on the provided **synthetic dataset** only?
2. **Infrastructure location** – Should all components run in the **client’s cloud/VPC** or in **Lingaro’s secure lab environment** (with optional migration later)?
3. **Client‑side resources** – Which **subject‑matter experts, data owners, and DevOps personnel** can the client allocate (estimated FTEs / hours per week) for prompt validation, ontology review, and environment support?
