# Agentic Backend Checklist: Backend Agentic Architecture Refactor

**Purpose**: Pre-implementation requirements quality gate — validate that spec, plan, contracts, and tasks are complete, clear, consistent, and measurable before `/speckit.implement`  
**Created**: 2026-05-25  
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)  
**Audience**: PR reviewer / implementer (standard depth)  
**Focus**: Native streaming, structured research output, session-store projection, API stability, concurrency, big-bang release

**Note**: Items test **requirements writing quality**, not runtime behavior.

---

## Requirement Completeness

- [ ] CHK001 Are real-time streaming requirements defined for both chat and research workflows with distinct progress vs token event semantics? [Completeness, Spec §US1, FR-001]
- [ ] CHK002 Is the prohibition on artificial post-completion streaming explicitly stated as a requirement? [Completeness, Spec §FR-002]
- [ ] CHK003 Are structured research output fields (chat, article, title, actions) all documented with optional vs mandatory rules per response type? [Completeness, Spec §US2, FR-003–FR-004]
- [ ] CHK004 Are requirements defined for chat-only research responses that must not mutate the article panel? [Completeness, Spec §US2, FR-004]
- [ ] CHK005 Is the authoritative session history store and domain projection relationship documented for both chat and research? [Completeness, Spec §Clarifications, FR-005, Data Model]
- [ ] CHK006 Are source citation field requirements (title, URL, snippet, rank, dedup cap) specified independently of answer text parsing? [Completeness, Spec §US4, FR-006]
- [ ] CHK007 Are stop, timeout, and orphan-run recovery requirements each defined with distinct terminal states? [Completeness, Spec §US5, FR-007–FR-008, FR-017]
- [ ] CHK008 Are per-session and per-user concurrency limits both specified with HTTP response semantics? [Completeness, Spec §Clarifications, FR-009, FR-009a, Contracts §409]
- [ ] CHK009 Is the big-bang cutover requirement (chat + research together, no mixed architecture) documented in spec, plan, and tasks? [Completeness, Spec §US7, FR-010, Assumptions]
- [ ] CHK010 Are observability requirements scoped to both chat and research runs when tracing is enabled vs disabled? [Completeness, Spec §US6, FR-013]
- [ ] CHK011 Are token/cost persistence requirements limited to research with explicit fields documented? [Completeness, Spec §FR-014, Key Entities §Cost Record]
- [ ] CHK012 Are credential initialization and agent reuse requirements specified without prescribing unsafe runtime patterns? [Completeness, Spec §FR-015–FR-016]
- [ ] CHK013 Is one-time history backfill for pre-existing chat sessions documented as an assumption with success/failure expectations? [Gap, Spec §Assumptions, Plan §Phase E, Tasks §T027]

---

## Requirement Clarity

- [ ] CHK014 Is "real-time streaming" quantified with a time-to-first-event threshold applicable to both chat and research? [Clarity, Spec §SC-001, US1]
- [ ] CHK015 Is "safe progress indicator" defined with examples of permitted vs prohibited content (e.g., no raw chain-of-thought)? [Clarity, Spec §US1, Constitution §Agent Behavior]
- [ ] CHK016 Is "structured research outcome" defined precisely enough to replace delimiter-based parsing without ambiguity? [Clarity, Spec §US2, Plan §Research Decision]
- [ ] CHK017 Is partial-content-on-stop behavior specified with message status semantics (`stopped`) and research article-version rules? [Clarity, Spec §Clarifications, US5, Edge Cases]
- [ ] CHK018 Is the per-user concurrent run cap stated as an exact number (10) in all relevant artifacts? [Clarity, Spec §Clarifications, FR-009a, SC-011]
- [ ] CHK019 Are new 409 error codes (`run_in_progress`, `concurrent_run_limit`) defined with JSON shape in contracts? [Clarity, Contracts §api-stability]
- [ ] CHK020 Is "agent session store authoritative; domain tables projection" unambiguous about which API reads from which layer? [Clarity, Spec §Clarifications, Data Model §Layer Architecture]
- [ ] CHK021 Is median time-to-first-token improvement (≥30%) defined with baseline measurement method? [Clarity, Spec §SC-009, Quickstart §Baseline]
- [ ] CHK022 Is "research structured output success rate" (90%) defined with test scenario classes? [Clarity, Spec §SC-002, US2 Independent Test]

---

## Requirement Consistency

- [ ] CHK023 Are chat concurrent-run rules consistent between edge cases, FR-009, US5 acceptance scenario 4, and api-stability contract? [Consistency, Spec §Edge Cases, FR-009, Contracts]
- [ ] CHK024 Are research concurrent-run rules aligned with chat (reject vs queue) across spec and tasks? [Consistency, Spec §FR-009, Tasks §T034–T035]
- [ ] CHK025 Do stop/partial-content requirements align across US5, FR-007, edge case, and projection invariants without contradicting "empty content fallback"? [Consistency, Spec §US5, Edge Cases]
- [ ] CHK026 Is reasoning exposure policy consistent between chat (safe progress only) and research (`reasoning` SSE event / stored field)? [Consistency, Spec §US1 vs US6, Plan §event_mapper]
- [ ] CHK027 Do success criteria SC-007 (100% contract pass) and US7 (no frontend changes) align with FR-010 big-bang scope? [Consistency, Spec §SC-007, US7, FR-010]
- [ ] CHK028 Are research history authority rules consistent between chat clarification (agent store authoritative) and research's existing `research_agno_sessions` usage? [Consistency, Data Model, Plan §Phase C]
- [ ] CHK029 Do tasks.md phases enforce the same dependency order as plan.md (foundation → US1 → US2 → gate)? [Consistency, Tasks §Dependencies, Plan §Implementation Phases]

---

## Acceptance Criteria Quality

- [ ] CHK030 Can SC-001 (3s first event, 95%) be measured objectively without implementation details? [Measurability, Spec §SC-001]
- [ ] CHK031 Can SC-005 (stop within 10s, 95%) be verified independently of SC-001 streaming metrics? [Measurability, Spec §SC-005]
- [ ] CHK032 Can SC-006 (zero stuck runs after restart) be tied to a defined orphan transition requirement? [Measurability, Spec §SC-006, FR-017]
- [ ] CHK033 Can SC-011 (11th run rejected, 100%) be traced to FR-009a and contract error payload? [Measurability, Spec §SC-011, Contracts]
- [ ] CHK034 Is SC-010 (reusable execution pattern for third workflow) defined as an architectural outcome rather than a line-count metric? [Measurability, Spec §SC-010]
- [ ] CHK035 Does each P1 user story (US1, US2, US3, US7) have an independent test statement mappable to quickstart or contract tests? [Traceability, Spec §User Scenarios, Quickstart]

---

## Scenario Coverage

- [ ] CHK036 Are primary flows (chat message, research create, research refine) each covered by at least one acceptance scenario? [Coverage, Spec §US1–US3]
- [ ] CHK037 Are alternate flows (summary-only, Q&A-only, no article update) explicitly required for research? [Coverage, Spec §US2 scenario 2, FR-004]
- [ ] CHK038 Are exception flows defined for missing/invalid search credentials, empty model output, and structured output failure? [Coverage, Spec §Edge Cases, US2 scenario 3]
- [ ] CHK039 Are recovery flows defined for SSE reconnect with event replay scope? [Gap, Spec §Edge Cases — replay window/buffer duration not quantified]
- [ ] CHK040 Are recovery flows defined for application restart during active runs? [Coverage, Spec §Edge Cases, FR-017, SC-006]
- [ ] CHK041 Are recovery flows defined for Auth0 JWKS rotation without redeploy? [Coverage, Spec §Edge Cases, FR-018, Plan §Phase A]
- [ ] CHK042 Is the frontend impact of new 409 responses documented as a compatibility note (SHOULD handle)? [Coverage, Contracts §api-stability, Gap — spec silent on frontend obligation]

---

## Edge Case Coverage

- [ ] CHK043 Are requirements defined for research stop mid-stream when article preview was emitted but structured outcome incomplete? [Edge Case, Spec §Edge Cases partial stop, Gap — preview vs version conflict]
- [ ] CHK044 Are requirements defined when projection and agent session store temporarily diverge during streaming? [Gap, Data Model §Invariant — sync timing not specified]
- [ ] CHK045 Are requirements defined for users at exactly 10 active runs starting an 11th via session create vs message submit paths? [Edge Case, Spec §SC-011, Tasks §T035]
- [ ] CHK046 Are requirements defined for backfill when agent store already has partial data for a session? [Gap, Assumptions §backfill idempotency only in tasks, not spec]
- [ ] CHK047 Is single-replica SSE limitation documented as an accepted tradeoff with criteria for revisiting? [Edge Case, Assumptions, Plan §Risks]

---

## Non-Functional Requirements

- [ ] CHK048 Are performance targets specified separately for chat (60s) and research (300s) timeouts with user-facing messages? [NFR, Spec §FR-008, Settings context Plan]
- [ ] CHK049 Are security requirements for owner-scoped runs, streams, and stops unchanged and explicitly preserved? [NFR, Spec §FR-011, Constitution §Auth0]
- [ ] CHK050 Are logging requirements defined to exclude secrets/tokens while covering run lifecycle? [NFR, Spec §FR-012]
- [ ] CHK051 Are telemetry opt-out requirements independent of optional third-party tracing? [NFR, Spec §FR-020]
- [ ] CHK052 Are deployment constraints (no new Railway services, health check preserved) stated as requirements not just plan notes? [NFR, Constitution §Deployment, Plan §Technical Context]

---

## Dependencies & Assumptions

- [ ] CHK053 Are external provider dependencies (OpenRouter, Tavily, Auth0, LangWatch) listed with failure-mode expectations? [Dependencies, Spec §Assumptions, Edge Cases]
- [ ] CHK054 Is the Agno 2.4+ version constraint documented as an assumption with pin rationale? [Assumption, Plan §Technical Context, Tasks §T001]
- [ ] CHK055 Is the "no frontend release for v1" assumption consistent with new 409 responses and unchanged SSE names? [Assumption, Spec §Assumptions, Contracts]
- [ ] CHK056 Are migration/backfill dependencies called out as deploy-order requirements for big-bang release? [Dependencies, Tasks §T027, T046–T047, Gap in spec]

---

## Ambiguities & Conflicts

- [ ] CHK057 Is research `reasoning_content` storage and SSE `reasoning` event policy aligned with "never expose raw chain-of-thought to end users" in constitution? [Ambiguity, Constitution vs Spec §US6, Plan §event_mapper]
- [ ] CHK058 Does FR-016 (reuse agent instances) conflict with per-run session_id/user_id isolation requirements? [Conflict check, Spec §FR-016, FR-005]
- [ ] CHK059 Is "incremental internally but big-bang externally" clearly bounded so tasks don't imply partial production rollout? [Ambiguity, Spec §Assumptions vs Tasks §MVP Scope]
- [ ] CHK060 Are SSE event payload minimum keys in contracts sufficient for all refactored event sources without undefined optional fields? [Gap, Contracts §SSE Event Contract vs Plan §event_mapper mapping table]

---

## Notes

- Complements [requirements.md](./requirements.md) (spec authoring gate, already passed)
- Use before `/speckit.implement`; resolve `[Gap]` and `[Ambiguity]` items in spec/plan/contracts first
- Items CHK039, CHK043–CHK044, CHK046, CHK056, CHK060 flag documented gaps for optional spec amendment
