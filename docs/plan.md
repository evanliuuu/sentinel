# Sentinel plan

Sentinel is a local pipeline over a package-registry snapshot. It finds license changes and lookalike package names, applies each team's license policy, and answers which apps inherited a change.

The program enforces one rule. Every answer cites rows from the warehouse, and a team never sees another team's roots.

PRs land in this order. pr-model, pr-license, pr-squat, pr-scanners, pr-warehouse, pr-tenants, pr-airflow, pr-ask, pr-docs.

The checked-in fixture is the proof until a live deps.dev export is wired to the same jobs.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `pstack/skills/poteto-mode/playbooks/autopilot-stack.md`. The operator lands the stack bottom-up. Every PR stops at STACK-READY. No owner merges.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Read these from trunk at program start. Re-read them at every tick.
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-stack.md`
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/autopilot-full.md`
  - [ ] `git show origin/main:pstack/skills/swarm/SKILL.md`
  - [ ] `git show origin/main:cursor-team-kit/skills/control-cli/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `git show origin/main:pstack/skills/principle-sequence-verifiable-units/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/technical-writing/SKILL.md`
  - [ ] `git show origin/main:pstack/skills/no-comments/SKILL.md`
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Spawn one owner per PR with the full lifecycle the execution playbook names.
- [ ] Follow this dependency graph. Start dependent work only after its parent branch exists, and base each PR on its parent branch.
  - [ ] pr-model is first and branches from `main`.
  - [ ] pr-license after pr-model.
  - [ ] pr-squat after pr-license.
  - [ ] pr-scanners after pr-squat.
  - [ ] pr-warehouse after pr-scanners.
  - [ ] pr-tenants after pr-warehouse.
  - [ ] pr-airflow after pr-tenants.
  - [ ] pr-ask after pr-airflow.
  - [ ] pr-docs after pr-ask.
- [ ] Hold the file boundaries. pr-model touches only `pyproject.toml`, `src/sentinel/model.py`, `src/sentinel/cli.py`, `fixtures/**`, and `tests/test_model.py`.
- [ ] Hold the file boundaries. pr-license touches only `src/sentinel/license_changes.py` and `tests/test_license_changes.py`.
- [ ] Hold the file boundaries. pr-squat touches only `src/sentinel/lookalikes.py` and `tests/test_lookalikes.py`.
- [ ] Hold the file boundaries. pr-scanners touches only `src/sentinel/scanners.py`, `fixtures/tarballs/**`, and `tests/test_scanners.py`.
- [ ] Hold the file boundaries. pr-warehouse touches only `dbt/dbt_project.yml`, `dbt/models/package_version.sql`, `dbt/models/license_change.sql`, `dbt/models/lookalikes.sql`, `dbt/models/scanner_disagreement.sql`, and `dbt/models/schema.yml`.
- [ ] Hold the file boundaries. pr-tenants touches only `policies/**`, `dbt/models/tenant_exposure.sql`, and `tests/test_tenant_isolation.py`.
- [ ] Hold the file boundaries. pr-airflow touches only `airflow/**`.
- [ ] Hold the file boundaries. pr-ask touches only `src/sentinel/ask.py` and `tests/test_ask.py`.
- [ ] Hold the file boundaries. pr-docs touches only `docs/**`.
- [ ] Hold the review gate. pr-ask changes an interaction. It waits for the operator's review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`. If `command -v origin` succeeds and Origin can resolve the repository, use `origin pr` for every PR operation. Record any fallback to `gh`. Never require `gt`.
- [ ] Open the PR ready, never draft, per **Opening a PR**. Use the run's built-in PR tool when it has one, else `origin pr create --status open --base <base-branch>` or `gh pr create --base <base-branch>` according to the resolved forge. A stack child targets its parent branch.
- [ ] Run the repo's lint and typecheck once before the PR-facing push. Push with hooks on.
- [ ] Run `/deslop` before each commit and `/no-comments` before review.
- [ ] Triage every Bugbot and security-reviewer comment per `../references/bugbot-triage.md`.
- [ ] Rebase onto the parent branch before the code-ready report and babysit. Keep that merge base in fix rounds. Rebase again only at merge prep, on a `git merge-tree` conflict with the parent, or on a CI failure that comes from a change on the parent.

### Verdict and merge, for every PR

- [ ] A full swarm runs once, at the code-ready head. Another full swarm runs only for new behavior, a redesign, or a large new diff. A rebase, a merge-conflict resolution, or a minor fix gets a single verifier at the new head. Run each full swarm per `pstack/skills/swarm/SKILL.md`. One gates lane. The ten live lanes from the PR's **Verify, live** block. The perf lane from its **Verify, perf** block. Two or more audit lanes, each with its own focus, that read the diff and the receipts and distrust the PR body. The root audits the receipts in the STACK-READY report before the verdict.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner, including a defect that a lane filed as a note. A new head gets a fresh verdict, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`.
- [ ] Owners report STACK-READY and never merge. The root appends each clean PR in dependency order with its base set to its parent branch. The operator lands the stack bottom-up. Apply the patch-id rule from `playbooks/shipping.md` link by link.

### Boot recipe, for every live lane

Each live lane runs on its own cloud VM at the PR head. Drive through `control-cli` from `cursor-team-kit`.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] Create `.venv`, install the package with dev extras, and wait until `sentinel --help` exits 0.
- [ ] Deliver input only through control-cli commands. Read-only diagnostics are command stdout and row counts from the parquet or DuckDB files the command writes.
- [ ] Save every screenshot to `/tmp/swarm-<pr-id>/worker-<n>/<slug>.png` and return the paths with the report.

## Lock the domain model (pr-model)

**Depends on.** None.

**Files.**

- [ ] Create `pyproject.toml`.
- [ ] Create `src/sentinel/model.py`.
- [ ] Create `src/sentinel/cli.py`.
- [ ] Create `fixtures/snapshot.json`.
- [ ] Create `tests/test_model.py`.

**Build.**

- [ ] Add PackageVersion, LicenseChange, Lookalike, TeamPolicy, and TenantExposure in `src/sentinel/model.py`, keyed by system, name, and version.
- [ ] Add `sentinel fixture` in `src/sentinel/cli.py`. It loads `fixtures/snapshot.json` and rejects a duplicate grain or a missing license.
- [ ] Check in the fixture. widget moves from MIT at 1.0.0 to SSPL at 2.0.0. left-pad stays MIT. react is popular. raect is one character off react. app-a depends on widget. app-b depends on left-pad. alpha forbids SSPL and ships app-a. beta allows SSPL and ships app-b.

**You see.**

- [ ] `sentinel fixture` prints widget 2.0.0 with license SSPL and exits 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_model.py` gains the grain, the widget license pair, the raect and react pair, both team roots, a duplicate row, and a missing license. Run `.venv/bin/pytest tests/test_model.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `sentinel fixture` at trunk and head. Trunk has no command, so record that and gate a printed widget row plus exit code 0. Save `pr-model-lane-1.png`. Pass when the head print includes widget, 2.0.0, and SSPL.
- [ ] Lane 2. Run `sentinel fixture` and read the left-pad lines. Save `pr-model-lane-2.png`. Pass when 1.0.0 and 1.1.0 are both MIT.
- [ ] Lane 3. Run `sentinel fixture` and read the name list. Save `pr-model-lane-3.png`. Pass when both react and raect are present.
- [ ] Lane 4. Run `sentinel fixture --team alpha`. Save `pr-model-lane-4.png`. Pass when the only root is app-a.
- [ ] Lane 5. Run `sentinel fixture --team beta`. Save `pr-model-lane-5.png`. Pass when the only root is app-b.
- [ ] Lane 6. Run `sentinel fixture --snapshot fixtures/bad-duplicate.json`. Save `pr-model-lane-6.png`. Pass when the exit code is non-zero and the text says duplicate grain.
- [ ] Lane 7. Run `sentinel fixture --snapshot fixtures/bad-license.json`. Save `pr-model-lane-7.png`. Pass when the exit code is non-zero and the text says missing license.
- [ ] Lane 8. Run `sentinel fixture --snapshot fixtures/empty.json`. Save `pr-model-lane-8.png`. Pass when the exit code is non-zero and the text says empty snapshot.
- [ ] Lane 9. Run `sentinel fixture` twice and diff the stdout. Save `pr-model-lane-9.png`. Pass when the two prints are identical.
- [ ] Lane 10. Run `sentinel fixture` and read the dependency lines. Save `pr-model-lane-10.png`. Pass when app-a depends on widget and app-b depends on left-pad.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `sentinel fixture` on the checked-in snapshot, and the end state of a successful print.
- [ ] Probe. Time `sentinel fixture` at trunk and at head, interleaved. Trunk has no command, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no command, so the baseline is absent.
- [ ] Rule. Fail the head when the command exceeds 2 seconds or the exit code is not 0.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto `main` after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Find license changes (pr-license)

**Depends on.** pr-model.

**Files.**

- [ ] Create `src/sentinel/license_changes.py`.
- [ ] Create `tests/test_license_changes.py`.

**Build.**

- [ ] Add a Spark SQL job in `src/sentinel/license_changes.py` that orders versions and emits a row only when the SPDX license changes.
- [ ] Add `sentinel licenses`. It reads the fixture and writes `out/license_change.parquet`.

**You see.**

- [ ] `sentinel licenses` writes one row, widget 2.0.0, previous license MIT, license SSPL.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_license_changes.py` gains the widget change, the left-pad non-change, a single-version package, and a case-only MIT versus mit non-change. Run `.venv/bin/pytest tests/test_license_changes.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `sentinel licenses` at trunk and head. Trunk has no command, so record that and gate the widget parquet row plus exit code 0. Save `pr-license-lane-1.png`. Pass when the head row is widget 2.0.0 from MIT to SSPL.
- [ ] Lane 2. Read `out/license_change.parquet` after a fixture run. Save `pr-license-lane-2.png`. Pass when left-pad is absent.
- [ ] Lane 3. Print the output columns. Save `pr-license-lane-3.png`. Pass when the columns are system, name, version, previous_license, and license.
- [ ] Lane 4. Count output rows. Save `pr-license-lane-4.png`. Pass when the count is 1.
- [ ] Lane 5. Run the command twice and hash the parquet. Save `pr-license-lane-5.png`. Pass when the hashes match.
- [ ] Lane 6. Run on `fixtures/reversed.json` with the same versions shuffled. Save `pr-license-lane-6.png`. Pass when the widget row matches the normal run.
- [ ] Lane 7. Run on a snapshot whose only package has one version. Save `pr-license-lane-7.png`. Pass when the row count is 0 and the exit code is 0.
- [ ] Lane 8. Run on a snapshot that changes MIT to mit. Save `pr-license-lane-8.png`. Pass when the row count is 0.
- [ ] Lane 9. Run on `fixtures/empty-versions.json` that has packages and no versions. Save `pr-license-lane-9.png`. Pass when the exit code is non-zero.
- [ ] Lane 10. Run on the fixture and print previous_license and license for widget. Save `pr-license-lane-10.png`. Pass when both fields are non-empty.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `sentinel licenses` on the checked-in fixture, and the end state of a written parquet file.
- [ ] Probe. Time the command at trunk and at head, interleaved. Trunk has no command, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no command, so the baseline is absent.
- [ ] Rule. Fail the head when the command exceeds 90 seconds or the parquet file is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-model after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Find lookalike names (pr-squat)

**Depends on.** pr-license.

**Files.**

- [ ] Create `src/sentinel/lookalikes.py`.
- [ ] Create `tests/test_lookalikes.py`.

**Build.**

- [ ] Add a Spark SQL job in `src/sentinel/lookalikes.py` that compares new names to popular names inside the same first-letter block.
- [ ] Add `sentinel squats`. It writes `out/lookalikes.parquet` with name, popular_name, and edit_distance.

**You see.**

- [ ] `sentinel squats` writes raect against react with edit distance 1, and does not write react against itself.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_lookalikes.py` gains the raect hit, the react self-pair exclusion, a different-letter non-match, and a low-dependent non-match. Run `.venv/bin/pytest tests/test_lookalikes.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `sentinel squats` at trunk and head. Trunk has no command, so record that and gate the raect row plus exit code 0. Save `pr-squat-lane-1.png`. Pass when the head row pairs raect with react at distance 1.
- [ ] Lane 2. Read the output names. Save `pr-squat-lane-2.png`. Pass when widget is absent.
- [ ] Lane 3. Print the react rows. Save `pr-squat-lane-3.png`. Pass when react is not paired with react.
- [ ] Lane 4. Add fixture name zzz and rerun. Save `pr-squat-lane-4.png`. Pass when zzz is absent, because the first letter differs from react.
- [ ] Lane 5. Lower the popular threshold so left-pad qualifies, and add a name leftpad. Save `pr-squat-lane-5.png`. Pass when leftpad pairs with left-pad.
- [ ] Lane 6. Run twice and hash the parquet. Save `pr-squat-lane-6.png`. Pass when the hashes match.
- [ ] Lane 7. Run on a snapshot with no new names. Save `pr-squat-lane-7.png`. Pass when the row count is 0 and the exit code is 0.
- [ ] Lane 8. Print the score column. Save `pr-squat-lane-8.png`. Pass when every score is from 0 through 1 inclusive.
- [ ] Lane 9. Run with the popular set empty. Save `pr-squat-lane-9.png`. Pass when the row count is 0 and the exit code is 0.
- [ ] Lane 10. Print the output order. Save `pr-squat-lane-10.png`. Pass when rows are sorted by name.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `sentinel squats` on the checked-in fixture, and the end state of a written parquet file.
- [ ] Probe. Time the command at trunk and at head, interleaved. Trunk has no command, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no command, so the baseline is absent.
- [ ] Rule. Fail the head when the command exceeds 90 seconds or the parquet file is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-license after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Diff the scanners (pr-scanners)

**Depends on.** pr-squat.

**Files.**

- [ ] Create `src/sentinel/scanners.py`.
- [ ] Create `fixtures/tarballs/widget-2.0.0/**`.
- [ ] Create `fixtures/tarballs/mystery-1.0.0/**`.
- [ ] Create `tests/test_scanners.py`.

**Build.**

- [ ] Add `sentinel scan`. It reads `out/license_change.parquet`, opens each tarball, and records the deps.dev label, the licensee label, and the package.json label.
- [ ] Check in widget 2.0.0 where LICENSE says SSPL and package.json says MIT.
- [ ] Check in mystery 1.0.0 where the three labels all differ, and write the disagreement as unknown.

**You see.**

- [ ] `sentinel scan` writes a widget row whose note says the LICENSE file was trusted, and a mystery row whose note says unknown.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_scanners.py` gains the widget agreement of deps.dev and licensee, the package.json disagreement, the unknown mystery row, and the skip of left-pad. Run `.venv/bin/pytest tests/test_scanners.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `sentinel licenses` and then `sentinel scan` at trunk and head. Trunk has no scan command, so record that and gate the widget disagreement row. Save `pr-scanners-lane-1.png`. Pass when the head note for widget says the LICENSE file was trusted.
- [ ] Lane 2. Print the deps.dev label for widget. Save `pr-scanners-lane-2.png`. Pass when it is SSPL.
- [ ] Lane 3. Print the licensee label for widget. Save `pr-scanners-lane-3.png`. Pass when it is SSPL.
- [ ] Lane 4. Print the package.json label for widget. Save `pr-scanners-lane-4.png`. Pass when it is MIT.
- [ ] Lane 5. Print the mystery note. Save `pr-scanners-lane-5.png`. Pass when the note says unknown.
- [ ] Lane 6. Confirm left-pad is absent from `out/scanner_disagreement.parquet`. Save `pr-scanners-lane-6.png`. Pass when left-pad is absent.
- [ ] Lane 7. Run `sentinel scan` twice and hash the parquet. Save `pr-scanners-lane-7.png`. Pass when the hashes match.
- [ ] Lane 8. Point one changed package at a missing tarball. Save `pr-scanners-lane-8.png`. Pass when that package is marked missing and widget is still written.
- [ ] Lane 9. Print the columns. Save `pr-scanners-lane-9.png`. Pass when the columns include system, name, version, source, and label.
- [ ] Lane 10. Run scan before licenses, with no parquet present. Save `pr-scanners-lane-10.png`. Pass when the exit code is non-zero and the text says missing license changes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `sentinel scan` on the two checked-in tarballs, and the end state of a written disagreement file.
- [ ] Probe. Time the command at trunk and at head, interleaved. Trunk has no command, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no command, so the baseline is absent.
- [ ] Rule. Fail the head when the command exceeds 120 seconds or the disagreement file is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-squat after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Build the warehouse tables (pr-warehouse)

**Depends on.** pr-scanners.

**Files.**

- [ ] Create `dbt/dbt_project.yml`.
- [ ] Create `dbt/models/package_version.sql`.
- [ ] Create `dbt/models/license_change.sql`.
- [ ] Create `dbt/models/lookalikes.sql`.
- [ ] Create `dbt/models/scanner_disagreement.sql`.
- [ ] Create `dbt/models/schema.yml`.

**Build.**

- [ ] Add a dbt project on DuckDB that reads the parquet outputs and builds package_version, license_change, lookalikes, and scanner_disagreement.
- [ ] Contract license_change in `dbt/models/schema.yml`. Grain is system, name, and version. previous_license and license are required. dependent_count is zero or greater.

**You see.**

- [ ] `dbt build` in `dbt/` succeeds, and a query of license_change returns the widget row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `dbt/models/schema.yml` gains the grain test, the not-null tests, and the dependent_count bound. Run `.venv/bin/dbt build --project-dir dbt`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run the spark commands and then `dbt build` at trunk and head. Trunk has no dbt project, so record that and gate the widget row in license_change. Save `pr-warehouse-lane-1.png`. Pass when the head query returns widget 2.0.0 from MIT to SSPL.
- [ ] Lane 2. Count package_version. Save `pr-warehouse-lane-2.png`. Pass when the count equals the fixture version count.
- [ ] Lane 3. Query lookalikes for raect. Save `pr-warehouse-lane-3.png`. Pass when popular_name is react.
- [ ] Lane 4. Load a license_change row with a null previous_license and run `dbt build`. Save `pr-warehouse-lane-4.png`. Pass when the contract test fails.
- [ ] Lane 5. Load a negative dependent_count and run `dbt build`. Save `pr-warehouse-lane-5.png`. Pass when the contract test fails.
- [ ] Lane 6. Load a duplicate license_change key and run `dbt build`. Save `pr-warehouse-lane-6.png`. Pass when the grain test fails.
- [ ] Lane 7. Run `dbt build` twice. Save `pr-warehouse-lane-7.png`. Pass when the second run reports no new failure and the row count is unchanged.
- [ ] Lane 8. Print the columns of package_version. Save `pr-warehouse-lane-8.png`. Pass when tenant_id is absent.
- [ ] Lane 9. Query scanner_disagreement for mystery. Save `pr-warehouse-lane-9.png`. Pass when the note says unknown.
- [ ] Lane 10. Query license_change for left-pad. Save `pr-warehouse-lane-10.png`. Pass when the result is empty.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `dbt build` after the fixture parquet files exist, and the end state of a successful build.
- [ ] Probe. Time `dbt build` at trunk and at head, interleaved. Trunk has no project, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no dbt project, so the baseline is absent.
- [ ] Rule. Fail the head when `dbt build` exceeds 60 seconds or the widget row is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-scanners after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Apply team policies (pr-tenants)

**Depends on.** pr-warehouse.

**Files.**

- [ ] Create `policies/alpha.yml`.
- [ ] Create `policies/beta.yml`.
- [ ] Create `dbt/models/tenant_exposure.sql`.
- [ ] Create `tests/test_tenant_isolation.py`.

**Build.**

- [ ] Add `dbt/models/tenant_exposure.sql`. It takes a policy and the shared marts and emits team, root, and offending version. The SQL does not contain the strings alpha or beta.
- [ ] Add `policies/alpha.yml` and `policies/beta.yml` from the fixture teams.
- [ ] Add `tests/test_tenant_isolation.py`. It fails when an alpha row carries a beta root.

**You see.**

- [ ] After `dbt build`, alpha exposure contains widget 2.0.0 for app-a, and beta exposure has no rows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_tenant_isolation.py` gains the alpha hit, the empty beta result, a crossed-root failure, and a scan of shared SQL for team names. Run `.venv/bin/pytest tests/test_tenant_isolation.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Build the marts and query tenant_exposure at trunk and head. Trunk has no exposure model, so record that and gate the alpha widget row. Save `pr-tenants-lane-1.png`. Pass when alpha shows app-a and widget 2.0.0.
- [ ] Lane 2. Query beta exposure. Save `pr-tenants-lane-2.png`. Pass when the row count is 0.
- [ ] Lane 3. Insert an alpha row whose root is app-b and run the isolation test. Save `pr-tenants-lane-3.png`. Pass when the test fails.
- [ ] Lane 4. Search `dbt/models/package_version.sql`, `license_change.sql`, `lookalikes.sql`, and `tenant_exposure.sql` for alpha and beta. Save `pr-tenants-lane-4.png`. Pass when those strings are absent.
- [ ] Lane 5. Print `policies/alpha.yml`. Save `pr-tenants-lane-5.png`. Pass when SSPL is forbidden and the root is app-a.
- [ ] Lane 6. Add `policies/empty.yml` with no roots and build. Save `pr-tenants-lane-6.png`. Pass when that team has zero exposure rows.
- [ ] Lane 7. Run `dbt build` twice and count alpha rows. Save `pr-tenants-lane-7.png`. Pass when the count stays 1.
- [ ] Lane 8. Edit beta to forbid SSPL and rebuild. Save `pr-tenants-lane-8.png`. Pass when beta still has zero rows, because app-b does not depend on widget.
- [ ] Lane 9. Edit alpha to allow SSPL and rebuild. Save `pr-tenants-lane-9.png`. Pass when the alpha widget row disappears.
- [ ] Lane 10. Query every exposure row for root app-a. Save `pr-tenants-lane-10.png`. Pass when every such row has team alpha.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `dbt build` plus the isolation test, and the end state of the alpha exposure row.
- [ ] Probe. Time that pair at trunk and at head, interleaved. Trunk has no exposure model, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no exposure model, so the baseline is absent.
- [ ] Rule. Fail the head when the pair exceeds 60 seconds or the alpha widget row is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-warehouse after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Schedule the daily run (pr-airflow)

**Depends on.** pr-tenants.

**Files.**

- [ ] Create `airflow/dags/sentinel_daily.py`.
- [ ] Create `tests/test_dag_import.py`.

**Build.**

- [ ] Add a DAG named sentinel_daily that runs licenses, squats, scan, dbt build, and the exposure model, in that order, for one event date.
- [ ] Write each date under `out/dates/<event_date>/` so a rerun replaces that date instead of appending.

**You see.**

- [ ] `airflow dags list` includes sentinel_daily, and a fixture run for date 2026-01-15 exits 0 with the alpha widget row still present.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_dag_import.py` gains the task order, the date path, and a refusal to import when a team name appears in the DAG file. Run `.venv/bin/pytest tests/test_dag_import.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `airflow dags list` at trunk and head. Trunk has no DAG, so record that and gate the name sentinel_daily. Save `pr-airflow-lane-1.png`. Pass when the head list includes sentinel_daily.
- [ ] Lane 2. Print the task order. Save `pr-airflow-lane-2.png`. Pass when the order is licenses, squats, scan, dbt, and exposure.
- [ ] Lane 3. Run the DAG twice for 2026-01-15 and count license_change rows. Save `pr-airflow-lane-3.png`. Pass when the count is still 1.
- [ ] Lane 4. Force the licenses task to fail and run the DAG. Save `pr-airflow-lane-4.png`. Pass when dbt does not start.
- [ ] Lane 5. Run the DAG with event date 2026-01-16. Save `pr-airflow-lane-5.png`. Pass when output lands under `out/dates/2026-01-16/`.
- [ ] Lane 6. Run the DAG with a missing snapshot path. Save `pr-airflow-lane-6.png`. Pass when the run fails and names the missing path.
- [ ] Lane 7. Search `airflow/dags/sentinel_daily.py` for alpha and beta. Save `pr-airflow-lane-7.png`. Pass when those strings are absent.
- [ ] Lane 8. Run 2026-01-15 and 2026-01-16. Save `pr-airflow-lane-8.png`. Pass when the two output directories both exist and neither is empty.
- [ ] Lane 9. List files under `airflow/`. Save `pr-airflow-lane-9.png`. Pass when the DAG file is the only Python file.
- [ ] Lane 10. After a successful 2026-01-15 run, query alpha exposure. Save `pr-airflow-lane-10.png`. Pass when app-a and widget 2.0.0 are present.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of one fixture DAG run for one date, and the end state of the alpha exposure row.
- [ ] Probe. Time a one-date run at trunk and at head, interleaved. Trunk has no DAG, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no DAG, so the baseline is absent.
- [ ] Rule. Fail the head when the one-date run exceeds 5 minutes or the alpha widget row is missing.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-tenants after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Answer from the tables (pr-ask)

**Depends on.** pr-airflow.

**Files.**

- [ ] Create `src/sentinel/ask.py`.
- [ ] Create `tests/test_ask.py`.

**Build.**

- [ ] Add `sentinel ask`. It accepts a team and a question id, runs SQL only against license_change, lookalikes, scanner_disagreement, and tenant_exposure, and prints the claim, the SQL, and the row ids.
- [ ] Add a paragraph check. A sentence is rejected when it contains a package name or a count that is not in the result rows.

**You see.**

- [ ] `sentinel ask --team alpha --question inherited` prints app-a, widget 2.0.0, the SQL, and a row id. The beta run prints no rows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_ask.py` gains the alpha answer, the empty beta answer, an unknown team, a lookalike question, and a paragraph that cites a package not in the result. Run `.venv/bin/pytest tests/test_ask.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `sentinel ask --team alpha --question inherited` at trunk and head. Trunk has no ask command, so record that and gate the widget answer. Save `pr-ask-lane-1.png`. Pass when the head print includes app-a, widget, and 2.0.0.
- [ ] Lane 2. Read the alpha answer for a row id. Save `pr-ask-lane-2.png`. Pass when a row id is present and matches tenant_exposure.
- [ ] Lane 3. Read the printed SQL. Save `pr-ask-lane-3.png`. Pass when the SQL text is present and names tenant_exposure.
- [ ] Lane 4. Feed a paragraph that mentions react when the result is only widget. Save `pr-ask-lane-4.png`. Pass when the check rejects it.
- [ ] Lane 5. Run `sentinel ask --team beta --question inherited`. Save `pr-ask-lane-5.png`. Pass when the print says no rows and exits 0.
- [ ] Lane 6. Run `sentinel ask --team missing --question inherited`. Save `pr-ask-lane-6.png`. Pass when the exit code is non-zero.
- [ ] Lane 7. Run `sentinel ask --team alpha --question lookalikes`. Save `pr-ask-lane-7.png`. Pass when raect and react are present.
- [ ] Lane 8. Print every table the SQL reads. Save `pr-ask-lane-8.png`. Pass when the only tables are license_change, lookalikes, scanner_disagreement, and tenant_exposure.
- [ ] Lane 9. Run the alpha inherited question twice. Save `pr-ask-lane-9.png`. Pass when the two prints match.
- [ ] Lane 10. Read the inherited answer for app-b. Save `pr-ask-lane-10.png`. Pass when app-b is absent.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of one alpha inherited question against the built warehouse, and the end state of a printed row id.
- [ ] Probe. Time the ask command at trunk and at head, interleaved. Trunk has no command, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no ask command, so the baseline is absent.
- [ ] Rule. Fail the head when the command exceeds 5 seconds or the row id is missing.

**Review gate.** The operator reviews before merge.

- [ ] Copy lane 1 screenshots into `/cursor/stores/self/docs/media/pr-ask-review-ask.png`.
- [ ] Record a 30 to 60 second video of the change on a lane VM. Save it as `/cursor/stores/self/docs/media/pr-ask-review.mp4`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The operator has reviewed the screenshots and the video.
- [ ] The branch is rebased onto pr-airflow after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Write the contract and the recommendation (pr-docs)

**Depends on.** pr-ask.

**Files.**

- [ ] Create `docs/architecture.md`.
- [ ] Create `docs/license_change_contract.md`.
- [ ] Create `docs/recommendation.md`.
- [ ] Create `docs/agent_notes.md`.
- [ ] Create `docs/check_docs.py`.

**Build.**

- [ ] Write the architecture note for snapshot, Spark, dbt, policy, scanners, and ask.
- [ ] Write the license_change contract with the grain and the required fields.
- [ ] Write the recommendation from the fixture result. One license change, widget 2.0.0, app-a on team alpha. Name the mystery scanner case as unknown.
- [ ] Write four agent notes. Each has a task, an artifact, and a correction.
- [ ] Add `docs/check_docs.py`. It fails when the recommendation names a package or a count that the ask command did not return.

**You see.**

- [ ] `python docs/check_docs.py` exits 0, and the recommendation names widget and the count 1.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `docs/check_docs.py` gains the package-name check, the count check, and the unknown-case check. Run `.venv/bin/python docs/check_docs.py`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `grok-4.7-xhigh-fast` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `python docs/check_docs.py` at trunk and head. Trunk has no docs checker, so record that and gate an exit code of 0 plus the widget sentence. Save `pr-docs-lane-1.png`. Pass when the head checker exits 0 and the recommendation includes widget and the count 1.
- [ ] Lane 2. Invent the name not-a-package inside the recommendation and rerun the checker. Save `pr-docs-lane-2.png`. Pass when the checker fails.
- [ ] Lane 3. Read `docs/architecture.md` headings. Save `pr-docs-lane-3.png`. Pass when snapshot, Spark, dbt, policy, scanners, and ask are all named.
- [ ] Lane 4. Read `docs/license_change_contract.md`. Save `pr-docs-lane-4.png`. Pass when the grain is system, name, and version.
- [ ] Lane 5. Count entries in `docs/agent_notes.md`. Save `pr-docs-lane-5.png`. Pass when four entries each have a task, an artifact, and a correction.
- [ ] Lane 6. Change the recommendation count from 1 to 9 and rerun the checker. Save `pr-docs-lane-6.png`. Pass when the checker fails.
- [ ] Lane 7. Read the recommendation for a claimed registry-wide row count. Save `pr-docs-lane-7.png`. Pass when the only count is the fixture count returned by ask.
- [ ] Lane 8. Read the recommendation for app-b under alpha. Save `pr-docs-lane-8.png`. Pass when that pairing is absent.
- [ ] Lane 9. Run the checker twice. Save `pr-docs-lane-9.png`. Pass when both exits are 0.
- [ ] Lane 10. Read the recommendation for the mystery package. Save `pr-docs-lane-10.png`. Pass when the note says unknown.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall clock of `python docs/check_docs.py`, and the end state of exit code 0.
- [ ] Probe. Time the checker at trunk and at head, interleaved. Trunk has no checker, so record absent there and still time the head.
- [ ] Baseline. Record the trunk value first. Trunk has no checker, so the baseline is absent.
- [ ] Rule. Fail the head when the checker exceeds 5 seconds or the exit code is not 0.

**Review gate.** None. is not review-gated.

**Merge.**

- [ ] Root records a clean verdict at the exact head SHA.
- [ ] Bugbot triage is done.
- [ ] The branch is rebased onto pr-ask after the verdict and the patch id is unchanged.
- [ ] The root appends this PR to the stack and the operator lands it bottom-up.

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the stack root, the stack tip, a one-line verdict per PR, and anything parked, per the autopilot-stack playbook.

## Appendix A. Prototype evidence

No prototype branch exists. The repository has only its initial commit, and this plan was written before any job ran.

These questions stay unproven.

- Local PySpark can read the fixture and finish the license and lookalike jobs inside the perf budgets.
- licensee and ScanCode can be installed on a lane VM and match the canned widget labels.
- A deps.dev export can replace `fixtures/snapshot.json` without a change to the job interfaces.
- `git show origin/main:<skill>` works only if those skill files are on the sentinel trunk. They are not on the trunk today. Owners read the playbooks from the pstack checkout until that changes.

## Appendix B. Alternatives rejected

A single PR that lands Spark, dbt, Airflow, scanners, and the question command together. A reviewer cannot see which step produced the widget row.

A live BigQuery read on every PR. The fixture already contains the one license change and the one lookalike the later PRs must show. The export is an input swap, not a new behavior.

A web page for questions. The interview demo is the printed claim, SQL, and row ids. A page would add a second surface before the CLI is proven.

Independent PRs that each branch from main. The warehouse cannot build until the parquet writers exist, so the work is one stack.

Computing the full npm transitive closure inside Spark. deps.dev already publishes dependency edges. The jobs score versions, then join only the roots in the team policy.

## Appendix C. Risks

- pr-license and pr-squat. PySpark may exceed the 90 second fixture budget on a cold VM. The owner records the measured time and raises the budget only with that measurement.
- pr-scanners. Scanner binaries may be missing. The unit tests use the canned tarball labels. The live lanes install the tools. A missing binary is a failed lane, not a skipped one.
- pr-airflow. Airflow install time can dominate the 5 minute run budget. The owner times install separately from the DAG run and reports both.
- pr-ask. The review gate blocks the stack above it until the operator watches the video.
- pr-docs. The recommendation can drift from the fixture. `docs/check_docs.py` is the guard, and it must call the same ask result the reader sees.
- Program start. Skill paths in the arm list are not on sentinel trunk. See Appendix A.

## Appendix D. Links and reading list

Read `https://docs.deps.dev/bigquery/v1` before changing a column name. The tables in use are PackageVersions, Dependencies, and Dependents in `bigquery-public-data.deps_dev_v1`.

pr-license, pr-squat, and pr-scanners get `pstack/skills/how/SKILL.md` on the fixture shape and `pstack/skills/interrogate/SKILL.md` on the diff. pr-ask gets interrogate because it is the review-gated interaction.

Keep the decision trail with `pstack/skills/show-me-your-work/SKILL.md` at `/cursor/stores/self/docs/sentinel-decisions.tsv`.
