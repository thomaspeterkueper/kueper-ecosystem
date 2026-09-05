# Dashboard graph live semantics

The Control Room ecosystem graph uses three distinct signals:

1. **Registry integrations** are static architecture edges.
2. **GitHub `external-tasks/open`** entries are request backlog edges. They are aggregated by source/target pair and are not animated.
3. **Supabase Control Plane traces** provide lifecycle activity. Only unblocked `claimed`, `running`, or `review_pending` work is animated. Pending/blocked work remains visible but stationary.

All enabled projects in `registry/projects.json` are rendered. Project-code aliases (ECO, ENG, NOX, SSF, KG, OTA, KUE, TKD, NXU, MISH, OMNI, AVI, KON, and system-prefixed forms) resolve to registry identities before edge aggregation.

The graph is intentionally compact: the control plane is centered, the first eight domain projects occupy an inner ring, and all remaining enabled projects occupy an outer ring. Multiple tasks on the same route are rendered as one edge with a count rather than as overlapping lines.
