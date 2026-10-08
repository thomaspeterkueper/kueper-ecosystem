# KUEPER Products routing gate

Status: active proposal  
Date: 2026-10-06  
Target code: `PROD`

## Purpose

KUEPER Products is the productization layer of the ecosystem. It receives findings only when there is a plausible path from knowledge or capability to a real user problem and testable product hypothesis.

## Product Potential gate

Route a finding to `PROD` when at least one condition is met:

1. a validated or explicitly bounded effect has a plausible real-world function;
2. a recurring user problem can plausibly be addressed by a physical or digital product;
3. KUEPER Engineering has produced a capability that lacks a product/user layer;
4. a NOXIA concept has a credible near-term real-world analogue worth testing;
5. an SSF demonstrator could become a meaningful physical learning or measurement product.

Scientific interest alone is not sufficient.

## Required payload

A routed Product-Potential request should state, where known:

- source finding / evidence package;
- candidate user and use context;
- problem or useful effect;
- existing alternative or baseline;
- engineering dependencies;
- first falsification criterion;
- evidence maturity and uncertainty.

Unknown fields must remain unknown; do not invent costs, performance or market demand.

## Outcomes

Products may classify the item as:

- structured product opportunity;
- Research Watch / hold;
- rejected / no product case.

Negative decisions remain documented to prevent repeated rediscovery.

## Source-of-truth boundaries

- OTA owns evidence provenance.
- KG owns canonical concepts and relations.
- Engineering owns feasibility, calculations and technical baselines.
- SSF owns learning/demonstration context.
- Products owns product problem, users, requirements, portfolio, usability, costing, lifecycle and maturity.
- NOXIA owns gameplay/future simulation and is not evidence of real-world feasibility.

## Google Drive

Product-owned binary/working artifacts may live in the KUEPER Products Google Drive structure. Git remains the durable index and stores product identity, status, decisions and Drive references. Engineering calculations are referenced rather than silently forked into Drive.
