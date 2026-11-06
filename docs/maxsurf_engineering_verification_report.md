# Maxsurf Generated Hull Artifact — Engineering Verification Report

**Date:** 2026-11-06  
**Software:** Maxsurf Modeler 64-bit 20.00.01.59  
**Process:** `MaxsurfModeler64.exe`, PID 17168 during verification  
**Verification mode:** Sandbox, read-only source handling

## Artifacts

| Role | Path | SHA-256 | Size |
|---|---|---|---:|
| Source | `D:\OpenCode\Design 1.msd` | `1695a02cbde8d75b53a4e0f2c62e3a3ad4e0889d2152dcd6da66193b1095100d` | 18022 bytes |
| Generated output | `data/projects/capability-probe/maxsurf/design1/artifacts/generated-hull.msd` | `6d6f52c9d61cc2c6d94da19accb0b9b1542d34e5abe597623b3a20dd95c76792` | 18022 bytes |

## Verified

- Source file exists and was handled read-only.
- Generated output exists in sandbox.
- Source and output checksums differ.
- Source checksum remained unchanged.
- Generated output was reopened successfully in Maxsurf by operator confirmation.
- Evidence records exist for generation and reopen inspection.

Evidence IDs:

- `b59a78c2-aa2b-46ee-922b-c188544c001e` — generated artifact
- `7a1b30bc-9fe0-44b4-979b-a88fb2d7c860` — reopen inspection

## Not verified

- NEI automated input exchange into Maxsurf.
- Hydrostatic calculations or approval.
- Stability calculations or approval.
- Hull fairness or production suitability.
- Classification, regulatory, or engineering approval.

## Capability interpretation

```text
maxsurf.hull_generation_manual = SUPPORTED
maxsurf.hull_generation_from_nei = UNKNOWN
```

`SUPPORTED` means sandbox artifact generation and reopen were evidenced. It does not mean hull design is approved for production use.

## Conclusion

Artifact exchange and manual Maxsurf reopen are traceable and reproducible in the sandbox. Keep NEI-driven automation and engineering approval explicitly unverified until separate evidence is produced.
