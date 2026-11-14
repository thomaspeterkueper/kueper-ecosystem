# Synthetic energy pilot v0.1

Run: `node --test research/energy-pilot/energy.test.mjs` (Node.js >= 20).

One-hour steps; all power caps kW and energy values kWh. Dispatch priority: direct renewables, battery, hydrogen. Surplus charges battery before hydrogen; deficits discharge battery before hydrogen. Battery and hydrogen efficiencies are **full-cycle assumptions applied on charging** for an idealized aggregate model, not independently calibrated charge/discharge efficiencies. No imports, no real-world dispatch or costs.

Evidence: synthetic only. The result checks an explicit energy conservation residual. It cannot establish empirical reliability or economic competitiveness.

Future work: distinct charge/discharge efficiencies, self-discharge, initial state, capacity degradation, reserve constraints, scenario costs, multi-day weather inputs, and benchmark against real measurements.

Source context: NREL Storage Futures Study https://www.nrel.gov/docs/fy21osti/78694.pdf and 2026 comparative review https://doi.org/10.1016/j.est.2026.122821. Parameter choices in tests are arbitrary fixtures, not estimates from these studies.
