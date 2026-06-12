# Datasets

This directory records authoritative dataset sources, metadata, and small reproducible samples used for algorithm validation.

Rules:
- Store source descriptions, download URLs, licenses, checksums, and preprocessing notes.
- Keep large raw datasets outside Git or in managed external storage.
- Do not commit non-public, production, or unredacted sensor data.
- Validation data used in automated tests should stay small and reproducible; larger cases should be referenced by manifest.
