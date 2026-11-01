# Architecture

The game is a React browser interface, one FastAPI service and validated JSON story content. Local Ollama runs separately when live dialogue is enabled. There is no account system, database, training service or durable saved game.

```text
Browser controls -> typed action -> FastAPI validation and rules
                                  -> updated public state -> browser
Ghost question   -> eligible character facts -> Ollama/Qwen selection
                                  -> validated authored clauses -> browser
```

## Authority and content

The backend validates room access, object operations, discoveries, puzzle answers, deductions, relationships and theory support. It applies accepted effects once and evaluates endings deterministically. Browser card positions and unfinished puzzle arrangements are local presentation state.

Canonical JSON includes hidden predicates, solutions and story truth. The API projects only eligible state and referenced presentation assets. The production frontend must not import canonical JSON or the private content schema. This boundary protects normal play from accidental spoilers, not readers of the published source repository.

## Dialogue boundary

Before calling the provider, the backend filters each ghost's knowledge by game conditions and relationship state and removes superseded beliefs. It prepares a bounded permitted-fact selection and recent history instead of the complete hidden case truth. Qwen selects permitted fact identifiers and a bounded reaction through structured output. The backend rejects invalid selections and renders authored factual clauses. This is real inference with constrained content, not unrestricted generated factual prose.

The provider attempt has a ten-second deadline and no automatic replacement retry. Unavailable, slow or malformed output produces labeled authored fallback. Demo mode uses authored responses without a provider call. The response's source metadata is displayed; a health response or configured model name does not prove inference.

## Transport and sessions

[Contract 1.0.0](../contracts/README.md) defines closed request/response schemas. Mutations carry a request UUID and expected revision. Repeated request identity supports safe recovery; revision conflicts must not silently overwrite newer state. The interface preserves uncertain requests for explicit same-request retry.

Run one backend worker. Sessions and idempotency records exist in process memory. There are eight process-lifetime session slots and a 500-mutation lifetime allowance per session; restarting an investigation does not reset that allowance. A backend restart loses all sessions. This architecture is intended for local play, not public multiuser hosting.

## Presentation

Six generated room backplates and three generated portraits are combined with code-based overlays, object states, evidence/puzzle controls and optional synthesized sound. The server supplies asset references. Readable object lists and non-drag controls remain available; motion and sound never decide progress. See [notices](../THIRD_PARTY_NOTICES.md) and [verification limits](progress.md).
