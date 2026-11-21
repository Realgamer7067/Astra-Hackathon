# Interfaces and contracts — TO BE DECIDED

**No interface below is approved until kickoff.** Every consuming feature must agree on the shapes and error behavior **before** parallel implementation begins.

For each interface, specify:

1. Producer and consumers, owner and version.
2. Endpoint / function / event name and method.
3. Request shape and example, validation, authentication.
4. Success response and error shapes with examples.
5. Null/empty/loading behavior, pagination/limits where relevant.
6. Compatibility tests and migration policy.

## Contract list

| ID | Producer | Consumers | Status | Link to schema/test |
|---|---|---|---|---|
| (none yet) | | | | |

## Change policy

Any breaking change needs coordination with affected task owners **before** implementation, an updated contract, and matching automated contract/integration tests. Do not silently rename endpoints, response fields, or shared types.

