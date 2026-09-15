# Plan: PROV-01 — Production OpenRouter adapter and explicit provider controls

## Approach

Always send the explicit selected model and bounded provider policy; never allow OpenRouter automatic routing to replace NoeRelay route authority. Test Chat and upstream Responses independently. Remote tests use protected non-production credentials, synthetic prompts, allowlisted models, and an explicit spend ceiling.

## Components

- `crates/noerelay-gateway/src/lib.rs (proxy_openai_request, validate_requested_model, upstream path selection)`
- `crates/noerelay-gateway/src/stub_provider.rs (test provider boundary)`

## Risks

- A redirect or DNS rebinding sends the request to an untrusted host.
- Usage is not captured, breaking cost reconciliation.
