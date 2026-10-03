# Agent Instructions for mod-llm-chatter

Ambient bot conversations for AzerothCore WotLK (3.3.5a).

These instructions apply to any mod-llm-chatter task, including related
files outside this module directory. Shared workspace instructions in the
root `AGENTS.md` still apply.

Paths below are relative to this module unless marked workspace-relative.

## Context Loading

For any mod-llm-chatter task, first read
`docs/mod-llm-chatter-philosophy.md`. Every feature and its implementation
must adhere to these immersion principles.

For mod-llm-chatter changes, read both:

- `docs/mod-llm-chatter-architecture.md`
- `docs/mod-llm-chatter-documentation.md`

These two docs are authoritative for ownership and runtime behavior.
Keep them contributor-facing: no personal paths, internal artifact links,
session history, or process notes.

## Development Environment

- `ac-llm-chatter-bridge` - mod-llm-chatter Python service

Follow the root `AGENTS.md` build and runtime policy.

## Separation of Concerns

Follow the current ownership map for C++ (`src/`) and Python (`tools/`).

Each file should have a clear ownership domain. New features or subsystems
get their own file(s); shared utilities belong in a dedicated shared file.

## Contributor Code Review

This section applies specifically to mod-llm-chatter contributions. It does
not add requirements for upstream core or mod-playerbots changes.

Apply `.agents/docs/code-review.md` (workspace-relative) first, then
protect the established design and quality bar of this module.

Contributor code should look and behave as though it belongs in the
existing module. Compare it with nearby code and the closest analogous
feature before accepting it. Check that it:

- upholds `docs/mod-llm-chatter-philosophy.md` in both player-facing
  behavior and implementation
- follows the module's existing ownership boundaries and keeps each
  concern in the appropriate file
- reuses established helpers, contracts, config patterns, JSON shapes,
  naming, logging, and error-handling conventions
- preserves existing runtime behavior and compatibility unless the
  change deliberately and clearly updates that behavior
- handles null, empty, malformed, failure, retry, concurrency, and
  cleanup paths to the same standard as the surrounding implementation
- avoids parallel abstractions, duplicated utilities, unrelated
  refactors, and unnecessary changes outside the contribution's scope
- applies SoC, DRY, KISS, and YAGNI pragmatically; do not add complexity
  or abstractions for hypothetical future use
- updates configuration templates, migrations, tests, and contributor
  documentation when the behavior or contract changes

Consistency does not mean copying an existing defect or blocking a
clear improvement. Correctness, safety, maintainability, and documented
architecture take priority. Accept a deliberate divergence when its
benefit is concrete and the new pattern is applied coherently; otherwise
require the contributor to match the established approach.

Review findings must identify the specific established pattern or
quality risk being violated. Do not reject code solely because a
reviewer would have written it differently.
