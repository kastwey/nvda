# Local work backup — 5 October 2026

This branch is a recovery snapshot, not a pull-request branch.
The description-list implementation is saved separately in
`fix/description-lists-3858`, commit `7cf80258277b596a85bb23af383ece1eba2be5df`.
Its parent, before the feature changes, is `c43cf6c1b0518326bd9ff0ed4712474feeb6131c`.

## Included work

* The implementation, regression tests and user documentation from the feature branch.
* The four local Spanish explanation/reproduction documents in `projectDocs/issues/`.
* The hand-written accessible-name diagnostic page and Python probe in `local-backup/diagnostics/`.
* The local VS Code tasks configuration in `local-backup/vscode-tasks.json`.
* The dependency checkout positions below, without modifying the live dependency repositories.
* An eSpeak patch recording all local tracked-file deletions.
* A patch for the only local edit inside the nested CLDR staging repository.
* A source archive of the local generated nvda-cldr commit, so recovery does not depend on its availability on a remote branch.
* A source archive of the clean, formerly untracked nvda_dmp checkout.

Generated native binaries, virtual environments, caches, and raw NVDA/Robot logs are not published.
Raw logs can contain personal window titles and other session information.
They remain untouched in the original local checkout.

## Dependency recovery information

The three changed submodule pointers are recorded in this backup commit, not in the feature commit.

| Local path | Repository | Checked-out commit | Local changes |
| --- | --- | --- | --- |
| `include/espeak` | <https://github.com/espeak-ng/espeak-ng> | `b0b605c8a80f76c4c19e18033c6780c3cc4afc5b` | Apply `espeak-worktree.patch` from that repository root. |
| `include/liblouis` | <https://github.com/liblouis/liblouis> | `2aa5f84b14de17bcfe8317862d11f6bd7d640e55` | None. |
| `include/nvda-cldr` | <https://github.com/nvaccess/nvda-cldr> | `6d3ba86c3963f023550a4b1aa8160945e77ca423` | Generated checkout; full source is in `nvda-cldr-6d3ba86.tar.gz`. |
| `include/nvda-cldr/cldr` | <https://github.com/unicode-org/cldr-staging> | `fda5b28295ef1ef2dbe5e39f991928aa7514f04c` | Apply `cldr-staging-worktree.patch` from this nested repository root. |
| `include/nvda_dmp` | <https://github.com/codeofdusk/nvda_dmp> | `6a97cc7809e4596d14a9aa6d7fc5542b1cd3c4d3` | None; source archived in `nvda-dmp-6a97cc7.tar.gz`. Not added as a new NVDA dependency. |
| `.vscode` | <https://github.com/nvaccess/vscode-nvda> | `22faeb775256e4e8fa9ba2d650da1666489ceaaf` | Copy `vscode-tasks.json` to this checkout as `tasks.json`. |

All other initialized submodules match the recorded feature-branch gitlinks and have no local tracked/untracked changes.

## Validation at snapshot time

* 76 focused Python unit tests pass.
* Both accessible-name Chrome system tests pass with real NVDA, IA2 and UIA, speech and braille.
* The broader Chrome list suite has 9 passes and 2 failures: UIA moving past a container can stay on its last line.
  These failures are retained for investigation; the suite is not claimed to be green.
* The native-runtime build succeeded and the changed x86/x64 DLLs were verified.
* The full source build stopped on a missing eSpeak dictionary in the local dependency checkout.
  This backup preserves that state; it does not pretend the dependency checkout is a clean baseline.

Do not merge this recovery branch into an upstream pull request.

## Independent Chromium UIA container candidate

The follow-up investigation and issue-form materials are backed up in `uia-container/`.
The candidate code is on `fix/chromium-uia-container-end`, commit
`ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8`, based directly on official
`c22a509337c0b94ac5459ab2a749eeeb9cb06116`, not on this recovery branch.

The official source build and all 1,481 candidate unit tests (five skips) succeeded.
The real clean-build/candidate browser comparison is still pending: Windows was locked,
and the lock screen was not bypassed. The issue-form draft clearly preserves this limitation.
No issue or PR has been opened. Only a narrowly selected earlier log excerpt is included;
full private NVDA/Robot logs are not published.
