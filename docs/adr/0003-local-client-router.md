# ADR 0003: Keep one Rust routing authority for local coding clients

Status: accepted for the current local deployment, 2026-09-15.

## Decision

Retain `noerelay-core::StagedRouter` and the Rust gateway task classifier. OpenCode, Zoo Code, and Codex use public aliases. Python adapters do not independently choose models. LiteLLM adapts protocols; llama.cpp manages model loading. Governance and capability filters remain authoritative before fallback.

Fix a measured policy defect rather than adding a second router: substring matching treated `improve` as `prove`, selecting the slower reasoning tier. Whole-word and normalized phrase matching keeps simple code improvements on Qwen3.6 while formal proof and root-cause prompts select Qwen3.8. Regression tests bind this behavior. No claim of globally optimal task classification is made.

## Alternatives and fit

- RouteLLM (Python) provides learned strong/weak model selection and threshold calibration. Its documented MF/similarity defaults use embeddings; representative outcome data are required to calibrate these local model choices. We do not have that dataset. Adding it now offers no demonstrated quality benefit and introduces another decision layer. https://github.com/lm-sys/RouteLLM
- LiteLLM routing handles deployment selection, retries, and latency/cost balancing. Keep its protocol integration; leave fallback and policy in Rust to avoid conflicting retry owners. https://docs.litellm.ai/docs/routing
- vLLM Semantic Router provides richer policy and learned selectors. Its own documentation describes trained selectors as experimental and dependent on representative query/model outcomes. It adds a separate service/control layer beyond this three-model, one-resident-model deployment. https://github.com/vllm-project/semantic-router/tree/main/src/semantic-router/pkg/modelselection

## Evidence boundary

This is an architectural fit assessment and code-path review, not a head-to-head performance benchmark. The existing router already exposes an advisory-ranking boundary that cannot waive hard constraints. A future learned ranker should first run in shadow mode against a held-out coding/reasoning corpus, measure task success, routing latency and model-switch costs, and demonstrate improvement before replacing the deterministic policy. Existing configured acceptance scores are not newly measured quality estimates.

The live client tests observe the complete NoeRelay path. Concurrent local builds and model loading affect timings; do not interpret their wall-clock duration as isolated router overhead.
