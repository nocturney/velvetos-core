# Provider interface v0 — context compaction

Status: **NON_NORMATIVE_REFORM_PREPARATION**  
Runtime enabled: **false**

The provider adapter is deliberately narrower than the VelvetOS continuity contract. Provider-specific compaction is an optimization; VelvetOS state and verification remain provider-independent.

## Adapter contract

```text
estimate(input) -> PressureEstimate
compact(input)  -> CompactionResult
```

### PressureEstimate

Required conceptual fields:

- `provider`
- `model_or_runtime`
- `measurement_kind`: exact_tokens | provider_headroom | estimate | unknown
- `used`
- `limit`
- `headroom`
- `confidence`
- `observed_at`

Unknown values stay unknown. A provider adapter must not synthesize a precise token count from a heuristic and label it exact.

### CompactionInput

- derived continuation manifest that already passed pre-compaction verification;
- bounded recent tail;
- optional provider-native conversation/session reference;
- target headroom requested by the harness;
- redaction/exclusion list;
- immutable references that must survive unchanged.

The adapter must not receive policy authority or permission to mutate canonical VelvetOS state.

### CompactionResult

- `status`: success | failed | unsupported
- `provider`
- `summary_or_native_reference`
- `retained_exact_refs`
- `provider_metrics`
- `warnings`
- `error`

A successful provider response is **not** a continuation PASS. It must still pass the VelvetOS post-compaction verifier.

## Planned adapters

### OpenAI native path

Prefer provider-native compaction when the selected OpenAI runtime exposes it. Keep provider/session identifiers opaque and outside policy authority. The adapter may use native compacted state/reference rather than re-summarizing when supported.

### Provider-agnostic fallback

A bounded summarization adapter may emit a structured compacted tail, but it must obey the same preservation list and verification. It must never become a second memory system.

## Failure semantics

- unsupported -> continue without compaction;
- provider error -> continue/recover without changing canonical state;
- malformed result -> reject;
- missing exact ref -> reject;
- authority drift -> reject;
- contradiction with canonical state -> canonical source wins; reject compacted result.

## Kill switch

One global feature flag must be able to bypass every provider adapter and restore current checkpoint/HANDOFF continuation behavior with no data migration.
