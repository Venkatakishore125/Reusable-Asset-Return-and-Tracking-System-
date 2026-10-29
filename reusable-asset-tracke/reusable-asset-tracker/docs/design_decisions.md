# Design decisions and trade-offs

- **Synthetic data:** avoids personal or confidential logistics data and makes edge cases reproducible.
- **Fixed seed:** enables repeatable runs and regression tests. Use the same seed and scale to compare outputs.
- **CSV exports:** easy to inspect and portable; SQLite can be added as a persistence layer without changing entity IDs.
- **Append-only events:** preserves traceability; the snapshot is derived and should never replace event history.
- **Separate ground truth:** anomaly labels are for evaluation only and must not be joined into model input features.
- **Explicit anomalies:** the five required negative cases are labelled so validation can distinguish intentional faults from accidental data corruption.
- **Trade-off:** the generator prioritizes a runnable, inspectable baseline over full event-sourcing and advanced reconciliation. The README records this limitation honestly.
