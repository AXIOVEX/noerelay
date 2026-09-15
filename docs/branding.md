# Axiovex Systems, LLC branding

The canonical repository is [AXIOVEX/noerelay](https://github.com/AXIOVEX/noerelay). NoeRelay is a product of **Axiovex Systems, LLC**. Its proprietary license terms are unchanged; Python package metadata now points to the existing LICENSE instead of incorrectly declaring MIT.

Approved artwork comes from [the AXIOVEX brand package](https://github.com/AXIOVEX/solution-delivery-framework/tree/main/assets/brand). The imported banner and existing logos are unmodified. `deploy/docker/brand/SOURCE.json` pins revision and checksum provenance. Preserve aspect ratios, clear space, and the supplied colors. Open WebUI attribution remains visible.

Active documentation, repository links, SIEM vendor labels, package metadata, schema identifier namespaces, and UI company notices use the new identity. Local helper scripts resolve the checkout dynamically; Cursor uses `${workspaceFolder}`. The local checkout folder is not moved by a GitHub organization transfer.

Historical evidence, runtime claims, AEE assessments, and the chained ledger retain their original recorded paths and identities. Editing those records would invalidate their hashes. Prior records can also contain source digests for files changed by this migration; they describe their recorded revision, not the current file bytes.

Run `python scripts/verify-branding.py` to check active references, package metadata, schema identifiers, and approved asset hashes. `evidence/branding/live-webui.json` records the observed deployed company watermark, identity banner, and served asset digests. G12 / NR-OPS-008 / T-OPS-008 tracks this migration.
