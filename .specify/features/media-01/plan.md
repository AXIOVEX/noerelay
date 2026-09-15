# Plan: MEDIA-01 — Vision and image-processing routes

## Approach

Keep binary media outside JSON/database rows; bind content type, size, dimensions, parameters, provider/model revision, hashes, and retention. Route through the registry and provider plane with modality-aware admissibility.

## Components

- `crates/noerelay-core/src/wire.rs (multimodal content parts)`
- `crates/noerelay-core/src/registry.rs (modality capabilities)`
- `crates/noerelay-core/src/artifacts.rs (media artifact binding)`

## Risks

- A decompression bomb or oversized image is processed without limits.
- Media provenance is missing, breaking receipt binding.
