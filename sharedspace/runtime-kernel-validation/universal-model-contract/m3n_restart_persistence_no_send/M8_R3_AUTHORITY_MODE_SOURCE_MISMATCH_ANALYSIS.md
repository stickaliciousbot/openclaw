# M8 R3 Authority Mode Source Mismatch Analysis

Classification: `SOURCE_EMITS_OBSERVE_ONLY_INSTEAD_OF_ENFORCED_NO_SEND`

Secondary: `SPEC_FIXTURE_RUNTIME_MISMATCH`

The source reused `M6_AUTHORITY_MODE` (`observe_only`) for M8's policy, valid intent, validation gate, and evidence. Fixtures accepted that value. Installed verification correctly required the M8 literal `enforced_no_send`. The package was not stale; it faithfully carried the source mismatch.
