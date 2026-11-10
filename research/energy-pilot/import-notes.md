# Read-only ENTSO-E import adapter: phase 1

Implemented: pure normalization of **average MW per UTC interval** into **MWh per complete UTC hour**, with strict 15/30/60-minute interval coverage and source metadata. No network access, token use or database writes.

The normalized result is *operational-source-labeled only if the caller supplies genuine verified measured data*. The fixture uses synthetic numbers and must not be described as a real measurement; a future importer must attach the actual source and evidence classification, including dataset revision.

The ENTSO-E Transparency Platform publishes actual load and generation, with per-market-time-unit observations. Reference: https://www.entsoe.eu/data/transparency-platform/ ; API guide: https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fweb+api%2FIG-for-TP-data-extraction-process.pdf .

Pending: authenticated API retrieval, response XML validation, explicit handling of revisions, generation/load boundary reconciliation, and an integration test with a known published dataset. **Never directly pass actual load and domestic generation as a closed islanded model.**
