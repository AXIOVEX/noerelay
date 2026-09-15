#!/usr/bin/env python3
"""Generate spec-kit feature folders for the NoeRelay GA completion program.

One feature folder per work package:

    .specify/features/<pkg-lower>/{spec.md, plan.md, tasks.md}

plus a `.specify/features/README.md` index.

The generator keeps the generated specs in sync with the two machine/human
authoritative sources so the spec-kit layer matches the real architecture:

  * spec/coverage-manifest.json  -> requirement -> work-package -> release-test
                                    mapping and the G0-G8 evidence gates. This is
                                    the file `xtask evidence validate/coverage/gate`
                                    parses, so requirement/test IDs used here are
                                    taken from it, never re-typed.
  * docs/requirements.md         -> requirement text + acceptance outcome, parsed
                                    from the Markdown tables (single source of
                                    truth for wording).

Per-package narrative (outcome, approach, components, risks, acceptance, tasks)
is encoded below from docs/ga-completion-orchestrator-plan.md sections 6 and 7.
Component references point at the real crate modules that exist in this
repository; where a capability is not yet implemented the component is listed as
the target module and the task list carries the build work.

Idempotent: re-running overwrites the managed files. It does not touch anything
outside .specify/features/.

Run:  python scripts/generate_specify_features.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import OrderedDict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
MANIFEST_PATH = os.path.join(REPO_ROOT, "spec", "coverage-manifest.json")
REQUIREMENTS_PATH = os.path.join(REPO_ROOT, "docs", "requirements.md")
FEATURES_DIR = os.path.join(REPO_ROOT, ".specify", "features")

REQ_ID_RE = re.compile(r"^NR-[A-Z]+-\d{3}$")


# --------------------------------------------------------------------------- #
# Source parsing
# --------------------------------------------------------------------------- #
def load_manifest(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_requirements(path: str) -> "OrderedDict[str, dict]":
    """Parse `| ID | Requirement | Acceptance outcome |` tables in requirements.md."""
    reqs: "OrderedDict[str, dict]" = OrderedDict()
    in_table = False
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            s = line.strip()
            if s.startswith("| ID | Requirement"):
                in_table = True
                continue
            if not in_table:
                continue
            if not s.startswith("|"):
                in_table = False
                continue
            if set(s.replace("|", "").strip()) <= set("-: "):
                continue  # separator row
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 3:
                rid = cells[0].strip("`").strip()
                if REQ_ID_RE.match(rid):
                    reqs[rid] = {"text": cells[1], "acceptance": cells[2]}
    return reqs


def build_maps(manifest: dict):
    """Invert manifest into pkg->reqs and req->tests, and collect gate info."""
    pkg_to_reqs: "OrderedDict[str, list]" = OrderedDict()
    req_to_tests: "dict[str, list]" = {}
    for r in manifest.get("requirements", []):
        rid = r["requirement_id"]
        req_to_tests[rid] = list(r.get("primary_release_tests", []))
        for wp in r.get("primary_work_packages", []):
            pkg_to_reqs.setdefault(wp, [])
            if rid not in pkg_to_reqs[wp]:
                pkg_to_reqs[wp].append(rid)
    gates = manifest.get("release_gates", {})
    return pkg_to_reqs, req_to_tests, gates


# --------------------------------------------------------------------------- #
# Per-work-package catalog (from plan sections 6 and 7)
# --------------------------------------------------------------------------- #
# Each entry: id, title, outcome, approach, goals[], non_goals[], components[],
# risks[], acceptance[], tasks[]. `requirements` is derived from the manifest at
# run time (packages absent from the manifest are treated as supporting).
PACKAGES = [
    # ---- FND ----
    dict(
        id="FND-01",
        title="Freeze profile, scope, baseline, and risks",
        outcome="Capture the immutable baseline: the named v1 deployment profile, the frozen "
                "requirement set, the requirement-to-work-package traceability, and the initial "
                "risk register. Everything downstream is validated against this baseline.",
        approach="Record the DEC-01 local/test-only decision, the named profile ID, non-goals, and "
                "risk register in docs/fnd-01-scope-baseline.md; freeze the requirement set and the "
                "machine-readable coverage manifest; validate traceability (no orphans, unique IDs, "
                "no placeholders) before any implementation wave starts.",
        goals=[
            "Freeze the named deployment profile and its non-goals.",
            "Freeze the authoritative MUST requirement set and its IDs.",
            "Produce and validate the requirement-to-work-package coverage manifest.",
            "Establish the initial risk register and the local/test-only evidence profile.",
        ],
        non_goals=[
            "No production deployment or external customer commitment.",
            "No requirement additions or scope changes after freeze (those are new revisions).",
        ],
        components=[
            "docs/fnd-01-scope-baseline.md (DEC-01 record, profile, risk register, traceability validation)",
            "spec/coverage-manifest.json (machine-readable req -> package -> test + gates)",
            "xtask/src/main.rs (evidence record/validate/coverage/gate entry points)",
        ],
        risks=[
            "Scope creep after freeze invalidates earlier evidence; must be gated as a new revision.",
            "Placeholder or orphaned requirement IDs silently weaken the release gate.",
        ],
        acceptance=[
            "Every MUST requirement has at least one primary work package and one release test.",
            "No orphaned requirements, no duplicate IDs, no TBD placeholders in the manifest.",
            "Named profile ID and DEC-01 local/test-only status are recorded and approved.",
        ],
        tasks=[
            "Record DEC-01 decision and the named profile ID in docs/fnd-01-scope-baseline.md.",
            "Freeze the requirement set and confirm IDs against docs/requirements.md.",
            "Validate spec/coverage-manifest.json (orphan, uniqueness, placeholder checks).",
            "Record the baseline revision and current test baseline for evidence.",
        ],
    ),
    dict(
        id="FND-02",
        title="One versioned cross-language schema lineage",
        outcome="Establish a single versioned schema lineage that defines all wire and domain "
                "objects across Rust, Python, Go, and TypeScript, so no language hand-writes a "
                "competing definition.",
        approach="Own object definitions in Rust; generate JSON Schema and OpenAPI from the Rust "
                "types via xtask; gate every change with a breaking-change diff and golden "
                "round-trip vectors. Handwritten competing definitions are prohibited.",
        goals=[
            "Generate JSON Schema and OpenAPI from the Rust canonical types.",
            "Gate schema changes with a breaking-change diff.",
            "Prove round-trip stability with golden vectors.",
        ],
        non_goals=[
            "No language-specific divergent object models.",
            "No hand-edited generated files.",
        ],
        components=[
            "crates/noerelay-core/src/wire.rs (canonical wire types)",
            "crates/noerelay-core/src/types.rs (domain types)",
            "xtask/src/schema.rs (generate_json, generate_openapi, diff)",
            "xtask/src/golden.rs (golden vector round-trip)",
            "spec/schemas/ (committed generated schemas)",
        ],
        risks=[
            "A hand-edited generated file drifts from the Rust source of truth.",
            "Breaking changes ship without a recorded diff and invalidate dependent evidence.",
        ],
        acceptance=[
            "JSON Schema and OpenAPI regenerate cleanly with an empty diff on a no-op run.",
            "Golden vectors round-trip without loss for every supported wire object.",
            "A breaking change is detected by the diff gate before merge.",
        ],
        tasks=[
            "Wire xtask schema generate/diff into the required test commands.",
            "Commit generated JSON Schema and OpenAPI under spec/schemas/.",
            "Add golden vectors for the core wire objects.",
            "Add a CI step that fails on a non-empty schema diff.",
        ],
    ),
    dict(
        id="FND-03",
        title="Executable observed-evidence pipeline",
        outcome="Make evidence collection executable: every test ID records command, revision, "
                "environment, result, and artifact hash into an evidence bundle that the release "
                "gate can validate.",
        approach="Implement the evidence envelope and the record/validate/coverage/gate commands in "
                "xtask; ingest evaluator outcomes (pass/warn/iterate/clarify/gather_evidence/block) "
                "as observed events; enforce that a test ID is not evidence until a runner records "
                "the full envelope.",
        goals=[
            "Record a complete evidence envelope per test run.",
            "Validate bundles against the coverage manifest.",
            "Report requirement coverage and gate readiness.",
        ],
        non_goals=[
            "No acceptance from model self-attestation without an observed test event.",
            "No reuse of evidence from a different revision or artifact digest.",
        ],
        components=[
            "xtask/src/evidence.rs (TestRunRecorder, envelope)",
            "xtask/src/validate.rs (BundleValidator)",
            "xtask/src/coverage.rs (coverage report, gate check)",
            "crates/noerelay-core/src/evidence.rs (evidence model)",
            "crates/noerelay-core/src/evaluator_ingestion.rs (SpecKitHook outcome mapping)",
            "evidence/ (recorded bundles and baselines)",
        ],
        risks=[
            "Evidence recorded against the wrong revision is silently stale.",
            "A test ID treated as passing without a recorded envelope defeats the gate.",
        ],
        acceptance=[
            "xtask evidence validate passes only for complete, manifest-consistent bundles.",
            "xtask evidence coverage reports per-requirement coverage with no orphans.",
            "xtask evidence gate reports pass/fail per G0-G8 gate.",
        ],
        tasks=[
            "Implement the evidence envelope schema and recorder in xtask.",
            "Implement bundle validation against the coverage manifest.",
            "Implement the coverage report and per-gate check.",
            "Record a baseline evidence bundle for the local/test profile.",
        ],
    ),
    # ---- GOV ----
    dict(
        id="GOV-01",
        title="Immutable V-model governance registry",
        outcome="Persist immutable, bidirectionally linked revisions for architecture, requirements, "
                "threats, tests, policies, work orders, artifacts, evidence, and release baselines, "
                "with a queryable impact graph and revision pinning.",
        approach="Store immutable revisions with the lifecycle draft->proposed->reviewed->approved->"
                "active->superseded (plus rejected). Runs pin exact revisions and never read a moving "
                "latest pointer. Changing an active requirement creates a new revision and marks "
                "dependent unexecuted evidence stale; it never edits history. The implementing "
                "identity cannot activate its own high-risk acceptance revision.",
        goals=[
            "Persist immutable revisions for every governed object class.",
            "Maintain bidirectional links and an impact graph.",
            "Enforce revision pinning and stale-evidence invalidation.",
            "Keep the Rust release gate as the final automated authority.",
        ],
        non_goals=[
            "No editing of a historical revision that governed an earlier run.",
            "No self-activation of a high-risk acceptance revision by its implementer.",
        ],
        components=[
            "crates/noerelay-store/src/governance.rs (governance repository)",
            "crates/noerelay-core/src/governance.rs (governance domain model)",
            "crates/noerelay-core/src/traceability.rs (impact graph, orphan/cycle detection)",
            "crates/noerelay-gateway/src/lib.rs (governance_release_gate route)",
        ],
        risks=[
            "A moving latest pointer lets a run read a revision it was not governed by.",
            "An orphan or cycle in the impact graph silently breaks traceability.",
        ],
        acceptance=[
            "T-SPEC-001 proves immutable revision pinning and historical replay.",
            "Orphan and cycle entries are rejected on write.",
            "Changing an active requirement marks dependent unexecuted evidence stale.",
            "Unauthorized activation or supersession is denied.",
        ],
        tasks=[
            "Model the governed object classes and the revision lifecycle.",
            "Implement bidirectional links and the impact graph query.",
            "Implement revision pinning and stale-evidence invalidation.",
            "Add the release-gate authorization check (no self-activation).",
            "Add T-SPEC-001 fixtures for pinning, orphan, cycle, and replay.",
        ],
    ),
    # ---- IAM ----
    dict(
        id="IAM-01",
        title="Canonical tenancy and policy scope",
        outcome="Implement normalized organizations, projects, environments, principals, "
                "memberships, roles, permissions, quotas, and policy bindings, with scope derived "
                "from authenticated identity and forced RLS on every tenant-bearing table.",
        approach="Scope is derived from authenticated identity and server-side bindings, never "
                "trusted from caller headers. Apply and force RLS to every tenant-bearing table "
                "including caches, streams, outbox rows, artifacts, reports, and recommendation "
                "data. Build the full role x route x tenant x project allow/deny matrix.",
        goals=[
            "Normalize the tenancy and policy model in PostgreSQL and Rust.",
            "Derive scope from authenticated identity only.",
            "Force RLS on every tenant-bearing table.",
        ],
        non_goals=[
            "No trust in caller-supplied scope headers.",
            "No cross-tenant read, inference, mutation, or enumeration.",
        ],
        components=[
            "crates/noerelay-store/src/iam.rs (tenancy repository)",
            "crates/noerelay-core/src/iam.rs (tenancy domain model)",
            "crates/noerelay-gateway/src/iam.rs (scope derivation at the boundary)",
        ],
        risks=[
            "A pooled connection that does not reset scope leaks a prior tenant's RLS context.",
            "A cache or stream key that omits scope enables cross-tenant disclosure.",
        ],
        acceptance=[
            "T-IAM-001 denies every unauthorized role x route x tenant x project combination.",
            "Direct-ID, list, pagination, search, timing, cache-key, stream-resume, export, and "
            "error-message enumeration attacks are denied or non-enumerating.",
            "RLS holds under distinct database roles and pooled-connection scope reset.",
        ],
        tasks=[
            "Implement the normalized tenancy and policy tables with RLS.",
            "Implement server-side scope derivation from authenticated identity.",
            "Add the role x route x tenant x project allow/deny matrix tests.",
            "Add RLS tests with distinct roles and pooled-connection reset.",
        ],
    ),
    dict(
        id="IAM-02",
        title="API keys",
        outcome="Implement one-time API-key issuance with versioned prefix plus high-entropy secret, "
                "keyed-hash storage, constant-time verification, scoping, expiry, revocation, atomic "
                "rotation, and per-key rate and concurrency limits.",
        approach="Store keys with Argon2id (or an approved keyed hash). Verify in constant time. "
                "Never log or return the secret after creation. Enforce per-key rate and "
                "concurrency limits and record immutable audit events for the key lifecycle.",
        goals=[
            "Issue, verify, rotate, and revoke keys with keyed-hash storage.",
            "Enforce per-key rate and concurrency limits.",
            "Record immutable audit events for every key lifecycle action.",
        ],
        non_goals=[
            "No secret returned or logged after creation.",
            "No non-constant-time secret comparison.",
        ],
        components=[
            "crates/noerelay-store/src/api_keys.rs (issue/verify/revoke/rotate, rate + concurrency)",
        ],
        risks=[
            "A timing side-channel in verification leaks secret material.",
            "A non-atomic rotation window lets a revoked key keep working.",
        ],
        acceptance=[
            "T-IAM-002 passes creation, hash-at-rest, rotation, revocation, expiry, and concurrent use.",
            "Old-key use fails immediately after an atomic rotation.",
            "Brute-force attempts are throttled; compromised-key exercise revokes cleanly.",
        ],
        tasks=[
            "Implement one-time issuance with versioned prefix and keyed-hash storage.",
            "Implement constant-time verification and per-key rate/concurrency limits.",
            "Implement atomic rotation and immediate revocation with audit events.",
            "Add T-IAM-002 fixtures including the compromised-key exercise.",
        ],
    ),
    dict(
        id="IAM-03",
        title="OIDC, service identities, and RBAC",
        outcome="Define a versioned Rust identity-provider port that validates OIDC tokens and maps "
                "claims to the canonical scope model, with deny-by-default RBAC on every "
                "administrative route.",
        approach="Validate issuer, audience, signature, time claims, and nonce where applicable, "
                "with an explicit claim-to-scope mapping. Keep workload identities separate from "
                "humans. Map every administrative route and mutation to an explicit permission; "
                "unmapped routes deny. Bind step-up approvals to approver identity, scope, action "
                "hash, expiry, and separation of duties.",
        goals=[
            "Define the versioned identity-provider port and OIDC validation.",
            "Map claims to the canonical principal and scope model.",
            "Enforce deny-by-default RBAC on every administrative route.",
        ],
        non_goals=[
            "No unmapped administrative route reachable by a non-admin caller.",
            "No token confusion or replay across audiences.",
        ],
        components=[
            "crates/noerelay-core/src/iam.rs (identity port, claim mapping)",
            "crates/noerelay-gateway/src/iam.rs (route-permission enforcement)",
            "crates/noerelay-gateway/src/admin.rs (administrative routes)",
        ],
        risks=[
            "A missing route-permission mapping defaults to allow instead of deny.",
            "Token replay or audience confusion grants cross-tenant admin.",
        ],
        acceptance=[
            "OIDC/provider contract tests and token confusion/replay fixtures pass.",
            "Complete route-permission coverage: every admin route maps to a permission.",
            "Independent security review passes.",
        ],
        tasks=[
            "Implement the versioned identity-provider port and OIDC validation.",
            "Implement the claim-to-scope mapping for humans and workloads.",
            "Enforce deny-by-default RBAC across all administrative routes.",
            "Add token confusion/replay fixtures and the route-permission coverage test.",
        ],
    ),
    dict(
        id="IAM-04",
        title="Tenant lifecycle, retention, deletion, legal hold, export",
        outcome="Implement tenant data lifecycle: a complete data inventory, versioned lifecycle "
                "policies, legal hold, deletion jobs, cryptographic deletion where appropriate, "
                "export, tombstones, and reconciliation.",
        approach="Inventory every authoritative row, prompt, output, artifact, cache, trace, log, "
                "backup, receipt, recommendation feature, export, and provider copy. Apply versioned "
                "retention/residency policies; document what cannot be deleted immediately from "
                "immutable audit proofs or backups and why.",
        goals=[
            "Build the authoritative data inventory.",
            "Implement versioned retention, legal hold, deletion, and export.",
            "Reconcile lifecycle behavior across every store and derived view.",
        ],
        non_goals=[
            "No scoped record remains after deletion except configured tombstones/audit proofs.",
            "No legal-hold bypass.",
        ],
        components=[
            "crates/noerelay-store/src/lifecycle.rs (retention, hold, deletion, export)",
            "crates/noerelay-store/src/artifacts.rs (artifact retention and deletion)",
        ],
        risks=[
            "A derived view (cache, index, recommendation feature) is missed by deletion.",
            "Legal hold is not enforced on a deletion job path.",
        ],
        acceptance=[
            "Seeded canary records are removed or retained exactly per policy across every store and view.",
            "Backup expiry and legal-hold behavior are independently verified.",
            "Deletion tests prove no scoped record remains except configured tombstones/audit proofs.",
        ],
        tasks=[
            "Produce the authoritative data inventory.",
            "Implement versioned retention, legal hold, deletion jobs, and export.",
            "Add canary deletion/retention tests across every store and derived view.",
            "Document the non-deletable audit-proof and backup residue and why.",
        ],
    ),
    # ---- RUN ----
    dict(
        id="RUN-01",
        title="Persistent run/step/attempt/work-item state machines",
        outcome="Represent execution as normalized, append-friendly, durable entities (run, step, "
                "attempt, work item, dependency, reservation, approval, tool effect, provider call, "
                "verification check, artifact, terminal outcome) with legal transitions defined in "
                "Rust and enforced by database constraints.",
        approach="Replace whole-project snapshots as the only execution representation. Keep "
                "snapshot/replay projections only if useful, but make invariants transactional and "
                "explicitly versioned. Restarting at any transition boundary must reconstruct the "
                "same admissible next actions and never regenerate completed work from prose.",
        goals=[
            "Model the normalized durable execution entities.",
            "Define legal transitions in Rust and as database constraints.",
            "Make invariants transactional and versioned.",
        ],
        non_goals=[
            "No regeneration of completed work from prose on restart.",
            "No whole-project snapshot as the sole authority.",
        ],
        components=[
            "crates/noerelay-store/src/execution.rs (create_run/step/attempt/work_item, status updates)",
            "crates/noerelay-core/src/execution.rs (execution domain model)",
        ],
        risks=[
            "An illegal transition accepted at the boundary corrupts the run.",
            "A restart regenerates completed work, double-executing side effects.",
        ],
        acceptance=[
            "Restart at every transition boundary reconstructs the same admissible next actions.",
            "Completed work is never regenerated from prose.",
            "Illegal transitions are rejected by both Rust and the database constraints.",
        ],
        tasks=[
            "Model the normalized execution entities and their legal transitions.",
            "Add database constraints mirroring the Rust transition rules.",
            "Implement restart reconstruction and prove no completed-work regeneration.",
            "Add transition-boundary restart tests.",
        ],
    ),
    dict(
        id="RUN-02",
        title="Transactional outbox, leases, retries, and circuit breakers",
        outcome="Write authority state and an outbox event in one PostgreSQL transaction; run "
                "workers with bounded leases, heartbeats, fencing tokens, attempt limits, and "
                "poison-message quarantine; classify failures and scope circuit breakers.",
        approach="Emit outbox events atomically with the state change. Workers claim jobs with "
                "bounded leases and fencing tokens. Classify failures as transport, rate/quota, "
                "capability, semantic, epistemic, policy, specification, cancellation, or permanent; "
                "retry policy is operation-specific and budget-aware. Circuit breakers are scoped by "
                "provider/model/agent/tool and emit audit events.",
        goals=[
            "Emit outbox events atomically with authority state.",
            "Run leased, fenced, bounded workers with poison-message quarantine.",
            "Classify failures and scope circuit breakers with audit events.",
        ],
        non_goals=[
            "No policy failure retried as a transport failure.",
            "No unbounded retry or unscoped circuit breaker.",
        ],
        components=[
            "crates/noerelay-store/src/execution.rs (enqueue_outbox_event, claim_work_item, "
            "record_circuit_success/failure, expire_leases)",
        ],
        risks=[
            "A duplicate or reordered outbox delivery double-applies an effect.",
            "An expired lease is re-claimed while the original worker is still running.",
        ],
        acceptance=[
            "Killing workers before, during, and after provider/tool calls converges to one valid "
            "terminal state.",
            "Duplicate and reordered deliveries are handled without duplicate effects.",
            "Lease expiry and database failure are handled without split-brain.",
        ],
        tasks=[
            "Implement atomic outbox emission with the state change.",
            "Implement leased, fenced work claiming with poison-message quarantine.",
            "Implement failure classification and budget-aware retries.",
            "Implement scoped circuit breakers with audit events.",
            "Add worker-kill and duplicate-delivery fault tests.",
        ],
    ),
    dict(
        id="RUN-03",
        title="Scoped idempotency, cancellation, and side effects",
        outcome="Bind external idempotency keys to principal scope, endpoint profile, normalized "
                "request hash, and policy revision; propagate cancellation through the run DAG; and "
                "use an effect-intent/effect-result protocol with stable effect IDs.",
        approach="Store response/terminal references durably. Propagate cancellation through runs, "
                "provider streams, tools, MCP, A2A, and reservations. Use stable effect IDs, "
                "downstream idempotency where supported, reconciliation where not, and explicit "
                "unknown_effect_state escalation.",
        goals=[
            "Bind idempotency keys to scope, profile, request hash, and policy revision.",
            "Propagate cancellation across the full run DAG.",
            "Guarantee exactly-once visible effects via the effect protocol.",
        ],
        non_goals=[
            "No duplicate externally visible side effect under retry.",
            "No silent unknown effect state without escalation.",
        ],
        components=[
            "crates/noerelay-store/src/execution.rs (claim_idempotency_key, request_cancellation, "
            "record_effect_request/result, reconcile_effect)",
        ],
        risks=[
            "Same key with changed input is replayed instead of conflicting.",
            "A cancelled run leaves a reserved budget unreconciled.",
        ],
        acceptance=[
            "T-API-003 and T-EXEC-001 prove same-key replay and conflict on changed input.",
            "No duplicate visible effect under retry.",
            "Budget is released and reconciled after cancellation.",
        ],
        tasks=[
            "Implement scoped idempotency key binding and durable terminal references.",
            "Implement cancellation propagation across the run DAG.",
            "Implement the effect-intent/effect-result protocol with reconciliation.",
            "Add replay, conflict, and post-cancellation reconciliation tests.",
        ],
    ),
    dict(
        id="RUN-04",
        title="Multi-replica conflict recovery and failover",
        outcome="Add optimistic-conflict reload/retry, leader-free work claiming where possible, "
                "graceful drain, database failover behavior, and multi-replica stream ownership.",
        approach="Use compare-and-swap on work items with optimistic reload/retry. Claim work "
                "leader-free where possible. Drain gracefully on shutdown. Define and test database "
                "failover behavior and multi-replica stream ownership without split-brain acceptance.",
        goals=[
            "Recover from optimistic conflicts via reload/retry.",
            "Support graceful drain and database failover.",
            "Own streams across multiple replicas without split-brain.",
        ],
        non_goals=[
            "No split-brain acceptance under contention or failover.",
            "No lost or duplicated work across replicas.",
        ],
        components=[
            "crates/noerelay-store/src/execution.rs (acquire_lease, update_work_item_cas, "
            "claim_orphaned_work, acquire_stream, handle_failover, register/heartbeat/drain worker)",
        ],
        risks=[
            "Two replicas accept the same work item during a failover.",
            "A stale lease holder is not fenced after failover.",
        ],
        acceptance=[
            "Multi-replica contention, object-store outage, corrupt object, database failover, and "
            "rolling-deployment suites pass without split-brain acceptance.",
            "Orphaned work is reclaimed exactly once.",
        ],
        tasks=[
            "Implement CAS-based work claiming with optimistic reload/retry.",
            "Implement graceful drain and worker lifecycle (register/heartbeat/drain).",
            "Implement multi-replica stream ownership and orphaned-work reclamation.",
            "Add failover and rolling-deployment fault tests.",
        ],
    ),
    # ---- ART ----
    dict(
        id="ART-01",
        title="S3-compatible content-addressed artifact plane",
        outcome="Store large inputs, outputs, media, and test logs in a content-addressed object "
                "store with scope metadata, encryption, retention, integrity hashes, and receipt "
                "binding, while the database remains the authority for artifact identity and "
                "authorization.",
        approach="Address artifacts by content hash. Bind scope, content type, size, retention, and "
                "integrity hash in the database. Keep binary media out of JSON/database rows. Apply "
                "malware/content checks where applicable and bind artifacts to receipts.",
        goals=[
            "Store large payloads in a content-addressed object store.",
            "Bind scope, integrity, retention, and receipt in the database.",
            "Keep the database authoritative for identity and authorization.",
        ],
        non_goals=[
            "No binary media stored in JSON/database rows.",
            "No artifact accepted without an integrity hash and scope binding.",
        ],
        components=[
            "crates/noerelay-store/src/artifacts.rs (artifact repository)",
            "crates/noerelay-core/src/artifacts.rs (artifact domain model)",
        ],
        risks=[
            "A corrupt or swapped object is accepted without integrity verification.",
            "An artifact is readable across scope because the binding is missing.",
        ],
        acceptance=[
            "Corrupt-object and object-store-outage suites fail closed.",
            "Every accepted artifact verifies its integrity hash and scope binding.",
            "Artifacts are bound to receipts and respect retention.",
        ],
        tasks=[
            "Implement content-addressed storage with scope and integrity metadata.",
            "Implement receipt binding and retention enforcement.",
            "Add corrupt-object and cross-scope access tests.",
        ],
    ),
    # ---- API ----
    dict(
        id="API-01",
        title="Frozen compatibility profiles and fixture matrix",
        outcome="Freeze the supported OpenAI compatibility profile (text, structured output, tools, "
                "multimodal, usage, metadata, error, cancellation) and generate a positive/negative "
                "fixture matrix for every supported field.",
        approach="Use the official OpenAI Chat Completions and Responses references as inputs but "
                "freeze a supported NoeRelay profile. Generate positive and negative fixtures for "
                "each supported field and explicitly reject every unsupported field with stable "
                "OpenAI-shaped errors. Run official SDKs in at least Python, TypeScript, and one "
                "more language against the suite.",
        goals=[
            "Freeze the supported compatibility profile.",
            "Generate positive and negative fixtures per supported field.",
            "Reject unsupported fields with stable OpenAI-shaped errors.",
        ],
        non_goals=[
            "No claim of every current and future OpenAI field.",
            "No unknown field passed through with altered meaning.",
        ],
        components=[
            "crates/noerelay-core/src/wire.rs (canonical wire request/response IR)",
            "tests/compat/test_fixtures.rs (compatibility fixtures)",
        ],
        risks=[
            "An unsupported field is silently reinterpreted instead of rejected.",
            "The support matrix is hand-maintained and drifts from the tests.",
        ],
        acceptance=[
            "T-API-001 passes all golden and negative fixtures.",
            "The support matrix is generated from tests and published.",
            "Official SDKs in at least three languages pass the suite.",
        ],
        tasks=[
            "Freeze the supported profile and document the field matrix.",
            "Generate positive and negative fixtures per field.",
            "Implement stable OpenAI-shaped errors for unsupported fields.",
            "Add official-SDK conformance runs (Python, TypeScript, +1).",
        ],
    ),
    dict(
        id="API-02",
        title="Complete supported Chat Completions behavior",
        outcome="Implement the complete supported Chat Completions behavior, normalizing the public "
                "API into the internal Rust request IR and projecting terminal results back into the "
                "requested profile.",
        approach="Normalize Chat Completions into the canonical IR, apply governance, route, "
                "execute, verify, and project the result back. Preserve tool-call normalization, "
                "streaming, usage, and error behavior within the frozen profile.",
        goals=[
            "Normalize Chat Completions into the canonical IR.",
            "Project terminal results back into the Chat profile.",
            "Preserve tool-call, usage, and error behavior in profile.",
        ],
        non_goals=[
            "No field outside the frozen profile.",
            "No authority decision made outside Rust.",
        ],
        components=[
            "crates/noerelay-gateway/src/lib.rs (chat_completions, proxy_openai_request, "
            "normalize_legacy_tool_calls)",
            "crates/noerelay-core/src/wire.rs (canonical IR)",
        ],
        risks=[
            "A legacy tool-call envelope is promoted to a native call without an allowed tool.",
            "A rejected output leaks through an earlier stream chunk.",
        ],
        acceptance=[
            "T-API-001 passes Chat golden and negative fixtures.",
            "Legacy tool envelopes are promoted only for allowed tools.",
            "Usage and error shapes match the frozen profile.",
        ],
        tasks=[
            "Implement Chat Completions normalization into the canonical IR.",
            "Implement tool-call normalization and promotion guards.",
            "Implement result projection back to the Chat profile.",
            "Add Chat golden/negative fixtures to T-API-001.",
        ],
    ),
    dict(
        id="API-03",
        title="Complete supported Responses behavior",
        outcome="Implement the complete supported Responses behavior, normalizing into the same "
                "internal Rust request IR and projecting terminal results back into the Responses "
                "profile.",
        approach="Share the canonical IR with Chat Completions so the two profiles do not diverge. "
                "Project terminal results into the Responses shape, preserving usage, errors, and "
                "tool behavior within the frozen profile.",
        goals=[
            "Normalize Responses into the shared canonical IR.",
            "Project terminal results back into the Responses profile.",
            "Keep Chat and Responses behavior consistent through the shared IR.",
        ],
        non_goals=[
            "No dependence on one provider's beta semantics in the canonical IR.",
            "No field outside the frozen profile.",
        ],
        components=[
            "crates/noerelay-gateway/src/lib.rs (responses, proxy_openai_request)",
            "crates/noerelay-core/src/wire.rs (shared canonical IR)",
        ],
        risks=[
            "The Responses profile diverges from Chat through a separate code path.",
            "A provider beta semantic leaks into the canonical IR.",
        ],
        acceptance=[
            "T-API-001 passes Responses golden and negative fixtures.",
            "Chat and Responses produce consistent governance through the shared IR.",
            "Usage and error shapes match the frozen profile.",
        ],
        tasks=[
            "Implement Responses normalization into the shared canonical IR.",
            "Implement result projection back to the Responses profile.",
            "Add Responses golden/negative fixtures to T-API-001.",
        ],
    ),
    dict(
        id="API-04",
        title="Governed incremental streaming, resume, and cancellation",
        outcome="Implement a durable stream event model with monotonic sequence IDs, bounded "
                "buffers, backpressure, heartbeats, resume cursors, disconnect cancellation, and "
                "risk-class-aware output gating.",
        approach="Parse provider SSE into canonical events (never treated as authority). Low risk "
                "may stream verified-safe increments; medium/high/critical output is buffered or "
                "provisional until checks pass. A terminal accepted event is impossible before "
                "durable verification and receipt commit; rejected output is not leaked through "
                "earlier chunks.",
        goals=[
            "Implement the durable stream event model with monotonic sequence IDs.",
            "Gate output by risk class without leaking rejected content.",
            "Support resume cursors and disconnect cancellation.",
        ],
        non_goals=[
            "No terminal accepted event before durable verification and receipt commit.",
            "No provider SSE treated as authority.",
        ],
        components=[
            "crates/noerelay-gateway/src/lib.rs (format_sse, stream handling, release_response)",
            "crates/noerelay-store/src/execution.rs (acquire_stream, renew_stream, release_stream)",
        ],
        risks=[
            "A rejected high-risk output leaks through an earlier chunk.",
            "A slow client or disconnect leaves an orphaned stream.",
        ],
        acceptance=[
            "T-API-002 passes event ordering, slow clients, disconnects, resumption, provider "
            "truncation, duplicate chunks, malformed frames, and cancellation.",
            "High-risk non-leakage holds: no rejected content in earlier chunks.",
        ],
        tasks=[
            "Implement the durable stream event model with sequence IDs and backpressure.",
            "Implement risk-class output gating and non-leakage.",
            "Implement resume cursors and disconnect cancellation.",
            "Add T-API-002 streaming fixtures.",
        ],
    ),
    dict(
        id="API-05",
        title="Stable admin/run/evidence/cost interfaces and generated SDK",
        outcome="Create versioned Rust administration APIs for runs, evidence, receipts, costs, and "
                "governance, and generate the client SDK from OpenAPI.",
        approach="Expose stable, versioned administration interfaces. Keep the outward response "
                "simple while governance metadata is available through extensions, headers, and "
                "run/receipt endpoints. Generate the TypeScript client from OpenAPI; the console "
                "never owns authority and never receives secrets after creation.",
        goals=[
            "Expose stable versioned admin/run/evidence/cost APIs.",
            "Keep governance metadata retrievable without changing the simple response.",
            "Generate the client SDK from OpenAPI.",
        ],
        non_goals=[
            "No authority owned by the console or SDK.",
            "No secret returned after creation.",
        ],
        components=[
            "crates/noerelay-gateway/src/admin.rs (administration endpoints)",
            "crates/noerelay-gateway/src/lib.rs (cost_report, receipt, governance_release_gate)",
        ],
        risks=[
            "An admin endpoint leaks a foreign tenant's run or receipt.",
            "The SDK is hand-written and drifts from the OpenAPI contract.",
        ],
        acceptance=[
            "Role-scoped API tests pass for runs, evidence, receipts, and costs.",
            "The generated SDK matches the OpenAPI contract.",
            "Secret redaction and pagination/export tests pass.",
        ],
        tasks=[
            "Implement the versioned admin/run/evidence/cost endpoints.",
            "Implement receipt and cost-report retrieval with scope checks.",
            "Generate the client SDK from OpenAPI.",
            "Add role-scoped and secret-redaction API tests.",
        ],
    ),
    # ---- REG / PROV ----
    dict(
        id="REG-01",
        title="Versioned model/provider/agent/tool registry and quarantine",
        outcome="Persist immutable model/provider/agent/tool revisions with provenance, times, "
                "explicit OpenRouter IDs, modalities, capabilities, limits, price snapshots, data "
                "policies, health, benchmark versions, and allowed roles; quarantine incomplete or "
                "stale entries.",
        approach="Store immutable revisions with fetched-at/valid-at times and provenance. "
                "Quarantine incomplete, stale, contradictory, or unevaluated entries. Activation "
                "points to a signed revision and never edits history.",
        goals=[
            "Persist immutable registry revisions with full capability metadata.",
            "Quarantine incomplete, stale, contradictory, or unevaluated entries.",
            "Activate only signed revisions.",
        ],
        non_goals=[
            "No unversioned or incomplete candidate routed.",
            "No editing of registry history.",
        ],
        components=[
            "crates/noerelay-store/src/registry.rs (registry repository)",
            "crates/noerelay-core/src/registry.rs (registry domain model)",
            "crates/noerelay-core/src/route_target.rs (route target model)",
        ],
        risks=[
            "An incomplete candidate is routed because a field defaulted instead of quarantining.",
            "Activation edits history instead of pointing to a new signed revision.",
        ],
        acceptance=[
            "Unversioned or incomplete candidates are quarantined.",
            "Activation points to a signed revision and never edits history.",
            "T-ROUTE-001 reads only admissible, complete registry entries.",
        ],
        tasks=[
            "Model the immutable registry revisions with full metadata.",
            "Implement quarantine for incomplete/stale/contradictory entries.",
            "Implement signed-revision activation.",
            "Add registry completeness and quarantine tests.",
        ],
    ),
    dict(
        id="PROV-01",
        title="Production OpenRouter adapter and explicit provider controls",
        outcome="Implement live OpenRouter adapters with explicit selected model/provider policy, "
                "restricted base URL, DNS/IP/redirect protections, TLS validation, timeouts, body/"
                "stream limits, rate-limit handling, sanitized errors, and usage capture.",
        approach="Always send the explicit selected model and bounded provider policy; never allow "
                "OpenRouter automatic routing to replace NoeRelay route authority. Test Chat and "
                "upstream Responses independently. Remote tests use protected non-production "
                "credentials, synthetic prompts, allowlisted models, and an explicit spend ceiling.",
        goals=[
            "Implement the live OpenRouter adapter with explicit provider controls.",
            "Enforce restricted egress, TLS, timeouts, and body/stream limits.",
            "Capture usage and sanitize errors.",
        ],
        non_goals=[
            "No OpenRouter automatic model selection replacing route authority.",
            "No implicit paid tests.",
        ],
        components=[
            "crates/noerelay-gateway/src/lib.rs (proxy_openai_request, validate_requested_model, "
            "upstream path selection)",
            "crates/noerelay-gateway/src/stub_provider.rs (test provider boundary)",
        ],
        risks=[
            "A redirect or DNS rebinding sends the request to an untrusted host.",
            "Usage is not captured, breaking cost reconciliation.",
        ],
        acceptance=[
            "Upstream requests always contain the explicit selected model and bounded policy.",
            "DNS/IP/redirect protections, TLS validation, and timeouts hold.",
            "Usage capture and sanitized errors are verified.",
        ],
        tasks=[
            "Implement the OpenRouter adapter with explicit selected-model forwarding.",
            "Implement restricted egress, TLS, timeout, and body/stream limits.",
            "Implement usage capture and sanitized errors.",
            "Add protected non-production remote tests with a spend ceiling.",
        ],
    ),
    dict(
        id="PROV-02",
        title="Bounded transport/capability/semantic/epistemic/specification fallbacks",
        outcome="Implement separate bounded fallback paths for endpoint transport, provider, "
                "capability, semantic repair, epistemic escalation, specification clarification, "
                "rejection, and human escalation, each with its own budget, evidence, and terminal "
                "code.",
        approach="Keep each fallback class distinct with its own attempt count, cost reservation, "
                "latency budget, evidence requirements, and terminal code. No fallback may weaken "
                "data policy, verifier independence, or acceptance criteria.",
        goals=[
            "Implement distinct, bounded fallback paths per failure class.",
            "Cost every attempt across fallback paths.",
            "Emit distinct failure events per class.",
        ],
        non_goals=[
            "No fallback weakening data policy, verifier independence, or acceptance.",
            "No unbounded fallback loop.",
        ],
        components=[
            "crates/noerelay-core/src/routing.rs (fallback policy)",
            "crates/noerelay-core/src/route_target.rs (route target and fallback targets)",
            "crates/noerelay-core/src/verification.rs (epistemic escalation)",
        ],
        risks=[
            "A semantic failure is retried as a transport failure, hiding the real cause.",
            "A fallback loop exceeds budget because the class is not bounded.",
        ],
        acceptance=[
            "The provider failure end-to-end scenario proves complete attempt costing and distinct "
            "failure events.",
            "Each fallback class has separate budgets, events, metrics, and terminal behavior.",
        ],
        tasks=[
            "Implement the distinct bounded fallback paths per failure class.",
            "Implement per-attempt cost reservation across fallbacks.",
            "Implement distinct failure events and terminal codes.",
            "Add the provider failure end-to-end scenario.",
        ],
    ),
    # ---- MEDIA ----
    dict(
        id="MEDIA-01",
        title="Vision and image-processing routes",
        outcome="Treat vision understanding and deterministic image processing as distinct "
                "capabilities with separate artifacts, policies, provenance, costs, and "
                "verification steps.",
        approach="Keep binary media outside JSON/database rows; bind content type, size, "
                "dimensions, parameters, provider/model revision, hashes, and retention. Route "
                "through the registry and provider plane with modality-aware admissibility.",
        goals=[
            "Route vision understanding and image processing as distinct capabilities.",
            "Bind media provenance, cost, and verification per capability.",
            "Keep binary media out of JSON/database rows.",
        ],
        non_goals=[
            "No media capability sharing an artifact or policy with text.",
            "No binary media stored in JSON/database rows.",
        ],
        components=[
            "crates/noerelay-core/src/wire.rs (multimodal content parts)",
            "crates/noerelay-core/src/registry.rs (modality capabilities)",
            "crates/noerelay-core/src/artifacts.rs (media artifact binding)",
        ],
        risks=[
            "A decompression bomb or oversized image is processed without limits.",
            "Media provenance is missing, breaking receipt binding.",
        ],
        acceptance=[
            "Supported modality fixtures pass size/type/decompression-bomb, unsupported-media, "
            "corrupt-artifact, provenance, cost, and release tests.",
        ],
        tasks=[
            "Model vision and image-processing as distinct capabilities in the registry.",
            "Implement media artifact binding with provenance and limits.",
            "Add modality fixtures for size/type/decompression and provenance.",
        ],
    ),
    dict(
        id="MEDIA-02",
        title="Explicit image generation/editing routes",
        outcome="Treat image generation and editing as explicit capabilities with separate "
                "artifacts, policies, provenance, costs, and safety/verification steps.",
        approach="Generate/edit through governed tool and provider paths with declared parameters. "
                "Bind transformation/generation parameters, provider/model revision, hashes, and "
                "retention. Apply safety and verification steps before acceptance.",
        goals=[
            "Route image generation and editing as explicit governed capabilities.",
            "Bind generation parameters, provenance, and cost.",
            "Apply safety and verification before acceptance.",
        ],
        non_goals=[
            "No implicit image generation outside a governed tool path.",
            "No unverified generated media accepted.",
        ],
        components=[
            "crates/noerelay-core/src/tools.rs (image tool definitions)",
            "crates/noerelay-core/src/tool_execution.rs (governed tool execution)",
            "crates/noerelay-core/src/artifacts.rs (generated media binding)",
        ],
        risks=[
            "A generated image bypasses safety/verification and is accepted.",
            "Generation parameters are not bound, breaking provenance.",
        ],
        acceptance=[
            "Image generation/editing fixtures pass provenance, cost, safety, and release tests.",
            "Generated media is bound with parameters, revision, and hashes.",
        ],
        tasks=[
            "Model image generation/editing as governed tool capabilities.",
            "Implement parameter binding and provenance for generated media.",
            "Apply safety and verification steps before acceptance.",
            "Add generation/editing fixtures.",
        ],
    ),
    # ---- TOOL / MCP / A2A ----
    dict(
        id="TOOL-01",
        title="Versioned tool registry, schemas, grants, and approvals",
        outcome="Create immutable tool revisions with input/output JSON Schema, risk class, "
                "side-effect class, required permissions, credential grants, egress allowlist, "
                "resource profile, timeout, idempotency semantics, approval policy, and verifier "
                "requirements.",
        approach="A model-visible description grants no authority. Rust validates the proposal and "
                "mints a narrowly scoped, expiring execution grant. Side-effecting tools require "
                "idempotency and risk-appropriate approval.",
        goals=[
            "Model immutable tool revisions with full authority metadata.",
            "Mint narrowly scoped, expiring execution grants.",
            "Require idempotency and approval for side-effecting tools.",
        ],
        non_goals=[
            "No model-visible description granting authority.",
            "No side-effecting tool without idempotency and approval.",
        ],
        components=[
            "crates/noerelay-core/src/tools.rs (tool registry and grants)",
            "crates/noerelay-core/src/tool_execution.rs (governed execution)",
            "crates/noerelay-core/src/budget.rs (resource and cost grants)",
        ],
        risks=[
            "A tool proposal executes before deterministic authorization.",
            "A grant is over-scoped or does not expire.",
        ],
        acceptance=[
            "A model-proposed tool call executes only after deterministic authorization.",
            "Replay and retry cannot duplicate a side effect.",
            "T-EXEC-002 passes tool schema/grant fixtures.",
        ],
        tasks=[
            "Model immutable tool revisions with authority metadata.",
            "Implement proposal validation and scoped expiring grants.",
            "Enforce idempotency and approval for side-effecting tools.",
            "Add T-EXEC-002 tool schema/grant fixtures.",
        ],
    ),
    dict(
        id="TOOL-02",
        title="Bounded code/tool sandbox and egress broker",
        outcome="Enforce a bounded sandbox for tool and code execution with CPU, memory, process, "
                "wall-clock, filesystem, network, DNS, output, artifact, and secret limits, and a "
                "default-deny egress broker.",
        approach="Mount only declared inputs; default-deny egress; broker credentials without "
                "placing them in prompts or environment dumps; isolate tenants and runs; collect "
                "deterministic execution evidence.",
        goals=[
            "Enforce resource, filesystem, network, DNS, output, and secret limits.",
            "Broker credentials with default-deny egress.",
            "Isolate tenants and runs and collect execution evidence.",
        ],
        non_goals=[
            "No secret placed in prompts or environment dumps.",
            "No egress outside the allowlist.",
        ],
        components=[
            "crates/noerelay-core/src/tool_execution.rs (sandboxed execution and egress broker)",
            "crates/noerelay-core/src/budget.rs (resource limits)",
        ],
        risks=[
            "A sandbox escape, SSRF, or DNS rebinding reaches the host or metadata service.",
            "A fork/process bomb or output flood exhausts resources.",
        ],
        acceptance=[
            "Escape, SSRF, DNS rebinding, metadata-service, fork/process bomb, disk/memory "
            "exhaustion, output flood, symlink/path traversal, secret access, and cross-run "
            "contamination suites fail closed.",
        ],
        tasks=[
            "Implement the bounded sandbox with all resource and output limits.",
            "Implement the default-deny egress broker and credential brokering.",
            "Implement tenant/run isolation and deterministic evidence collection.",
            "Add the sandbox adversarial suites (escape, SSRF, bomb, flood, traversal).",
        ],
    ),
    dict(
        id="MCP-01",
        title="Isolated MCP host, authorization, sessions, and reconciliation",
        outcome="Implement one isolated stateful MCP client connection per server/principal scope "
                "with capability negotiation, server allowlisting, audience-bound authorization, "
                "token non-forwarding, schema pinning, bounded reads, cancellation, and "
                "reconciliation.",
        approach="Translate MCP capabilities into tool proposals that still require Rust "
                "authorization. Never let advertised capability grant authority. Enforce session "
                "isolation and cleanup.",
        goals=[
            "Isolate MCP sessions per server and principal.",
            "Authorize MCP capability use through Rust.",
            "Reconcile sessions and prevent token forwarding.",
        ],
        non_goals=[
            "No advertised MCP capability granting authority.",
            "No token forwarding across sessions.",
        ],
        components=[
            "crates/noerelay-core/src/tools.rs (MCP capability translation)",
            "crates/noerelay-core/src/tool_execution.rs (MCP session execution)",
        ],
        risks=[
            "A malicious MCP schema or advertised capability escalates authority.",
            "A token is forwarded or a session is accessed cross-principal.",
        ],
        acceptance=[
            "T-EXEC-002 passes token confusion, advertised-capability escalation, cross-session "
            "access, malicious schemas/content, reconnect, and cancellation fixtures.",
        ],
        tasks=[
            "Implement isolated per-server/principal MCP sessions.",
            "Implement audience-bound authorization and token non-forwarding.",
            "Implement schema pinning, bounded reads, and reconciliation.",
            "Add T-EXEC-002 MCP adversarial fixtures.",
        ],
    ),
    dict(
        id="A2A-01",
        title="Agent registry, outbound dispatcher, trust roots, durable mapping",
        outcome="Retain the narrow Go inbound adapter while placing outbound delegation selection, "
                "trust policy, data envelope, contract binding, budgets, lineage, and acceptance in "
                "Rust, with an immutable agent registry and durable local/remote task mapping.",
        approach="Pin/signed Agent Card metadata where available and configured trust roots where "
                "signing is absent. Persist the local/remote task mapping before sending. Do not "
                "treat A2A messages as durable authority.",
        goals=[
            "Implement the immutable agent registry with trust roots.",
            "Implement the outbound Rust dispatcher with contract binding and budgets.",
            "Persist durable local/remote task mapping before sending.",
        ],
        non_goals=[
            "No A2A message treated as durable authority.",
            "No outbound delegation outside trust and budget policy.",
        ],
        components=[
            "crates/noerelay-core/src/agent_dispatch.rs (outbound dispatcher, trust, mapping)",
            "crates/noerelay-core/src/registry.rs (agent registry)",
            "services/a2a-adapter (narrow Go inbound adapter)",
        ],
        risks=[
            "A foreign-tenant or malicious agent card is trusted.",
            "A task is sent before the durable mapping is persisted, losing lineage.",
        ],
        acceptance=[
            "T-A2A-001 passes trust, scope, and durable-mapping tests.",
            "Outbound delegation is contract-bound, budgeted, and lineage-tracked.",
        ],
        tasks=[
            "Implement the immutable agent registry with trust roots.",
            "Implement the outbound Rust dispatcher with contract binding and budgets.",
            "Persist durable local/remote task mapping before sending.",
            "Add T-A2A-001 trust and mapping fixtures.",
        ],
    ),
    dict(
        id="A2A-02",
        title="A2A depth/fan-out/cycle/replay/cancel/reconnect/budget gates",
        outcome="Enforce depth, fan-out, total descendants, TTL, lineage cycle detection, "
                "per-branch budgets, data-class limits, cancellation, replay protection, and "
                "independent verification for agent delegation.",
        approach="Run the official A2A conformance kit plus malicious-card, loop, flood, "
                "foreign-tenant, reconnect, lost-message, poisoned-artifact, and verifier-collusion "
                "suites. Keep acceptance with an independent verifier and the Rust release gate.",
        goals=[
            "Enforce depth, fan-out, descendant, TTL, and cycle limits.",
            "Enforce per-branch budgets and data-class limits.",
            "Protect against replay, and verify independently.",
        ],
        non_goals=[
            "No delegation loop, flood, or replay accepted.",
            "No implementing agent satisfying its own high-risk acceptance.",
        ],
        components=[
            "crates/noerelay-core/src/agent_dispatch.rs (depth/fan-out/cycle/budget gates)",
            "services/a2a-adapter (conformance and adversarial harness entry)",
        ],
        risks=[
            "A delegation cycle or flood is not detected and exhausts budget.",
            "A replayed A2A message re-triggers a side effect.",
        ],
        acceptance=[
            "T-A2A-001 and the governed delegation end-to-end scenario pass.",
            "Loop, flood, replay, cancellation, reconnect, and foreign-tenant suites pass.",
        ],
        tasks=[
            "Implement depth/fan-out/descendant/TTL/cycle enforcement.",
            "Implement per-branch budgets and data-class limits.",
            "Implement replay protection and independent verification hooks.",
            "Run the A2A conformance kit and adversarial suites.",
        ],
    ),
    # ---- VER / MEM / CTX / LED ----
    dict(
        id="VER-01",
        title="Persistent risk-scaled verification DAG and verifier independence",
        outcome="Persist verification DAG definitions, check revisions, inputs, outputs, evidence, "
                "verifier identity/family, independence constraints, attempts, and terminal state, "
                "running deterministic checks before probabilistic review.",
        approach="Order checks deterministically with dependencies. Enforce verifier independence "
                "appropriate to risk (same-family-only cannot satisfy an independent-family gate). "
                "Keep every failure path non-accepted.",
        goals=[
            "Persist the verification DAG with check revisions and evidence.",
            "Run deterministic checks before probabilistic review.",
            "Enforce risk-appropriate verifier independence.",
        ],
        non_goals=[
            "No failure path silently marking a run accepted.",
            "No same-family-only review satisfying an independent gate.",
        ],
        components=[
            "crates/noerelay-core/src/verification.rs (verification DAG and independence)",
            "crates/noerelay-core/src/evaluator_result.rs (check results)",
        ],
        risks=[
            "A probabilistic review runs before deterministic checks, ordering the DAG wrongly.",
            "A same-family verifier satisfies an independence gate.",
        ],
        acceptance=[
            "T-VER-001 proves deterministic ordering, verifier independence, and every fail-closed "
            "terminal path.",
            "Check ordering and dependency tests are deterministic and replayable.",
        ],
        tasks=[
            "Model the persistent verification DAG with check revisions.",
            "Implement deterministic-before-probabilistic ordering.",
            "Implement risk-scaled verifier independence.",
            "Add T-VER-001 ordering and independence fixtures.",
        ],
    ),
    dict(
        id="VER-02",
        title="Bounded repair/fallback/clarification/rejection/escalation state machines",
        outcome="Implement bounded repair cycles with unchanged acceptance criteria and explicit "
                "value/cost limits, plus clarification, abstention, rejection, and escalation "
                "states.",
        approach="On verification failure, trigger bounded repair, fallback, clarification, "
                "rejection, or escalation. Repair cycles keep acceptance criteria unchanged and are "
                "bounded by value and cost. No failure path marks a run accepted.",
        goals=[
            "Implement bounded repair with unchanged acceptance criteria.",
            "Implement clarification, abstention, rejection, and escalation states.",
            "Bound repair by value and cost.",
        ],
        non_goals=[
            "No acceptance-criteria weakening during repair.",
            "No unbounded repair loop.",
        ],
        components=[
            "crates/noerelay-core/src/verification.rs (repair/escalation state machines)",
            "crates/noerelay-core/src/routing.rs (fallback integration)",
        ],
        risks=[
            "A repair cycle weakens the acceptance criteria to force a pass.",
            "A repair loop exceeds its value/cost bound.",
        ],
        acceptance=[
            "T-VER-001 proves bounded repair and that no failure path marks a run accepted.",
            "Clarification/abstention/rejection/escalation states are reachable and correct.",
        ],
        tasks=[
            "Implement bounded repair with unchanged acceptance criteria.",
            "Implement clarification, abstention, rejection, and escalation states.",
            "Enforce value and cost bounds on repair.",
            "Add T-VER-001 repair and fail-closed fixtures.",
        ],
    ),
    dict(
        id="VER-03",
        title="Human approval and signed external-attestation APIs",
        outcome="Provide human approval and signed external-attestation APIs that are scoped, "
                "expiring, replay-protected, and bound to the exact action/artifact hash.",
        approach="Bind each attestation to the approver identity, scope, action hash, artifact "
                "hash, and expiry. Enforce separation of duties so the implementing identity cannot "
                "approve its own high-risk work.",
        goals=[
            "Implement signed, scoped, expiring, replay-protected attestations.",
            "Bind attestations to exact action and artifact hashes.",
            "Enforce separation of duties for high-risk approval.",
        ],
        non_goals=[
            "No self-approval of high-risk work by the implementing identity.",
            "No replayed or out-of-scope attestation accepted.",
        ],
        components=[
            "crates/noerelay-core/src/verification.rs (approval state)",
            "crates/noerelay-core/src/receipt.rs (signed attestation binding)",
            "crates/noerelay-gateway/src/admin.rs (approval endpoints)",
        ],
        risks=[
            "An attestation is replayed against a different action or artifact.",
            "An approver approves their own high-risk implementation.",
        ],
        acceptance=[
            "T-VER-001 proves critical human approval and replay protection.",
            "Attestations bind to exact action/artifact hashes and expire correctly.",
        ],
        tasks=[
            "Implement signed, scoped, expiring attestation APIs.",
            "Bind attestations to action and artifact hashes.",
            "Enforce separation of duties for high-risk approval.",
            "Add replay and self-approval denial fixtures.",
        ],
    ),
    dict(
        id="MEM-01",
        title="Durable typed project/user/session epistemic graph",
        outcome="Persist typed facts, requirements, decisions, assumptions, observations, "
                "predictions, preferences, artifacts, and evidence/support/refutation edges with "
                "source handles, uncertainty, retention, and revisions, preserving four-valued "
                "epistemic states.",
        approach="Extract candidate claims without accepting them; corroboration and contradiction "
                "remain evidence operations. Preserve supported, refuted, both, and neither. Apply "
                "deletion and residency policies to graph nodes, embeddings, indexes, and caches.",
        goals=[
            "Persist the typed epistemic graph with evidence and support/refutation edges.",
            "Preserve four-valued epistemic states.",
            "Apply retention and residency to nodes, embeddings, indexes, and caches.",
        ],
        non_goals=[
            "No candidate claim accepted on extraction.",
            "No contradiction averaged away.",
        ],
        components=[
            "crates/noerelay-core/src/epistemic.rs (epistemic graph and four-valued state)",
            "crates/noerelay-core/src/context.rs (graph-driven context)",
        ],
        risks=[
            "A contradiction is merged into a single averaged claim.",
            "A deleted node leaves residue in an embedding index or cache.",
        ],
        acceptance=[
            "T-CTX-001 truth-table and merge tests preserve contradictions.",
            "Each claim type has valid transitions, evidence rules, retention, and rendering.",
        ],
        tasks=[
            "Model the typed epistemic graph with evidence and support/refutation edges.",
            "Implement four-valued state and contradiction preservation.",
            "Apply retention and residency to nodes, embeddings, indexes, and caches.",
            "Add T-CTX-001 merge and truth-table fixtures.",
        ],
    ),
    dict(
        id="CTX-01",
        title="Retrieval, provenance summaries, compaction, and tokenizer accounting",
        outcome="Compile context from durable graph state and the active contract using "
                "model-specific tokenizer accounting, requirement-driven retrieval, provenance-"
                "carrying summaries, protected nodes, and an auditable inclusion/omission manifest.",
        approach="Drive retrieval by active requirements and unresolved claims. Preserve protected "
                "nodes verbatim or addressable. Summaries carry provenance and uncertainty and never "
                "overwrite sources. Fail closed (clarify/abstain) under insufficient evidence.",
        goals=[
            "Compile bounded context from durable graph state.",
            "Preserve protected nodes under compaction.",
            "Produce provenance-carrying summaries with an inclusion/omission manifest.",
        ],
        non_goals=[
            "No summary overwriting source evidence.",
            "No accepted answer fabricated under insufficient evidence.",
        ],
        components=[
            "crates/noerelay-core/src/context.rs (retrieval, compaction, tokenizer accounting)",
            "crates/noerelay-core/src/epistemic.rs (protected nodes)",
            "crates/noerelay-gateway/src/lib.rs (compile_wire_context)",
        ],
        risks=[
            "Compaction drops a protected requirement, decision, or evidence handle.",
            "Token accounting overruns the selected model limit.",
        ],
        acceptance=[
            "T-CTX-001 property/differential tests prove token bounds, protected-node recovery, "
            "contradiction preservation, provenance expansion, deletion, and abstention.",
        ],
        tasks=[
            "Implement requirement-driven retrieval and tokenizer accounting.",
            "Implement protected-node preservation under compaction.",
            "Implement provenance-carrying summaries and the inclusion/omission manifest.",
            "Add T-CTX-001 property and differential fixtures.",
        ],
    ),
    dict(
        id="LED-01",
        title="Concurrent append/replay, artifact binding, signed exports, key rotation",
        outcome="Extend the ledger for concurrent scoped append, canonicalization versioning, "
                "artifact hashes, key rotation, public-key history, offline verification, replay, "
                "signed exports, and redacted audit views.",
        approach="Canonicalize and hash-link every authority-changing event. Store signing keys in "
                "the approved KMS/HSM. Make scope/filter completeness testable without storing "
                "chain-of-thought or secrets. Bind accepted runs to signed receipts.",
        goals=[
            "Support concurrent scoped append and canonicalization versioning.",
            "Bind artifacts and produce signed, offline-verifiable receipts.",
            "Support key rotation, replay, signed exports, and redacted audit views.",
        ],
        non_goals=[
            "No chain-of-thought or secrets stored in the ledger.",
            "No scope or secret leaked through an audit view.",
        ],
        components=[
            "crates/noerelay-core/src/ledger.rs (hash-chained ledger)",
            "crates/noerelay-core/src/receipt.rs (signed receipts)",
            "crates/noerelay-store/src/lib.rs (insert_ledger_event, receipt, cost_rollups)",
        ],
        risks=[
            "A mutation, reorder, splice, or key substitution is not detected.",
            "An audit view leaks a foreign scope or a secret.",
        ],
        acceptance=[
            "T-LED-001 detects mutation, deletion, reorder, duplicate, splice, artifact tamper, "
            "receipt tamper, key substitution, and scope leakage, including after restore.",
        ],
        tasks=[
            "Implement concurrent scoped append and canonicalization versioning.",
            "Implement signed receipts and offline verification.",
            "Implement key rotation, replay, signed exports, and redacted audit views.",
            "Add T-LED-001 tamper and scope-leakage fixtures.",
        ],
    ),
    # ---- COST / EVAL / REC ----
    dict(
        id="COST-01",
        title="Attempt-level measured/estimated/provider/billed cost ledger",
        outcome="Record immutable attempt-level token, request, tool, verifier, artifact, "
                "infrastructure, and human-review quantities, preserving expected, estimated, "
                "provider-reported, and billed sources separately with currency, pricing revision, "
                "rounding rule, and reconciliation status.",
        approach="Reserve worst-case admissible cost before each attempt and reconcile atomically "
                "after. Keep the four cost sources distinct so reconciliation is exact.",
        goals=[
            "Record immutable attempt-level cost quantities.",
            "Preserve the four cost sources separately.",
            "Reserve before and reconcile after each attempt.",
        ],
        non_goals=[
            "No overspend of a shared cap under concurrency.",
            "No blending of estimated and billed values.",
        ],
        components=[
            "crates/noerelay-core/src/usage.rs (usage and cost quantities)",
            "crates/noerelay-core/src/budget.rs (reservation and reconciliation)",
            "crates/noerelay-store/src/lib.rs (cost_rollups)",
        ],
        risks=[
            "Concurrent requests overspend a shared cap because reservation is not atomic.",
            "A late billing event is not reconciled, skewing totals.",
        ],
        acceptance=[
            "T-COST-001 passes concurrency, overflow, rounding, and reservation fixtures.",
            "Reconciliation separates estimated, provider-reported, and billed values.",
        ],
        tasks=[
            "Model immutable attempt-level cost quantities with four sources.",
            "Implement atomic cost reservation and reconciliation.",
            "Add T-COST-001 concurrency, overflow, and rounding fixtures.",
        ],
    ),
    dict(
        id="COST-02",
        title="Scoped rollups, invoices, tradeoffs, and route regret",
        outcome="Compute complete scoped rollups, invoices, quality/cost/latency tradeoffs, and "
                "route regret only against candidates admissible at the historical decision using "
                "pinned registry/policy/features.",
        approach="Roll up by organization, project, environment, user, API key, run, model, "
                "provider, agent, tool, cohort, and time. Compute regret against historically "
                "admissible alternatives. Keep feedback types distinct.",
        goals=[
            "Compute complete scoped rollups and invoices.",
            "Compute quality/cost/latency tradeoffs and route regret.",
            "Keep feedback types distinct.",
        ],
        non_goals=[
            "No regret computed against non-admissible historical candidates.",
            "No feedback type conflated (a thumbs-up is not proof of correctness).",
        ],
        components=[
            "crates/noerelay-core/src/analytics.rs (rollups and regret)",
            "crates/noerelay-core/src/usage.rs (source quantities)",
            "crates/noerelay-gateway/src/lib.rs (cost_report)",
        ],
        risks=[
            "A rollup total does not equal the source attempt records within rounding rules.",
            "Route regret uses a candidate that was not admissible at the decision time.",
        ],
        acceptance=[
            "T-COST-001 passes aggregation conservation, late billing, correction, refund, "
            "currency, retry/fallback, and invoice reconciliation fixtures.",
            "Cohort reports compare chosen and admissible alternatives with uncertainty.",
        ],
        tasks=[
            "Implement scoped rollups and invoices.",
            "Implement tradeoff and route-regret computation against admissible alternatives.",
            "Keep feedback types distinct in the model.",
            "Add T-COST-001 aggregation and invoice reconciliation fixtures.",
        ],
    ),
    dict(
        id="EVAL-01",
        title="Versioned cohort/benchmark/harness registry and signed results",
        outcome="Build the evaluation plane (primarily Python) through immutable manifests and "
                "Rust-controlled promotion APIs, versioning dataset/cohort, task, metric, harness, "
                "prompt, model, provider, tool, verifier, environment, seed, and code revision, with "
                "signed result artifacts and uncertainty/calibration metrics.",
        approach="Use hidden/mutation/adversarial suites to resist gaming. A model name without its "
                "tested harness is not a transferable result. Promotion is controlled by Rust.",
        goals=[
            "Version every evaluation dimension (cohort, harness, model, seed, code).",
            "Store signed result artifacts with uncertainty and calibration.",
            "Resist gaming with hidden/mutation/adversarial suites.",
        ],
        non_goals=[
            "No transferable result without its tested harness.",
            "No promotion outside the Rust-controlled API.",
        ],
        components=[
            "crates/noerelay-core/src/evaluator_ingestion.rs (SpecKitHook outcome ingestion)",
            "crates/noerelay-core/src/evaluator_result.rs (signed results)",
            "crates/noerelay-core/src/analytics.rs (cohort statistics)",
            "bindings/python (evaluation plane)",
        ],
        risks=[
            "A result is attributed to a model without its harness, overclaiming transferability.",
            "An evaluation is gamed because only visible suites are used.",
        ],
        acceptance=[
            "Every launch cohort has a signed benchmark manifest and results.",
            "Calibration and hidden anti-gaming tests are included.",
            "Promotion occurs only through the Rust-controlled API.",
        ],
        tasks=[
            "Implement the versioned evaluation manifest and registry.",
            "Implement signed result artifacts with uncertainty/calibration.",
            "Add hidden/mutation/adversarial suites.",
            "Wire Rust-controlled promotion.",
        ],
    ),
    dict(
        id="REC-01",
        title="Advisory recommendations with uncertainty/freshness/coverage/reasons",
        outcome="Compute advisory recommendations in Rust from scoped versioned observations, "
                "reporting cohort coverage, sample size, lower confidence bound, uncertainty, "
                "freshness, drift, cost, latency, and reasons for abstention, keeping hard "
                "constraints first.",
        approach="Learn only from versioned, scoped observations and remain advisory until signed "
                "promotion. Sparse or stale data produces abstention or qualified advice, never "
                "false certainty.",
        goals=[
            "Compute advisory recommendations from scoped versioned observations.",
            "Report uncertainty, coverage, freshness, and abstention reasons.",
            "Keep hard constraints first and remain advisory until promotion.",
        ],
        non_goals=[
            "No online statistic mutating an active policy or acceptance threshold.",
            "No false certainty from sparse or stale data.",
        ],
        components=[
            "crates/noerelay-core/src/recommendation.rs (advisory recommendations)",
            "crates/noerelay-core/src/ranking.rs (advisory ranking)",
        ],
        risks=[
            "A recommendation mutates an active policy before signed promotion.",
            "Sparse data produces overconfident advice.",
        ],
        acceptance=[
            "T-ROUTE-002 proves cohort isolation, sparse/stale abstention, and advisory-only "
            "behavior.",
            "Recommendations report uncertainty, coverage, freshness, and reasons.",
        ],
        tasks=[
            "Implement advisory recommendations from scoped versioned observations.",
            "Implement uncertainty/coverage/freshness/abstention reporting.",
            "Enforce advisory-only behavior (no policy mutation).",
            "Add T-ROUTE-002 advisory and abstention fixtures.",
        ],
    ),
    dict(
        id="REC-02",
        title="Shadow/canary/promotion/drift/rollback controls",
        outcome="Implement shadow decisions, deterministic canary allocation, spending/risk "
                "envelopes, signed promotion, rollback, and automatic disable triggers.",
        approach="Promote only via signed evaluation. Trigger automatic disable on policy "
                "violations, unsafe accepts, tenant leaks, duplicate effects, calibration breaches, "
                "unexplained cost spikes, or evidence failures. Roll back by activating a previous "
                "signed revision.",
        goals=[
            "Implement shadow and deterministic canary allocation.",
            "Implement signed promotion and rollback.",
            "Implement automatic disable triggers.",
        ],
        non_goals=[
            "No promotion without signed evaluation.",
            "No rollback by editing history.",
        ],
        components=[
            "crates/noerelay-core/src/recommendation.rs (canary and promotion)",
            "crates/noerelay-core/src/ranking.rs (shadow decisions)",
            "crates/noerelay-core/src/governance.rs (signed revision activation)",
        ],
        risks=[
            "A canary exceeds its spending or risk envelope.",
            "A promotion is not reversible because history was edited.",
        ],
        acceptance=[
            "T-ROUTE-002 proves promotion independence, canary bounds, and rollback.",
            "Automatic disable triggers fire on the defined violation classes.",
        ],
        tasks=[
            "Implement shadow decisions and deterministic canary allocation.",
            "Implement signed promotion and rollback to a previous revision.",
            "Implement automatic disable triggers.",
            "Add T-ROUTE-002 canary and rollback fixtures.",
        ],
    ),
    # ---- UI ----
    dict(
        id="UI-01",
        title="Operator console for onboarding, runs, evidence, cost, approvals, policy",
        outcome="Build a TypeScript operator console for tenant/project onboarding, key metadata and "
                "rotation, policies/quotas, registry status, runs/steps/attempts, evidence/receipts, "
                "costs, route reasons/regret, approvals, recommendations, audit exports, kill "
                "switches, deletion/export requests, and operational status.",
        approach="Generate the TypeScript client from OpenAPI. The console never owns authority and "
                "never receives secrets after creation. Pass role-scoped browser/API end-to-end, "
                "accessibility, secret-redaction, pagination/export, and pilot usability tests.",
        goals=[
            "Build the operator console over the generated SDK.",
            "Keep the console non-authoritative and secret-free after creation.",
            "Pass accessibility, redaction, and usability tests.",
        ],
        non_goals=[
            "No authority owned by the console.",
            "No secret displayed after creation.",
        ],
        components=[
            "crates/noerelay-gateway/src/admin.rs (console backend APIs)",
            "tests/test_dashboard_ui.py (dashboard UI tests)",
            "tests/dashboard_requirements.py (dashboard requirements)",
        ],
        risks=[
            "The console displays a secret after creation.",
            "A role-scoped view leaks a foreign tenant's data.",
        ],
        acceptance=[
            "Role-scoped browser/API end-to-end tests pass.",
            "Accessibility, secret-redaction, and pagination/export tests pass.",
            "Pilot usability tasks pass.",
        ],
        tasks=[
            "Build the console over the generated OpenAPI SDK.",
            "Implement onboarding, runs, evidence, cost, approvals, and policy views.",
            "Add role-scoped end-to-end and secret-redaction tests.",
            "Add accessibility and pilot usability checks.",
        ],
    ),
    # ---- OPS ----
    dict(
        id="OPS-01",
        title="Liveness/readiness/metrics/traces/logs/events and SLO dashboards",
        outcome="Expose separate liveness and dependency-aware readiness, Prometheus-compatible "
                "metrics, OpenTelemetry traces, structured redacted logs, sanitized audit/security "
                "events, correlation, and SLO/error-budget dashboards.",
        approach="Keep liveness separate from dependency-aware readiness so a dependency failure "
                "removes readiness without a false liveness failure. Disable prompt/output capture "
                "by default; capture only through explicit redacted tenant policy.",
        goals=[
            "Expose separate liveness and dependency-aware readiness.",
            "Emit metrics, traces, redacted logs, and correlated events.",
            "Provide SLO/error-budget dashboards.",
        ],
        non_goals=[
            "No prompt/output captured by default.",
            "No dependency failure causing a false liveness failure.",
        ],
        components=[
            "crates/noerelay-gateway/src/lib.rs (ready, health handlers)",
            "crates/noerelay-gateway/src/main.rs (server bootstrap and probes)",
        ],
        risks=[
            "A dependency failure is reported as a liveness failure, triggering a needless restart.",
            "Prompt/output content is captured without an explicit redacted policy.",
        ],
        acceptance=[
            "T-OPS-001 passes probes and telemetry correlation/redaction.",
            "Dependency failure removes readiness without a false liveness failure.",
        ],
        tasks=[
            "Implement separate liveness and dependency-aware readiness.",
            "Implement metrics, traces, redacted logs, and correlation.",
            "Add SLO/error-budget dashboards.",
            "Add T-OPS-001 probe and redaction fixtures.",
        ],
    ),
    dict(
        id="OPS-02",
        title="Scoped kill switches and safe rollback",
        outcome="Implement audited kill switches globally and by tenant, project, provider, model, "
                "agent, tool, policy, and capability, stopping new and cached work and propagating "
                "to workers, with rollback by activating a previous signed revision.",
        approach="Define handling of in-flight work for each switch. Roll back by activating a "
                "previous signed revision rather than editing history. Record audit evidence for "
                "every switch action.",
        goals=[
            "Implement audited kill switches at every scope.",
            "Stop new and cached work and propagate to workers.",
            "Roll back by activating a previous signed revision.",
        ],
        non_goals=[
            "No rollback by editing history.",
            "No kill switch without audit evidence.",
        ],
        components=[
            "crates/noerelay-core/src/governance.rs (signed revision activation)",
            "crates/noerelay-store/src/lifecycle.rs (scope state)",
        ],
        risks=[
            "A kill switch does not stop cached work, so it keeps executing.",
            "A rollback edits history instead of activating a previous revision.",
        ],
        acceptance=[
            "T-OPS-001 kill-switch tests stop new/cached work and produce audit evidence.",
            "Rollback activates a previous signed revision without editing history.",
        ],
        tasks=[
            "Implement audited kill switches at every scope.",
            "Implement propagation to workers and in-flight handling.",
            "Implement rollback via previous signed revision activation.",
            "Add T-OPS-001 kill-switch fixtures.",
        ],
    ),
    dict(
        id="OPS-03",
        title="Backup, PITR, restore, artifact reconciliation, DR exercises",
        outcome="Automate encrypted backups, point-in-time recovery, object-store versioning/"
                "replication, restore into a clean environment, reconciliation, ledger/receipt "
                "verification, queue/outbox recovery, and key-availability procedures, with "
                "scheduled drills recording measured RPO/RTO.",
        approach="Restore into a clean environment and verify idempotent replay and receipts "
                "inside RPO/RTO. Run scheduled drills and record measured RPO/RTO.",
        goals=[
            "Automate encrypted backups and PITR.",
            "Restore into a clean environment and verify receipts.",
            "Run scheduled DR drills recording measured RPO/RTO.",
        ],
        non_goals=[
            "No restore that fails ledger/receipt verification.",
            "No unmeasured RPO/RTO claim.",
        ],
        components=[
            "crates/noerelay-store/src/lib.rs (ledger and receipt verification)",
            "deploy/ (container and orchestration manifests)",
            "docs/runbooks.md (backup/restore and incident procedures)",
        ],
        risks=[
            "A restore succeeds but ledger/receipt verification fails, masking corruption.",
            "RPO/RTO is claimed but never measured by a drill.",
        ],
        acceptance=[
            "T-OPS-001 backup, restore, replay, and post-restore ledger verification pass.",
            "A documented restore drill meets declared RPO/RTO and validates receipts afterward.",
        ],
        tasks=[
            "Automate encrypted backups and PITR.",
            "Implement clean-environment restore with receipt verification.",
            "Run scheduled DR drills and record measured RPO/RTO.",
            "Add T-OPS-001 restore and post-restore verification fixtures.",
        ],
    ),
    # ---- SEC ----
    dict(
        id="SEC-01",
        title="Threat-model-driven application/API/tenant/sandbox hardening",
        outcome="Maintain a data-flow and trust-boundary threat model and run adversarial auth/"
                "authz, parser, injection, SSRF, egress, tenant crossover, quota, ledger, artifact, "
                "sandbox, agent, stream, and secret-redaction suites, tracking every finding to "
                "closure.",
        approach="Cover public APIs, OpenRouter, PostgreSQL, object store, queue, OIDC, KMS, "
                "tools/sandbox, MCP, A2A, Python workers, console, CI/CD, telemetry, and operators. "
                "GA permits no open critical/high finding.",
        goals=[
            "Maintain the data-flow and trust-boundary threat model.",
            "Run the full adversarial suite set.",
            "Track every finding with severity, owner, remediation, and acceptance.",
        ],
        non_goals=[
            "No open critical/high finding at release.",
            "No finding closed without retest.",
        ],
        components=[
            "docs/threat-model.md (trust boundaries and data flows)",
            "crates/noerelay-gateway/src/lib.rs (authorized, constant_time_equal, auth boundary)",
            "crates/noerelay-store/src/ (tenant and ledger boundaries)",
        ],
        risks=[
            "A tenant-crossover or SSRF vector is missed by the suite set.",
            "A finding is closed without retest evidence.",
        ],
        acceptance=[
            "T-SEC-001 auth bypass, parser abuse, injection, SSRF, tenant crossover, and quota "
            "abuse suites pass.",
            "No critical/high finding remains open at release.",
        ],
        tasks=[
            "Maintain the data-flow and trust-boundary threat model.",
            "Implement and run the full adversarial suite set.",
            "Track findings to closure with retest evidence.",
            "Add T-SEC-001 adversarial fixtures.",
        ],
    ),
    dict(
        id="SEC-02",
        title="SBOM, licenses, scans, provenance, and signing",
        outcome="Pin dependencies and base images; scan source, secrets, dependencies, licenses, "
                "containers, and IaC; generate SPDX/CycloneDX SBOMs; produce SLSA/in-toto "
                "provenance; sign images, binaries, wheels, manifests, and release bundles; and "
                "verify signatures at deployment.",
        approach="Separate untrusted pull-request workflows from protected credentials. Publish "
                "multi-architecture artifacts. Block known disallowed risk in CI.",
        goals=[
            "Generate SBOMs and provenance for every artifact.",
            "Sign and verify images, binaries, wheels, and release bundles.",
            "Scan source, secrets, dependencies, licenses, containers, and IaC.",
        ],
        non_goals=[
            "No unsigned artifact deployed.",
            "No known disallowed risk passing CI.",
        ],
        components=[
            "xtask/ (build automation and evidence)",
            ".github/ (CI workflows)",
            "deploy/docker/Dockerfile (image build)",
            "deploy/ (IaC and orchestration)",
        ],
        risks=[
            "An unsigned or unprovenanced artifact is deployed.",
            "A pull-request workflow accesses protected credentials.",
        ],
        acceptance=[
            "T-SEC-001 dependency audit, SBOM, provenance, and signature gates pass.",
            "CI produces attributable artifacts and blocks known disallowed risk.",
        ],
        tasks=[
            "Generate SPDX/CycloneDX SBOMs and SLSA/in-toto provenance.",
            "Sign images, binaries, wheels, manifests, and release bundles.",
            "Verify signatures at deployment.",
            "Add T-SEC-001 SBOM/provenance/signature gate fixtures.",
        ],
    ),
    # ---- COMP ----
    dict(
        id="COMP-01",
        title="Versioned compliance framework mappings",
        outcome="Create versioned, profile-specific control mappings listing framework/control "
                "version, applicability, implementation, observed evidence, gaps, owner, reviewer, "
                "and next review date, as evidence aids rather than legal-certification claims.",
        approach="Include SOC 2/ISO 27001/privacy mappings only when selected by authorized "
                "reviewers. Never print certified or compliant solely from a passing automated "
                "check.",
        goals=[
            "Create versioned, profile-specific control mappings.",
            "Tie each control to observed evidence, gaps, owner, and review date.",
            "Keep mappings as evidence aids, not certification claims.",
        ],
        non_goals=[
            "No certified or compliant claim from an automated check alone.",
            "No framework mapping included without authorized reviewer selection.",
        ],
        components=[
            "docs/ (compliance mapping documents)",
            "xtask/ (evidence linkage for controls)",
        ],
        risks=[
            "A mapping claims certification without observed evidence.",
            "A control has no owner or review date.",
        ],
        acceptance=[
            "T-COMP-001 versioned framework mapping and gap disclosure fixtures pass.",
            "Reports identify framework version, controls, evidence, gaps, owner, and review date.",
        ],
        tasks=[
            "Create the versioned, profile-specific control mappings.",
            "Tie each control to observed evidence, gaps, owner, and review date.",
            "Add T-COMP-001 mapping and gap-disclosure fixtures.",
        ],
    ),
    dict(
        id="COMP-02",
        title="Data inventory and tested retention/residency/deletion/hold/export",
        outcome="Complete the data inventory and privacy/legal review, vendor/subprocessor "
                "inventory, data processing terms, retention/residency/deletion decisions, "
                "incident commitments, and customer-responsibility disclosures, with tested "
                "lifecycle behavior.",
        approach="Simulate and test lifecycle policies per tenant/project. Document what cannot be "
                "deleted immediately and why. Complete privacy/legal review and vendor inventory.",
        goals=[
            "Complete the data inventory and vendor/subprocessor inventory.",
            "Test retention, residency, deletion, legal hold, and export per tenant/project.",
            "Complete privacy/legal review and disclosures.",
        ],
        non_goals=[
            "No lifecycle behavior claimed without a test.",
            "No unreviewed vendor or subprocessor.",
        ],
        components=[
            "crates/noerelay-store/src/lifecycle.rs (retention, hold, deletion, export)",
            "crates/noerelay-store/src/artifacts.rs (artifact retention)",
        ],
        risks=[
            "A residency or deletion policy is not enforced for a derived store.",
            "A vendor/subprocessor is missing from the inventory.",
        ],
        acceptance=[
            "T-COMP-001 retention, residency, deletion, legal-hold, and export fixtures pass.",
            "Policy simulation and lifecycle tests prove configured behavior.",
        ],
        tasks=[
            "Complete the data and vendor/subprocessor inventory.",
            "Implement and test retention, residency, deletion, hold, and export.",
            "Complete privacy/legal review and customer-responsibility disclosures.",
            "Add T-COMP-001 lifecycle fixtures.",
        ],
    ),
    # ---- REL ----
    dict(
        id="REL-01",
        title="Quantitative load/soak/fault/chaos/SLO evidence",
        outcome="Publish measurable SLO, load, soak, fault-injection, and chaos results for the "
                "supported deployment profile, meeting declared concurrency, latency, error, "
                "durability, RPO, and RTO targets.",
        approach="Run the load/soak/fault/chaos suites in a protected environment. Publish "
                "measured methodology, environment, raw results, summaries, regressions, and "
                "artifact hashes. Targets are not evidence; measured results are.",
        goals=[
            "Run load, soak, fault-injection, and chaos suites.",
            "Meet declared concurrency, latency, error, durability, RPO, and RTO targets.",
            "Publish measured methodology, raw results, and artifact hashes.",
        ],
        non_goals=[
            "No target treated as evidence without a measured result.",
            "No network-dependent suite run outside a protected environment.",
        ],
        components=[
            "xtask/ (evidence recording for release metrics)",
            "benchmarks/ (load and soak harnesses)",
        ],
        risks=[
            "A target is reported as met without a measured result.",
            "A network-dependent suite runs without a spend ceiling.",
        ],
        acceptance=[
            "T-REL-001 load/soak/fault objectives pass for the named profile.",
            "Results meet declared concurrency, latency, error, durability, RPO, and RTO targets.",
        ],
        tasks=[
            "Run the load, soak, fault-injection, and chaos suites.",
            "Publish measured methodology, raw results, and artifact hashes.",
            "Verify results meet the declared targets.",
            "Add T-REL-001 release-metric evidence.",
        ],
    ),
    dict(
        id="REL-02",
        title="Independent security/privacy/legal/product/evaluation/ops review",
        outcome="Obtain independent product, engineering, security, evaluation, and operations "
                "sign-off evidence for the release candidate.",
        approach="Run independent reviews against every MUST requirement and verification row. "
                "Enumerate missing, stale, claimed-only, contradicted, or non-independent evidence. "
                "A missing approval leaves the candidate non-GA.",
        goals=[
            "Obtain independent sign-off from every required function.",
            "Enumerate and close evidence gaps before sign-off.",
            "Keep the candidate non-GA until all approvals are present.",
        ],
        non_goals=[
            "No sign-off from a non-independent reviewer.",
            "No GA with a missing approval.",
        ],
        components=[
            "docs/ (review records and sign-off evidence)",
            "evidence/ (independent review artifacts)",
        ],
        risks=[
            "A review is not independent (the implementer reviews their own work).",
            "A stale or claimed-only evidence item is signed off.",
        ],
        acceptance=[
            "T-REL-001 approval evidence is complete for every required function.",
            "Missing approval leaves the release candidate non-GA.",
        ],
        tasks=[
            "Run independent security, privacy, legal, product, evaluation, and ops reviews.",
            "Enumerate and close missing/stale/claimed-only/contradicted evidence.",
            "Record signed approvals tied to exact source and artifact digests.",
            "Add T-REL-001 approval evidence.",
        ],
    ),
    dict(
        id="REL-03",
        title="Seven-consecutive-day controlled pilot",
        outcome="Run a seven-consecutive-day controlled pilot for the named customer-like cohort "
                "with a spend ceiling and no unresolved launch blocker.",
        approach="Operate the named profile for seven consecutive days under a spend and error "
                "budget. Track launch blockers and resolve them. Rerun the regression suite at the "
                "end of the window.",
        goals=[
            "Run a seven-consecutive-day controlled pilot.",
            "Stay within the approved spend and error budget.",
            "Close all launch blockers and rerun the regression suite.",
        ],
        non_goals=[
            "No pilot day with an unresolved launch blocker.",
            "No spend beyond the approved ceiling.",
        ],
        components=[
            "docs/ (pilot plan and daily records)",
            "evidence/ (pilot telemetry and blocker log)",
        ],
        risks=[
            "An unresolved launch blocker is carried past the seven-day window.",
            "Spend exceeds the approved ceiling during the pilot.",
        ],
        acceptance=[
            "Seven consecutive days with no unresolved launch blocker and within budget.",
            "The regression suite is rerun and passes at the end of the window.",
        ],
        tasks=[
            "Prepare the named customer-like cohort and spend ceiling.",
            "Operate the pilot for seven consecutive days with daily records.",
            "Resolve launch blockers and rerun the regression suite.",
            "Record the pilot evidence bundle.",
        ],
    ),
    dict(
        id="REL-04",
        title="Immutable GA bundle, approvals, deployment, and rollback",
        outcome="Produce the immutable GA evidence bundle with exact artifact/source approvals, "
                "deployment, and a tested rollback package, recorded as a signed release record.",
        approach="Assemble the complete evidence bundle with exact source and artifact digests. "
                "Record the signed release record. Prepare and test the rollback package. Identify "
                "remaining external/customer responsibilities and non-goals.",
        goals=[
            "Assemble the immutable GA evidence bundle with exact digests.",
            "Record the signed release record with all approvals.",
            "Prepare and test the rollback package.",
        ],
        non_goals=[
            "No GA bundle with a missing or stale artifact digest.",
            "No release record without exact source and artifact approvals.",
        ],
        components=[
            "xtask/ (evidence bundle validation)",
            "evidence/ (GA evidence bundle)",
            "deploy/ (deployment and rollback manifests)",
        ],
        risks=[
            "A stale or reused evidence artifact is included in the GA bundle.",
            "The rollback package is not tested before GA.",
        ],
        acceptance=[
            "T-REL-001 complete evidence bundle, approvals, non-goals, and external-responsibility "
            "disclosure pass.",
            "The release record identifies remaining external/customer responsibilities and "
            "non-goals.",
        ],
        tasks=[
            "Assemble the immutable GA evidence bundle with exact digests.",
            "Record the signed release record with all approvals.",
            "Prepare and test the rollback package.",
            "Disclose remaining external/customer responsibilities and non-goals.",
        ],
    ),
    # ---- Phase 2: RTK, local LLM stack, operator tooling (manifest v1.1.0) ----
    dict(
        id="RTK-01",
        title="RTK native compression engine and PyO3 bridge",
        outcome="Ship the Rust-native context condenser (`noerelay-compact` in `rtk/`) as the "
                "authoritative compression engine for the Python gateway, with a Maturin/PyO3 "
                "bridge and a documented Python fallback, so compression is fast, deterministic, "
                "and auditable (NR-RTK-001, NR-RTK-002).",
        approach="Build `rtk/` as the standalone PyO3 cdylib (maturin) and wire the existing "
                 "`reference/gateway/rtk_bridge.py` import-or-fallback pattern into the gateway "
                 "pipeline after route selection; align the bridge to the crate's dict contract "
                 "(messages key, strategy, target_ratio, min_tokens); record compression metrics "
                 "(strategy, token counts, ratio, tokens saved, duration) into run metadata and "
                 "ledger-adjacent events; keep the Python `compression.py` as the documented "
                 "fallback path and prove both paths pass the same contract tests.",
        goals=[
            "Produce a buildable `noerelay-compact` native module from `rtk/` (maturin, pyo3).",
            "Route gateway compression through the native bridge with a null-signal fallback.",
            "Record per-pass compression metrics with protected-node preservation.",
            "Keep the Python fallback behaviorally equivalent for the shared contract tests.",
        ],
        non_goals=[
            "No changes to the Rust gateway core in this package (the bridge is the Python-side surface).",
            "No new compression strategies beyond dedup/prune/summarize/auto already defined.",
        ],
        components=[
            "rtk/Cargo.toml (noerelay-compact cdylib, pyo3)",
            "rtk/src/lib.rs (estimate_tokens_rust, dedup/prune/auto/compress_messages_rust)",
            "rtk/pyproject.toml (maturin build)",
            "reference/gateway/rtk_bridge.py (import-or-fallback bridge)",
            "reference/gateway/compression.py (documented Python fallback)",
            "tests/test_compression.py, tests/test_compression_cache.py, tests/test_compression_profiler.py",
        ],
        risks=[
            "PyO3 version skew between rtk (0.21) and the workspace (0.29) breaks the build; keep rtk standalone or pin a compatible pyo3.",
            "Stale `rtk/target/` artifacts from a previous machine path mislead the build.",
            "Native and fallback paths drift, so a fixture passes one path but not the other.",
        ],
        acceptance=[
            "`maturin build` in `rtk/` produces an importable `noerelay_compact` module.",
            "`is_native_available()` is true when built; the bridge returns None (fallback signal) when not.",
            "Compression contract tests pass with the native module installed and with it absent.",
            "Each compression pass emits strategy, token counts, ratio, tokens saved, and duration, and protected nodes survive.",
        ],
        tasks=[
            "Align `rtk/` pyo3 version and build it standalone with maturin.",
            "Verify `rtk_bridge.py` maps the crate's dict contract and returns None when native is missing.",
            "Wire the gateway pipeline to prefer native compression after route selection.",
            "Add/extend tests proving native and fallback parity and metric emission.",
            "Record T-RTK-001 evidence for NR-RTK-001/NR-RTK-002.",
        ],
    ),
    dict(
        id="LLM-01",
        title="Two-model local plane, GPU priority, and quant benchmark",
        outcome="Make the local profile a two-model plane (fast `gpt-oss-20b`, hard `qwen3.8-27b`) "
                "with the operator's primary GPU (RTX 4070 SUPER) as the preferred tensor owner, "
                "a recorded quant benchmark for `gpt-oss-20b`, and a machine-readable supported-"
                "model list (NR-LLM-001, NR-LLM-002, NR-LLM-003).",
        approach="Extend the model catalog in `src/noerelay/models.py` with `gpt-oss-20b` (three "
                 "quants) and tier metadata (fast/hard) plus VRAM guidance; fix "
                 "`_recommend_split` in `src/noerelay/provision.py` so the display/primary GPU "
                 "receives the larger tensor share (e.g. 15,10 on the reference host instead of "
                 "10,15); add a benchmark runner that loads each quant and records tokens/s, TTFT, "
                 "VRAM, and a quality proxy into `evidence/`; expose the supported-model list "
                 "through the catalog and the CLI.",
        goals=[
            "Add `gpt-oss-20b` (Q4_K_M/Q5_K_M/Q6_K) to the catalog with tier and VRAM metadata.",
            "Make the primary/display GPU the preferred tensor owner in the generated split.",
            "Record a per-quant benchmark artifact and derive the default quant from it.",
            "Expose a machine-readable supported-model list.",
        ],
        non_goals=[
            "No cloud routing changes; this is the local llama-server plane only.",
            "No automatic model self-upgrade; selection stays explicit and auditable.",
        ],
        components=[
            "src/noerelay/models.py (MODEL_CATALOG, tier/VRAM metadata)",
            "src/noerelay/provision.py (_recommend_split, _pick_model, _pick_ctx)",
            "src/noerelay/system_info.py (GPU detection, display GPU flag)",
            "benchmarks/ (task sets for the local benchmark)",
            "evidence/ (recorded per-quant benchmark artifact)",
        ],
        risks=[
            "Split weighting regresses to favoring the secondary GPU on hosts with different VRAM order.",
            "Benchmark artifacts are not reproducible (missing build tag, ctx, or seed).",
            "Catalog metadata drifts from what the provisioner actually loads.",
        ],
        acceptance=[
            "On the reference two-GPU host the generated tensor split assigns the 4070 SUPER the larger share.",
            "Both `gpt-oss-20b` and `qwen3.8-27b` appear in the catalog with distinct tier metadata.",
            "A routing fixture picks the fast tier by default and the hard tier only under the declared escalation.",
            "A benchmark artifact under `evidence/` records per-quant results and the chosen quant.",
        ],
        tasks=[
            "Add `gpt-oss-20b` quants and tier/VRAM metadata to `models.py`.",
            "Fix `_recommend_split` to weight the primary/display GPU first.",
            "Implement the local quant benchmark runner and record results under `evidence/`.",
            "Surface the supported-model list via the catalog and `noerelay models`.",
            "Record T-LLM-001/002/003 evidence for NR-LLM-001/002/003.",
        ],
    ),
    dict(
        id="LLM-02",
        title="Python-native server lifecycle and master YAML config",
        outcome="Replace the hand-written `C:\\LLM` PowerShell lifecycle scripts with noerelay "
                "Python entry points, and drive the llama-server invocation from a single master "
                "YAML that carries the full reference argument set (NR-LLM-004, NR-LLM-005).",
        approach="Move start/stop/scheduled-task logic into `src/noerelay/` (server lifecycle "
                 "module + CLI verbs) so `python -m noerelay.cli` performs the operations on "
                 "Windows and POSIX; have the installer generate only thin `.bat`/`.sh` wrappers "
                 "that resolve the provisioned venv interpreter and call the Python entry points; "
                 "introduce a master YAML schema for all llama-server settings (model, host/port, "
                 "ctx, parallel, batch/ubatch, flash-attn, cache types, tensor split, gpu layers, "
                 "flags) and generate `ProvisionPlan.server_args()` from it, matching the "
                 "reference `start-llama-server` arguments.",
        goals=[
            "Implement server start/stop/schedule in the Python package with CLI verbs.",
            "Make generated installer scripts thin venv-resolving wrappers (no `.ps1`).",
            "Define and validate a master YAML schema for llama-server settings.",
            "Generate the full server argument list from the YAML.",
        ],
        non_goals=[
            "No PowerShell lifecycle scripts are generated or required.",
            "No change to the OpenRouter cloud plane; this is local provisioner behavior.",
        ],
        components=[
            "src/noerelay/cli.py (start/stop/schedule verbs)",
            "src/noerelay/provision.py (ProvisionPlan.server_args from YAML)",
            "src/noerelay/installer.py (write_config, generate_scripts)",
            "src/noerelay/scripts.py (thin .bat/.sh wrappers)",
            "deploy/host/installer/README_TEMPLATE.md (operator docs)",
        ],
        risks=[
            "Generated wrappers invoke the wrong interpreter when the venv path is not resolved.",
            "YAML schema accepts unknown keys and silently drops a required flag.",
            "Scheduled-task creation differs between Windows and POSIX and is untested.",
        ],
        acceptance=[
            "`noerelay` start/stop/schedule work on Windows and POSIX using the venv Python.",
            "The installer emits only `.bat`/`.sh` wrappers that resolve the venv interpreter; no `.ps1` lifecycle files.",
            "The provisioned server launches with the full reference argument set generated from the YAML.",
            "Changing a YAML value changes the generated invocation; unknown keys are rejected.",
        ],
        tasks=[
            "Implement the Python server lifecycle module and CLI verbs.",
            "Rework `scripts.py` to emit thin venv-resolving wrappers only.",
            "Define the master YAML schema and load it in the provisioner.",
            "Generate `server_args()` from the YAML and validate against the reference set.",
            "Record T-LLM-004/005 evidence for NR-LLM-004/005.",
        ],
    ),
    dict(
        id="TOOLS-01",
        title="Local state locality and Hugging Face operator CLI",
        outcome="Keep all NoeRelay-managed local state inside the project-local `.noerelay/` "
                "directory, and give operators Hugging Face model search, download with progress "
                "and resume, and shell autocomplete in the CLI (NR-OPS-004, NR-LLM-006).",
        approach="Confirm and, where needed, pin the tooling defaults so databases, logs, run "
                 "artifacts, gap/verification matrices, and exports are written under `.noerelay/` "
                 "and `noerelay gaps` reads/writes there by default; add `noerelay hf search` and "
                 "`noerelay hf download` (GGUF resolution, progress, resume) backed by "
                 "huggingface_hub where available with a stdlib fallback; add completion data for "
                 "catalog and HF repo identifiers so tab-completion works without a network "
                 "round-trip for catalog entries.",
        goals=[
            "Default all managed local state to `.noerelay/` and keep tools reading from there.",
            "Add `noerelay hf search` and `noerelay hf download` with progress and resume.",
            "Provide autocomplete for model identifiers and quant names.",
        ],
        non_goals=[
            "No secret storage or credential handling in the CLI.",
            "No replacement of the provisioner's model download; this is an operator-facing helper.",
        ],
        components=[
            "src/noerelay/cli.py (hf search/download verbs, completion data)",
            "src/noerelay/config.py (state paths under .noerelay/)",
            "src/noerelay/models.py (catalog identifiers for completion)",
            "reference/gateway/config.py (gateway defaults to .noerelay/)",
        ],
        risks=[
            "A tool writes managed state outside `.noerelay/` and breaks the locality contract.",
            "Download resume loses partial progress on interruption.",
            "Completion data drifts from the catalog and suggests stale identifiers.",
        ],
        acceptance=[
            "No tool writes managed state outside `.noerelay/` on the local profile; `noerelay gaps` uses it by default.",
            "`noerelay hf search/download` resolves and fetches GGUF artifacts with progress and resume.",
            "Tab-completion suggests catalog and HF repo identifiers; catalog entries need no network.",
        ],
        tasks=[
            "Audit and pin state paths to `.noerelay/` across the CLI and gateway defaults.",
            "Implement `noerelay hf search` and `noerelay hf download` with resume.",
            "Add completion data for model identifiers and quant names.",
            "Record T-OPS-004 and T-LLM-006 evidence for NR-OPS-004 and NR-LLM-006.",
        ],
    ),
]


# --------------------------------------------------------------------------- #
# Plan section 6 metadata: primary owner and dependencies per work package.
# Kept separate from PACKAGES so the narrative list stays focused; applied in
# main() before rendering. Dependency strings may use plan-style ranges or
# prose (e.g. "IAM-01..04", "feature freeze") where the plan itself names a
# workstream rather than a single package.
# --------------------------------------------------------------------------- #
CATALOG_META = {
    "FND-01": {"owner": ("ROLE-ORCH",), "deps": []},
    "FND-02": {"owner": ("ROLE-ARCH",), "deps": ["FND-01"]},
    "FND-03": {"owner": ("ROLE-ORCH",), "deps": ["FND-01", "FND-02"]},
    "GOV-01": {"owner": ("ROLE-RUST", "ROLE-ARCH"), "deps": ["FND-02", "FND-03", "IAM-03"]},
    "IAM-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["FND-02"]},
    "IAM-02": {"owner": ("ROLE-RUST", "ROLE-SEC"), "deps": ["IAM-01"]},
    "IAM-03": {"owner": ("ROLE-RUST", "ROLE-SEC"), "deps": ["IAM-01"]},
    "IAM-04": {"owner": ("ROLE-DATA", "ROLE-COMP"), "deps": ["IAM-01", "ART-01"]},
    "RUN-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["FND-02", "IAM-01"]},
    "RUN-02": {"owner": ("ROLE-RUST",), "deps": ["RUN-01"]},
    "RUN-03": {"owner": ("ROLE-RUST",), "deps": ["RUN-01", "RUN-02"]},
    "RUN-04": {"owner": ("ROLE-RUST", "ROLE-SRE"), "deps": ["RUN-01", "RUN-02", "RUN-03"]},
    "ART-01": {"owner": ("ROLE-DATA",), "deps": ["FND-02", "IAM-01"]},
    "API-01": {"owner": ("ROLE-PROTO",), "deps": ["FND-02", "IAM-01"]},
    "API-02": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["API-01", "RUN-01"]},
    "API-03": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["API-01", "RUN-01"]},
    "API-04": {"owner": ("ROLE-RUST",), "deps": ["API-02", "API-03", "RUN-03"]},
    "API-05": {"owner": ("ROLE-RUST", "ROLE-WEB"), "deps": ["FND-02", "IAM-03"]},
    "REG-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["FND-02", "IAM-01"]},
    "PROV-01": {"owner": ("ROLE-RUST",), "deps": ["REG-01", "RUN-02", "API-02", "API-03"]},
    "PROV-02": {"owner": ("ROLE-RUST",), "deps": ["PROV-01", "VER-01"]},
    "MEDIA-01": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["REG-01", "PROV-01", "ART-01"]},
    "MEDIA-02": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["MEDIA-01", "TOOL-01"]},
    "TOOL-01": {"owner": ("ROLE-RUST", "ROLE-SEC"), "deps": ["REG-01", "IAM-03", "RUN-03"]},
    "TOOL-02": {"owner": ("ROLE-RUST", "ROLE-SEC"), "deps": ["TOOL-01", "ART-01"]},
    "MCP-01": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["TOOL-01", "TOOL-02", "RUN-03"]},
    "A2A-01": {"owner": ("ROLE-RUST", "ROLE-PROTO"), "deps": ["REG-01", "RUN-01", "RUN-02", "RUN-03", "IAM-03"]},
    "A2A-02": {"owner": ("ROLE-PROTO", "ROLE-SEC"), "deps": ["A2A-01", "VER-01"]},
    "VER-01": {"owner": ("ROLE-RUST",), "deps": ["RUN-01", "ART-01", "REG-01"]},
    "VER-02": {"owner": ("ROLE-RUST",), "deps": ["VER-01", "PROV-02"]},
    "VER-03": {"owner": ("ROLE-RUST", "ROLE-WEB"), "deps": ["VER-01", "IAM-03", "API-05"]},
    "MEM-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["RUN-01", "ART-01", "IAM-04"]},
    "CTX-01": {"owner": ("ROLE-RUST", "ROLE-PY-EVAL"), "deps": ["MEM-01", "REG-01"]},
    "LED-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["RUN-01", "ART-01", "IAM-03"]},
    "COST-01": {"owner": ("ROLE-RUST", "ROLE-DATA"), "deps": ["RUN-01", "RUN-02", "RUN-03", "REG-01", "PROV-01"]},
    "COST-02": {"owner": ("ROLE-RUST", "ROLE-WEB"), "deps": ["COST-01", "EVAL-01"]},
    "EVAL-01": {"owner": ("ROLE-PY-EVAL", "ROLE-RUST"), "deps": ["VER-01", "MEM-01", "COST-01"]},
    "REC-01": {"owner": ("ROLE-RUST", "ROLE-PY-EVAL"), "deps": ["EVAL-01", "COST-02"]},
    "REC-02": {"owner": ("ROLE-RUST", "ROLE-PY-EVAL"), "deps": ["REC-01", "OPS-02"]},
    "UI-01": {"owner": ("ROLE-WEB",), "deps": ["API-05", "VER-03", "COST-02"]},
    "OPS-01": {"owner": ("ROLE-SRE", "ROLE-RUST"), "deps": ["RUN-04", "API-04"]},
    "OPS-02": {"owner": ("ROLE-RUST", "ROLE-SRE"), "deps": ["IAM-03", "REG-01", "RUN-02"]},
    "OPS-03": {"owner": ("ROLE-SRE", "ROLE-DATA"), "deps": ["ART-01", "LED-01", "RUN-04"]},
    "SEC-01": {
        "owner": ("ROLE-SEC",),
        "deps": ["IAM-01..04", "RUN-01..04", "TOOL-01..02", "MCP-01", "A2A-01..02"],
    },
    "SEC-02": {
        "owner": ("ROLE-SEC", "ROLE-SRE"),
        "deps": ["FND-03", "immutable build pipeline"],
    },
    "COMP-01": {"owner": ("ROLE-COMP",), "deps": ["FND-03", "LED-01"]},
    "COMP-02": {"owner": ("ROLE-COMP", "ROLE-DATA"), "deps": ["IAM-04", "ART-01", "OPS-03"]},
    "REL-01": {
        "owner": ("ROLE-SRE",),
        "deps": ["feature freeze", "OPS-01", "OPS-02", "OPS-03", "SEC-01"],
    },
    "REL-02": {"owner": ("ROLE-HUMAN",), "deps": ["all beta gates"]},
    "REL-03": {"owner": ("ROLE-ORCH", "ROLE-HUMAN"), "deps": ["REL-01", "REL-02"]},
    "REL-04": {"owner": ("ROLE-ORCH", "ROLE-HUMAN"), "deps": ["REL-03"]},
    "RTK-01": {"owner": ("ROLE-PY-EVAL", "ROLE-RUST"), "deps": ["CTX-01"]},
    "LLM-01": {"owner": ("ROLE-PY-EVAL",), "deps": ["FND-01"]},
    "LLM-02": {"owner": ("ROLE-PY-EVAL", "ROLE-SRE"), "deps": ["LLM-01"]},
    "TOOLS-01": {"owner": ("ROLE-PY-EVAL", "ROLE-SRE"), "deps": ["LLM-02"]},
}


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def render_spec(pkg: dict, reqs_by_id: dict, pkg_reqs: list, req_to_tests: dict) -> str:
    lines = []
    lines.append(f"# Spec: {pkg['id']} — {pkg['title']}")
    lines.append("")
    lines.append("> Work package `{}` · NoeRelay GA Completion Program".format(pkg["id"]))
    lines.append("> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`")
    owners = pkg.get("owner") or ("ROLE-RUST",)
    if isinstance(owners, str):
        owners = (owners,)
    owners_cell = ", ".join("`{}`".format(o) for o in owners)
    deps = ", ".join("`{}`".format(d) for d in pkg.get("dependencies", [])) or "—"
    lines.append(f"> Primary owner: {owners_cell} · Depends on: {deps}")
    lines.append("")
    lines.append("## Problem")
    lines.append("")
    lines.append(pkg["outcome"])
    lines.append("")
    lines.append("## Goals")
    lines.append("")
    for g in pkg["goals"]:
        lines.append(f"- {g}")
    lines.append("")
    lines.append("## Non-goals")
    lines.append("")
    for ng in pkg["non_goals"]:
        lines.append(f"- {ng}")
    lines.append("")
    lines.append("## Requirements")
    lines.append("")
    if pkg_reqs:
        for rid in pkg_reqs:
            info = reqs_by_id.get(rid)
            if info:
                tests = ", ".join("`{}`".format(t) for t in req_to_tests.get(rid, [])) or "—"
                lines.append(f"- `{rid}` — {info['text']}")
                lines.append(f"  - Acceptance: {info['acceptance']} · Release test(s): {tests}")
            else:
                lines.append(f"- `{rid}` (see `docs/requirements.md`)")
    else:
        lines.append(
            "Supporting capability package: `{}` is not a primary owner of any MUST requirement in "
            "`spec/coverage-manifest.json`. It contributes to the routed capabilities and is "
            "exercised through the release tests of the packages that own the requirements it "
            "supports.".format(pkg["id"])
        )
    lines.append("")
    lines.append("## Acceptance criteria")
    lines.append("")
    for a in pkg["acceptance"]:
        lines.append(f"- [ ] {a}")
    lines.append("")
    return "\n".join(lines)


def render_plan(pkg: dict) -> str:
    lines = []
    lines.append(f"# Plan: {pkg['id']} — {pkg['title']}")
    lines.append("")
    lines.append("## Approach")
    lines.append("")
    lines.append(pkg["approach"])
    lines.append("")
    lines.append("## Components")
    lines.append("")
    for c in pkg["components"]:
        lines.append(f"- `{c}`")
    lines.append("")
    lines.append("## Risks")
    lines.append("")
    for r in pkg["risks"]:
        lines.append(f"- {r}")
    lines.append("")
    return "\n".join(lines)


def render_tasks(pkg: dict) -> str:
    lines = []
    lines.append(f"# Tasks: {pkg['id']} — {pkg['title']}")
    lines.append("")
    for i, t in enumerate(pkg["tasks"], start=1):
        lines.append(f"- [ ] {i}. {t}")
    lines.append("")
    return "\n".join(lines)


def render_readme(packages: list, pkg_to_reqs: dict) -> str:
    lines = []
    lines.append("# NoeRelay GA Completion Program — Work-Package Features")
    lines.append("")
    lines.append(
        "One feature folder per work package from the master catalog in "
        "`docs/ga-completion-orchestrator-plan.md` §6. Each folder holds `spec.md`, `plan.md`, "
        "and `tasks.md` (the spec-kit convention in `.specify/memory/constitution.md`)."
    )
    lines.append("")
    lines.append(
        "Generated by `scripts/generate_specify_features.py` from `spec/coverage-manifest.json` "
        "(requirement → package → test + gates) and `docs/requirements.md` (requirement text). "
        "Re-run the generator to refresh; do not hand-edit the generated requirement/test IDs."
    )
    lines.append("")
    lines.append("## Index")
    lines.append("")
    lines.append(
        "| Package | Title | Primary owner | Depends on | Primary requirements (coverage-manifest.json) |"
    )
    lines.append("|---|---|---|---|---|")
    for pkg in packages:
        reqs = pkg_to_reqs.get(pkg["id"], [])
        reqs_cell = ", ".join("`{}`".format(r) for r in reqs) if reqs else "supporting"
        owners = pkg.get("owner") or ("ROLE-RUST",)
        if isinstance(owners, str):
            owners = (owners,)
        owners_cell = ", ".join("`{}`".format(o) for o in owners)
        deps = pkg.get("dependencies", [])
        deps_cell = ", ".join("`{}`".format(d) for d in deps) if deps else "—"
        lines.append(
            f"| `{pkg['id']}` | {pkg['title']} | {owners_cell} | {deps_cell} | {reqs_cell} |"
        )
    lines.append("")
    lines.append(
        "Packages marked **supporting** are not a primary owner of any MUST requirement in "
        "`spec/coverage-manifest.json`; they contribute to the capabilities owned by other "
        "packages and are exercised through those packages' release tests."
    )
    lines.append("")
    lines.append("## Gate taxonomies (two ladders share the `G0`–`G8` labels)")
    lines.append("")
    lines.append(
        "The labels `G0`–`G8` appear in **two distinct taxonomies**. They are not the same "
        "gate and must not be conflated:"
    )
    lines.append("")
    lines.append(
        "1. **Release-authority ladder** — `docs/ga-completion-orchestrator-plan.md` §9.2. "
        "Human sign-off gates for the program: `G0 Architecture`, `G1 Walking system`, "
        "`G2 Live core`, `G3 Interoperability`, `G4 Governed intelligence`, `G5 Beta`, "
        "`G6 Release candidate`, `G7 Pilot`, `G8 GA`. Each gate names the required state and "
        "the release authority (human owners/verifiers). No later gate compensates for an "
        "earlier failure."
    )
    lines.append("")
    lines.append(
        "2. **Evidence-collection ladder** — `release_gates` in `spec/coverage-manifest.json`. "
        "Machine-checked by `xtask evidence gate`: `G0` scope freeze, `G1` schema lineage, "
        "`G2` evidence collection executable, `G3` identity/tenancy, `G4` durable runs, "
        "`G5` API compatibility/streaming, `G6` registry/routing, `G7` verification/ledger/"
        "cost, `G8` security/ops/compliance/release. Each gate lists the requirement IDs and "
        "release test IDs whose recorded evidence must be present."
    )
    lines.append("")
    lines.append(
        "The manifest keys are the machine contract parsed by `xtask` "
        "(`load_known_from_manifest`); they must not be renamed to match the plan's "
        "release-authority ladder."
    )
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> int:
    if not os.path.exists(MANIFEST_PATH):
        print(f"ERROR: manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1
    if not os.path.exists(REQUIREMENTS_PATH):
        print(f"ERROR: requirements not found at {REQUIREMENTS_PATH}", file=sys.stderr)
        return 1

    manifest = load_manifest(MANIFEST_PATH)
    reqs_by_id = parse_requirements(REQUIREMENTS_PATH)
    pkg_to_reqs, req_to_tests, gates = build_maps(manifest)

    # Sanity: every manifest requirement must have >=1 package and >=1 test.
    manifest_req_ids = {r["requirement_id"] for r in manifest.get("requirements", [])}
    problems = []

    # Apply plan section 6 owner/dependency metadata before rendering.
    known_ids = {p["id"] for p in PACKAGES}
    for pkg in PACKAGES:
        meta = CATALOG_META.get(pkg["id"])
        if meta is None:
            problems.append(f"{pkg['id']}: missing CATALOG_META owner/dependencies entry")
            continue
        pkg["owner"] = meta["owner"]
        pkg["dependencies"] = list(meta["deps"])
    for mid in CATALOG_META:
        if mid not in known_ids:
            problems.append(f"CATALOG_META entry {mid} has no matching package")
    for r in manifest.get("requirements", []):
        if not r.get("primary_work_packages"):
            problems.append(f"{r['requirement_id']}: no primary work package")
        if not r.get("primary_release_tests"):
            problems.append(f"{r['requirement_id']}: no primary release test")

    # Sanity: every requirement referenced by a package exists in the manifest.
    for pkg in PACKAGES:
        for rid in pkg_to_reqs.get(pkg["id"], []):
            if rid not in manifest_req_ids:
                problems.append(f"{pkg['id']}: references unknown requirement {rid}")

    # Sanity: every package id is unique.
    seen = set()
    for pkg in PACKAGES:
        if pkg["id"] in seen:
            problems.append(f"duplicate package id {pkg['id']}")
        seen.add(pkg["id"])

    if problems:
        print("Manifest/catalog sanity problems:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        return 1

    os.makedirs(FEATURES_DIR, exist_ok=True)
    written = 0
    supporting = []
    for pkg in PACKAGES:
        folder = os.path.join(FEATURES_DIR, pkg["id"].lower())
        os.makedirs(folder, exist_ok=True)
        pkg_reqs = pkg_to_reqs.get(pkg["id"], [])
        if not pkg_reqs:
            supporting.append(pkg["id"])
        files = {
            "spec.md": render_spec(pkg, reqs_by_id, pkg_reqs, req_to_tests),
            "plan.md": render_plan(pkg),
            "tasks.md": render_tasks(pkg),
        }
        for name, content in files.items():
            with open(os.path.join(folder, name), "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            written += 1

    with open(os.path.join(FEATURES_DIR, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_readme(PACKAGES, pkg_to_reqs))
    written += 1

    # Summary
    print("=== spec-kit feature generation ===")
    print(f"packages:        {len(PACKAGES)}")
    print(f"files written:   {written}  (in {FEATURES_DIR})")
    print(f"manifest reqs:   {len(manifest_req_ids)}")
    print(f"gates:           {', '.join(sorted(gates.keys()))}")
    print(f"supporting pkgs: {', '.join(supporting) if supporting else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
