# Mobile UX Checklist: Mobile Home and Research Pages

**Purpose**: Validate requirements quality for mobile/responsive UX before implementation and PR review — unit tests for the English in spec, plan, and contracts
**Created**: 2026-05-21
**Feature**: [spec.md](../spec.md) · [mobile-ui.md](../contracts/mobile-ui.md) · [plan.md](../plan.md)

**Note**: Items evaluate whether requirements are complete, clear, consistent, and measurable — not whether the implementation works.

**Defaults applied** (no `/speckit-checklist` arguments provided): Standard depth · PR reviewer audience · Focus: mobile UX, navigation, research workspace tabs

---

## Requirement Completeness

- [ ] CHK001 Are mobile layout requirements defined for every in-scope page (`/`, `/research/{sessionId}`) with explicit viewport boundary? [Completeness, Spec §FR-001–FR-004, Clarifications §768px]
- [ ] CHK002 Are shared navigation requirements documented for all authenticated pages including `/chat`? [Completeness, Spec §FR-008, FR-012, Clarifications]
- [ ] CHK003 Are requirements specified for all primary home-page interactions on mobile (compose, submit, list tabs, pagination, page size, session open, delete)? [Completeness, Spec §FR-002, User Story 1]
- [ ] CHK004 Are requirements specified for all primary research-workspace interactions on mobile (thread view, article view, stop, retry, follow-up, article controls)? [Completeness, Spec §FR-005–FR-007, User Story 2]
- [ ] CHK005 Are loading, empty, error, and submitting state requirements inherited or explicitly restated for mobile contexts? [Completeness, Spec §FR-002, Contract §Home Page States]
- [ ] CHK006 Are resize/rotation transition requirements documented separately from initial mobile load? [Completeness, Spec §FR-010, User Story 4]
- [ ] CHK007 Are out-of-scope boundaries explicitly documented for chat content layout vs. shared navigation? [Completeness, Spec §FR-012, Assumptions]
- [ ] CHK008 Are article-ready notification requirements defined for mobile tab UX (not just desktop dual-panel visibility)? [Completeness, Spec §FR-013, Clarifications]

---

## Requirement Clarity

- [ ] CHK009 Is the mobile/desktop breakpoint quantified as a single numeric threshold without conflicting ranges? [Clarity, Spec §FR-010, Assumptions, Contract §Global Rules]
- [ ] CHK010 Is the research workspace mobile pattern named explicitly (top tabs) with tab labels documented? [Clarity, Spec §FR-004, Clarifications, Contract §Research Workspace]
- [ ] CHK011 Is hamburger navigation structure defined with exact top-bar elements and drawer contents? [Clarity, Spec §FR-008, Contract §Shared Navigation]
- [ ] CHK012 Is "touch-friendly sizing" quantified with a minimum dimension requirement? [Clarity, Spec §FR-009, SC-003, Contract §Global Rules]
- [ ] CHK013 Is "no horizontal page scroll" defined with scope (page-level vs. in-pane content scroll)? [Clarity, Spec §Edge Cases, Contract §Global Rules]
- [ ] CHK014 Is article tab badge behavior defined for set, persist, and clear conditions? [Clarity, Spec §FR-013, User Story 2 §scenario 5]
- [ ] CHK015 Is "readable typography" for article markdown on mobile defined with content types enumerated? [Clarity, Spec §FR-006, User Story 2 §scenario 3]
- [ ] CHK016 Is default active tab on workspace load explicitly stated? [Clarity, User Story 2 §scenario 1, Contract §Workspace tabs]

---

## Requirement Consistency

- [ ] CHK017 Do breakpoint values align across spec assumptions, functional requirements, success criteria, and UI contract? [Consistency, Spec §Assumptions, FR-010, SC-001/SC-002, Contract §Global Rules]
- [ ] CHK018 Do navigation requirements align between User Story 3 acceptance scenarios and FR-008? [Consistency, Spec §User Story 3, FR-008]
- [ ] CHK019 Do research workspace tab requirements align between clarifications, FR-004, FR-013, and mobile-ui contract? [Consistency, Clarifications, Spec §FR-004/FR-013, Contract §Research Workspace]
- [ ] CHK020 Are desktop preservation requirements consistently stated as "unchanged at 768px+" across home, research, and nav sections? [Consistency, Spec §Assumptions, Contract §Desktop sections]
- [ ] CHK021 Do scope statements about `/chat` agree between FR-012, assumptions, User Story 3, and contract? [Consistency, Spec §FR-012, Assumptions, Contract §Chat Page]
- [ ] CHK022 Are delete-action visibility requirements consistent between home list edge cases and FR-002 mobile behavior? [Consistency, Spec §FR-002, Contract §Home Page research list]

---

## Acceptance Criteria Quality

- [ ] CHK023 Can SC-001 and SC-002 be objectively verified with defined viewport range and task list? [Measurability, Spec §SC-001, SC-002]
- [ ] CHK024 Is the 44×44px touch target criterion expressed as a measurable percentage (95%) with defined control scope? [Measurability, Spec §SC-003]
- [ ] CHK025 Is SC-004 measurable without implementation detail (zero page reloads, state intact)? [Measurability, Spec §SC-004, User Story 4]
- [ ] CHK026 Is SC-005 defined with a time bound and evaluation method despite qualitative framing? [Measurability, Spec §SC-005]
- [ ] CHK027 Does each P1 user story include an independent test statement decoupled from other stories? [Acceptance Criteria Quality, Spec §User Stories 1–2]

---

## Scenario Coverage

- [ ] CHK028 Are primary mobile flows covered: start research from home, open session, follow generation, read article? [Coverage, User Stories 1–2]
- [ ] CHK029 Are alternate flows covered: switch Drafts/Published, change pagination, switch Thread/Article tabs mid-session? [Coverage, User Stories 1–2]
- [ ] CHK030 Are exception flows covered: empty submit, agent error/retry, unauthenticated access? [Coverage, Spec §Edge Cases, FR-002, FR-005]
- [ ] CHK031 Are recovery flows defined for generation stopped mid-run on mobile? [Coverage, Spec §Edge Cases, Contract §Research Workspace States]
- [ ] CHK032 Are concurrent-interaction scenarios addressed (switch tabs during active generation, drawer open + profile menu)? [Coverage, Spec §Edge Cases, Contract §Nav States]
- [ ] CHK033 Are resize/rotation scenarios classified as a distinct user story with acceptance criteria? [Coverage, User Story 4]

---

## Edge Case Coverage

- [ ] CHK034 Are long session title requirements defined for truncation and discoverability of full title? [Edge Case, Spec §Edge Cases]
- [ ] CHK035 Are long message thread requirements defined for scroll vs. sticky control placement? [Edge Case, Spec §Edge Cases, Contract §Thread tab]
- [ ] CHK036 Are wide markdown element requirements defined (tables, code, ASCII) with in-pane vs. page scroll boundary? [Edge Case, Spec §Edge Cases, FR-006]
- [ ] CHK037 Is minimum supported viewport width (320px) explicitly addressed in requirements? [Edge Case, Spec §Edge Cases, SC-001]
- [ ] CHK038 Are empty research list and empty article states addressed for mobile layout? [Edge Case, Spec §Edge Cases, Contract §Home/Research States]
- [ ] CHK039 Are requirements defined for badge behavior when user is already on Article tab at completion? [Edge Case, Gap, Spec §FR-013, data-model §WorkspaceMobileState]

---

## Non-Functional Requirements

- [ ] CHK040 Are accessibility requirements specified for hamburger drawer and workspace tabs beyond implementation guidance? [Non-Functional, Gap, Contract §Accessibility]
- [ ] CHK041 Are focus management requirements defined for drawer open/close lifecycle? [Non-Functional, Gap, Contract §Accessibility]
- [ ] CHK042 Are performance or latency requirements defined for tab switching and resize reflow? [Non-Functional, Gap, Plan §Performance Goals]
- [ ] CHK043 Are authentication and authorization requirements explicitly scoped as unchanged for mobile presentation? [Non-Functional, Spec §FR-011, Constitution §Auth0]
- [ ] CHK044 Are iOS/Android mobile browser viewport quirks (dynamic chrome, `dvh`) documented as assumptions or requirements? [Non-Functional, Assumption/Gap, Plan §Risks]

---

## Dependencies & Assumptions

- [ ] CHK045 Is dependency on existing research UI contract (005) documented for baseline behaviors preserved on mobile? [Dependency, Spec §Assumptions, Contract preamble]
- [ ] CHK046 Is the assumption that mobile means `<768px` (not tablet-specific rules) stated and bounded? [Assumption, Spec §Assumptions]
- [ ] CHK047 Are backend/API unchanged assumptions explicit to prevent scope creep into mobile-specific endpoints? [Assumption, Spec §FR-011, Plan §Summary]
- [ ] CHK048 Is deployment/verification dependency on manual viewport testing documented with breakpoint spot-check matrix? [Dependency, quickstart.md, Plan §Phase D]

---

## Ambiguities & Conflicts

- [ ] CHK049 Is "phone-sized screen" terminology consistently mapped to the 768px threshold throughout all user stories? [Ambiguity, Spec §User Stories vs. Assumptions]
- [ ] CHK050 Does any requirement imply auto-switch to Article tab that conflicts with FR-013 stay-on-Thread rule? [Conflict, Spec §FR-013 vs. Edge Cases]
- [ ] CHK051 Is "equivalent single-pane pattern" language fully eliminated after clarification in favor of explicit top tabs? [Ambiguity, Spec §Assumptions post-clarify]
- [ ] CHK052 Are deferred accessibility items from clarification session tracked as known gaps vs. silent omissions? [Gap, Clarify coverage summary §Accessibility]

---

## Notes

- Check items off as completed: `[x]`
- `[Gap]` items flag missing requirements to add to spec/contract before implementation
- Items referencing Contract assume `specs/006-mobile-pages/contracts/mobile-ui.md`
- Pair with existing [requirements.md](./requirements.md) (spec authoring gate) — this checklist focuses on mobile UX requirement depth

---

## Post-Remediation Delta (2026-05-21)

*Validates requirement quality after analyze remediation (FR-014, SC-003 audit, badge edge case, terminology alignment).*

### Requirement Completeness

- [ ] CHK053 Is FR-014 documented with sufficient detail for drawer focus-trap and tab ARIA without relying solely on the contract? [Completeness, Spec §FR-014, Contract §Accessibility]
- [ ] CHK054 Are session-list row tap-target requirements traceable from User Story 1 scenario 3 through to an implementation task? [Completeness, Spec §User Story 1, tasks.md T008]
- [ ] CHK055 Is the SC-003 verification process defined end-to-end (spec criterion → quickstart inventory → audit artifact → task)? [Completeness, Spec §SC-003, quickstart.md, tasks.md T021]

### Requirement Clarity

- [ ] CHK056 Is the Article-tab-already-active badge exception stated consistently in edge cases, FR-013, User Story 2 scenario 7, and contract states table? [Clarity, Spec §FR-013, Edge Cases, Contract §Research Workspace States]
- [ ] CHK057 Is the minimum tap-target dimension (44×44px) linked explicitly to session row links and list controls—not only buttons? [Clarity, Spec §FR-009, User Story 1 §3, tasks.md T008]
- [ ] CHK058 Does SC-001/SC-002 sample-width language (320, 375, 767) clearly represent the full `<768px` mobile range rather than limiting scope to those widths only? [Clarity, Spec §SC-001, SC-002]

### Requirement Consistency

- [ ] CHK059 Is viewport terminology ("viewports below 768px") used consistently across user stories, FRs, SCs, and assumptions without residual "phone-sized" drift? [Consistency, Spec §Assumptions line 146 vs. Assumptions line 145]
- [ ] CHK060 Do FR-014 accessibility requirements align with contract implementation guidance without contradiction? [Consistency, Spec §FR-014, Contract §Accessibility]
- [ ] CHK061 Are home-page resize requirements in User Story 4 scenario 2 reflected in quickstart and tasks (not only research workspace)? [Consistency, Spec §User Story 4, quickstart.md, tasks.md T016]

### Acceptance Criteria Quality

- [ ] CHK062 Does SC-003 name a concrete verification artifact (`touch-target-audit.md`) and pass-rate threshold? [Measurability, Spec §SC-003, tasks.md T021]
- [ ] CHK063 Can the ≥95% SC-003 pass rate be computed from a defined control inventory in quickstart? [Measurability, quickstart.md §Touch Target Spot Check]

### Scenario Coverage

- [ ] CHK064 Is the alternate completion path (user already on Article tab) covered in both acceptance scenario and functional requirement? [Coverage, Spec §User Story 2 §7, FR-013]

### Non-Functional Requirements

- [ ] CHK065 Are workspace tab accessibility requirements specified in FR-014 beyond drawer focus management? [Non-Functional, Spec §FR-014, Gap if tabs omitted]
- [ ] CHK066 Is keyboard Escape-to-close for the nav drawer specified at requirements level (not only in contract/tasks)? [Non-Functional, Gap, Contract §Shared Navigation, tasks.md T003]

### Dependencies & Assumptions

- [ ] CHK067 Is the touch-target audit checklist (`touch-target-audit.md`) scoped as a release gate deliverable tied to SC-003? [Dependency, tasks.md T021, checklists/touch-target-audit.md]

### Ambiguities & Conflicts

- [ ] CHK068 Does Assumption line 146 ("Phone-sized viewports") conflict with normalized "viewports below 768px" terminology elsewhere? [Conflict, Spec §Assumptions]
- [ ] CHK069 Are original gap items CHK039–CHK041 from the pre-remediation checklist now resolved in spec/tasks, or do residual gaps remain? [Traceability, compare CHK039–CHK041 vs. Spec §FR-013/FR-014]

---

## Notes (Post-Remediation)

- Items CHK049, CHK039 (badge-on-Article-tab), CHK040–CHK041 (accessibility) may pass after reviewing CHK053–CHK069
- `touch-target-audit.md` is an implementation deliverable, not a requirements-quality checklist — T021 fills results at release time
