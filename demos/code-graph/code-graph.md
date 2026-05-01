=============================================================================
                     THE ULTIMATE AI SOFTWARE TEAM
=============================================================================

[User Request + Triage Gate] (User specifies intent: --new or --fix)
             │
             ├─────────────────────────────────────────────────┐
             ▼                                                 ▼
===========================================    ====================================
  PHASE 1: PERSPECTIVE (GREENFIELD PATH)         PHASE 1: PERSPECTIVE (REFACTOR PATH)
===========================================    ====================================
[1. PM Interrogator]                           [1. Blast Radius Mapper]
(Extracts edge cases, forces decisions)        (Scans git/AST to map dependencies,
             │                                  restricts context window)
[2. Parallel Context Researchers]                      │
(Scan old code for reuse opportunities)                │
             │                                         │
[3. Spec-Anchored PRD] (The Constitution)              │
             │                                         │
[4. Technical Designer] (Generates `shared.md`)        │
             │                                         │
[5. Human Gate] (Visual/manual approval)               │
             │                                         │
             └────────────────────┬────────────────────┘
                                  ▼
=============================================================================
                  PHASE 2: PROCESS (LOCAL EXECUTION LAYER)
=============================================================================
[6. Skeleton Scaffolder & TDD Enforcer]
(Generates directory structures, interfaces, and failing unit tests)
             │
             ▼
[7. Test Simplifier & Reviewer Gate]
(Strips bad mocks, enforces behavior-testing, locks tests as immutable ground truth)
             │
             ▼
[8. Adversarial Contract Generator]
(Writes black-box validation scripts: Playwright, Postman, Dockerized Bash)
             │
             ▼
[9. Task Sequencer]
(Translates spec/fix into `prd.json` task array, all marked "passes": false)
             │
             ▼
[10. THE ADVERSARIAL RALPH LOOP] ◄─────────────────────────────────────┐
             │                                                         │
             ├──► [Clean Headless Agent] (Writes code for one task)    │
             │                                                         │
             ├──► [Static Analysis Gate]                               │ (Loops
             │    (Fails instantly if empty diff or linter errors)     │  until
             │                                                         │  all
             ├──► [Local Test Gate]                                    │  tasks
             │    (Runs locked unit/integration tests)                 │  pass)
             │                                                         │
             └──► [Adversarial Sandbox]                                │
             │    (Executes the black-box contracts to try and break it│
             │                                                         │
             └─────────────────────────────────────────────────────────┘
             │
             ▼
[11. The Code Simplifier]
(Refactors passing implementation code for DRY/readability without altering logic)
             │
             ▼
[12. Atomic Commit & Push]
             │
             ▼
=============================================================================
                 PHASE 3: ENVIRONMENT (GITHUB ACTIONS CI/CD LAYER)
=============================================================================
[13. Standard CI/CD Pipeline] 
(Linters, build checks, standard test suites)
             │
             ├──► [IF FAILS] ──► [13a. The CI Auto-Fixer]
             │                   (Reads stdout logs, patches bug, pushes fix)
             │
             └──► [IF PASSES]
                         │
                         ▼
[14. Parallel Ensemble Reviewers]
  ├──► [Security Agent: Checks for OWASP/injection flaws]
  ├──► [Performance Agent: Checks Big-O and memory leaks]
  └──► [Architecture Agent: Checks drift from `shared.md`]
                         │
                         ▼
[15. The Full Adversarial E2E Gauntlet]
(Spins up staging container. Runs the complete, untampered Playwright/Postman
suite to guarantee real-world survival before merge is allowed)
                         │
                         ├──► [IF FAILS] ──► [15a. PR AI Comments]
                         │                   (Sends failure logs via GitHub API
                         │                    back to local developer/Auto-Fixer)
                         │
                         └──► [IF PASSES]
                                     │
                                     ▼
[16. Specum Formatter]
(Compiles high-signal, fluff-free PR description with architectural diffs)
                                     │
                                     ▼
[17. Draft PR Created] 
(Awaiting final Human Merge)