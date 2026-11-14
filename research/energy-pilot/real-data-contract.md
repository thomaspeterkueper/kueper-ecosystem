# Real-data integration contract (planned; no live ingestion yet)

Source candidate: ENTSO-E Transparency Platform, https://www.entsoe.eu/data/transparency-platform/ . Its publications include generation, actual load, transmission and balancing data. Documentation: https://transparencyplatform.zendesk.com/hc/en-us/articles/16647979768084-Actual-Total-Load-Day-ahead-Per-Bidding-Zone-6-1-A-6-1-B

**Do not treat total load and domestic generation as a closed system.** Actual load is affected by imports, exports, storage charging and losses. The synthetic model assumes an islanded system and requires a consistent system boundary. Add net imports/exports, curtailment, and storage measurements or choose a properly isolated dataset before calibration.

Import contract: source URL, retrieved_at, zone, UTC timestamps, interval duration, generation type, unit (MW or MWh), license, missingness, quality flags, revision timestamp. Convert power MW to energy MWh using exact interval duration; resample to 1-hour energy buckets only with complete interval coverage. Reject duplicate, non-monotonic, ambiguous timezone and missing intervals. Keep measured data immutable and derived scenarios separately labeled as simulation.

Next: create a read-only ingestion adapter with fixture data, timestamp and units tests, and independently verify ENTSO-E API credentials and usage terms. No API key is committed.
