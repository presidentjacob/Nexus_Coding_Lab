# Nexus lab evidence — November 10, 2026

## Contributors and participation
Ryan Minor requested completion with Codex assistance. Jacob Yepez authored the existing audit component in commit b5b7134. Codex integrated that component with lifecycle/notification code, added the check, and ran verification. Other team contributions remain to be confirmed. Ryan must confirm any classroom contributors and describe his own participation; none has been invented.

## Baseline
Teaching source pinned by the assignment: 75a8d145aa5bc0c92725197c0e4e9883491c542f.
Interpreter: Python 3.12.1. Commands below ran from nexus2.
- `python3 -B run_lab.py`: 8 tests, 4 passes and 4 failures (01, 02, 03, 08), exit 1.
- `python3 -B -m pytest tests`: 23 passed, exit 0.
Full original output: [contract](evidence-output/baseline-contract.txt), [regression](evidence-output/baseline-regression.txt).
An initial sandboxed pytest attempt could not create temporary files; rerunning with permitted filesystem access produced the baseline above.

## Our design decision
The chosen owner is InMemoryAuditStore, injected explicitly into CustomerLifecycleService. Its record_deactivation(customer_id, actor_id, reason) method appends an immutable DeactivationAuditRecord. records returns a list copy for inspection, and the lab adapter converts the actual entries to mappings. Actor.user_id maps to the audit field actor_id.

Order: authorize; find customer; trim and validate reason; deactivate and save; write audit; publish the public event. The synchronous notification subscriber runs during publish, after the audit exists. A notification exception still propagates while the customer remains inactive and the audit remains available. Rejected commands reach none of the writes.

Benefit: audit storage and the public notification path have separate ownership and dependencies. A new public subscriber cannot obtain the reason from this event. Cost: another dependency must be wired, and the service directly depends on a concrete in-memory implementation. A protocol could become useful with a real second backend; none is needed here.

Credible alternative: a service-owned list would reduce wiring but combine lifecycle and audit storage responsibilities. A subscriber on the same public bus is insufficient: it would require broadcasting the confidential information to public observers.

## Actual changes
- src/northstar/audit.py: Jacob’s existing immutable record and in-memory store retained unchanged.
- src/northstar/services.py: required audit constructor dependency; record after saving and before publishing; public payload contains only email, with customer identity retained on DomainEvent.
- src/northstar/notifications.py: exact generic deactivation message.
- lab/adapter.py: inject real audit store and map its real entries.
- tests/conftest.py: wire the new dependency.
- tests/test_lifecycle_service.py: change ONLY the old message expectation to `Your Atlas account has been deactivated.` R3 deliberately supersedes the previous reason-bearing expectation. The preserved pre-update run had 22 passes and that one failure; see [conflict](evidence-output/upstream-message-conflict.txt).
- lab/test_contract.py: preserve all eight supplied checks and add test_09.

Implemented: all R1–R5 behaviors in this prototype. No durable backend or recovery mechanism is proposed as implemented.

## Our added behavior check
Expected before implementation: a reason of `  abcde  ` must be accepted at the five-character trimmed boundary, retained as exactly `abcde` in one correctly attributed audit record, and absent from the public payload. This catches an erroneous <= 5 comparison or failure to trim the stored value. The added check failed against the starter because audit records were empty; [actual red run](evidence-output/added-check-before-fix.txt). It passes after implementation.

## Final execution evidence
- `python3 -B run_lab.py`: 9 tests, all OK, exit 0. [Full output](evidence-output/final-contract.txt).
- `python3 -B -m pytest`: 23 passed, exit 0. [Full output](evidence-output/final-regression.txt). Default pytest discovery covers the original tests; the separate lab runner covers the contract checks.
No remaining test failures. [Inspectable code diff](evidence-output/implementation.diff); the original commit is retained in Git history.

## Limitations and next step
Team baseline: presidentjacob/Nexus_Coding_Lab at b5b7134525cfbde00747c2d1a94ce2903f8c5240. The preexisting audit component was not yet connected; the actual baseline still had four contract failures.

The audit survives a notification exception in this process, not a restart. A private Python field is not production access control. Audit writes are assumed to succeed. Audit-write failure, concurrent calls, repeat-request deduplication and crash recovery are outside this lab. Each accepted invocation appends once, including an invocation for an already inactive customer; this is not deduplication. No database, encryption, new role, audit read API, retries or deployment was added.

Next check: use two different customers and actors, verify audit association and ordering, and attach a second public subscriber to verify that it only receives the sanitized event. Production adoption would require a separate discussion of durable auditing and failure atomicity.

## Individual PR starting points
These are design-review prompts supplied by Codex, not claims about Ryan’s thoughts or classroom discussion. Each student must write their own judgment.
- Initial claim to evaluate: a direct audit collaborator keeps the reason internal without widening the public event contract.
- Consequential design question: what remains if a synchronous notification raises after the customer is saved? Writing the audit before publish preserves the required evidence.
- Disposition to evaluate: retain the separate collaborator for explicit ownership, accepting wiring cost and in-memory lifetime.
- Ryan still needs to supply his actual initial claim, any real challenge, and his own assessment of the result.

No submission is due at November 10 class end. Save a local copy or accessible branch and share with any actual contributors.
