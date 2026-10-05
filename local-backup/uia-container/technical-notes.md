# Chromium UIA container-end investigation

## Status and evidence limits

Date: 2026-10-05.

**Candidate only: the clean-build keyboard comparison is still blocked by a locked Windows session.**
No new source NVDA or test Chrome instance was started while the session was locked.
Do not turn the unit results below into a claim that the pristine NVDA/Chrome reproduction or the candidate's browser tests passed.
No issue or pull request has been opened.

## What was actually observed

During end-to-end testing of a separate description-list feature, two Chrome/UIA tests failed when pressing comma at the beginning of the outer description list.
The list ended in a definition containing an ordinary nested unordered list.
The same tests passed with IAccessible2.
The UIA failures occurred before subsequent dynamic-count assertions, not in the accessible-name tests.

Actual recorded speech:

> list  with 1 item  bullet  Ordinary item  definition

Actual recorded braille region text:

> definition lst1 • Ordinary item lst end dlst end

Expected destination: the following button, “Toggle definition”.
See the explicitly labelled [earlier feature-run log excerpt](earlier-feature-run-excerpt.log).
This excerpt is not a log from the newly prepared official build or from the new attachment.

Separately, an earlier probe of Chrome's real UI Automation provider demonstrated the endpoint behaviour with **ordinary unordered lists as well as native description lists**, without depending on NVDA's new description-list roles:

| Operation | Ordinary unordered list | Description list |
| --- | --- | --- |
| Full element text from `RangeFromChild` | `• Alpha\n◦ Last nested item` | `Alpha\nDefinition\n• Last nested item` |
| Collapse End, expand Line | `◦ Last nested item` | `• Last nested item` |
| Collapse End, expand Character | `\n` | `\n` |
| Move one character forward, expand Line | `After ordinary` | `After description` |
| Compare container End to following button Start | -1 | -1 |

The comparison result -1 establishes ordering; it is **not** a measured character distance.
The one-character movement above was diagnostic, not the proposed production fix.

## Why this happens

The provider's element range can stop before the line separator following its last text.
The existing `script_movePastEndOfContainer` collapses that range at End, updates the browse-mode selection, then expands a line for speech.
For the observed endpoint, line expansion resolves onto the last line still inside the list.
The next character at the boundary is a newline, but that newline was not included in `RangeFromChild`.

This is a mismatch between the element endpoint and the next readable position, not evidence that the wrong enclosing list was selected.
Changing ancestor priority from an inner unordered list to an outer description list would be an unrelated and incorrect approach.
It is also not an accessible-name or ARIA role-normalization failure.

The relevant container-selection and navigation functions are unchanged between the description-list feature's original base and the official revision prepared here.
That, together with the ordinary-list provider probe and the unit control, is strong evidence that the boundary issue predates the feature.
**The requested pristine end-to-end confirmation is nevertheless still outstanding.**

## Official build provenance

* Official source: [c22a509337c0b94ac5459ab2a749eeeb9cb06116](https://github.com/nvaccess/nvda/commit/c22a509337c0b94ac5459ab2a749eeeb9cb06116), fetched from `nvaccess/master`.
* Source version: `2027.1.0dev`.
* Its pinned submodules were checked out recursively into an isolated worktree.
Only Git objects, not modified dependency worktrees or DLLs, were reused for clone acceleration.
* Separate Python 3.13.15 AMD64 virtual environment, synchronized from the official lockfile.
* Full `SCons -j4 source` build succeeded before editing any production source.
* The build deleted 99 tracked eSpeak `dictsource/*_emoji` inputs.
This is the official build's intentional `removeEmoji()` step, not an imported feature modification.
No other production source differed when the initial unit control ran.
* Officially built x64 remote DLL SHA-256: `9E057EB53DDDFE36BAB18561A2F197300E69024BCE42FBF78666799B7B22BA39`.
* Officially built x86 remote DLL SHA-256: `53987CAD51F23D67EC0311A3128D28BDA28408DBCFC2AFA1F6BB1E7FB358250E`.

Environment:

* Microsoft Windows 11 Pro 25H2, build 26200.9550, 64-bit.
The registry's legacy “Windows 10 Pro” product string is misleading; the OS caption was independently checked.
* Google Chrome 154.0.8037.97.
* Installed NVDA 2026.2 is available and remained running, but was not tested for this bug.
* wxPython 4.3.1; comtypes 1.4.16; Robot Framework 7.4.2; SCons 4.11.0.

## Candidate design

Independent branch: `fix/chromium-uia-container-end`, based on the official commit above, not on the description-list feature or backup branch.
Published candidate: [ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8](https://github.com/kastwey/nvda/commit/ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8).
The remote SHA and official parent were verified after pushing.

`ChromiumUIATreeInterceptor.getEnclosingContainerRange` delegates container and landmark selection to the existing implementation.
For the returned range it checks the character beginning exactly at the end.
It extends the range only when both conditions hold:

1. That character unit is LF, CR or CRLF, and its start equals the original container end.
2. Expanding a line at the endpoint starts before the endpoint, i.e. it still resolves onto preceding content rather than a separate following blank line.

The range is extended to the checked character unit's end.
The existing comma command then collapses at the next position itself.
The start of the container is unchanged, as are the shared navigation command, say-all handling, document-bottom logic, ancestor selection and other UIA hosts.

The second condition was added during review to preserve a blank line after a container whose range already includes its terminal newline.
There is no unconditional character move, whitespace-stripping loop, whole-document scan, new public API, new dependency, or change to accessible names.

## Validation completed

| Check | Result | What it establishes |
| --- | --- | --- |
| Full official source build | Pass | A separately built official runtime exists |
| Initial regression tests with production source still at the official commit | Expected assertion failures, no test errors | Existing code does not normalize the modelled boundary |
| Final 16 regression methods with exact official module text loaded into a separate unit-test process | 8 expected assertion failures, 0 errors | Same final tests reject the original implementation; one parametrized method contributes two failures |
| Final candidate regression methods | 16 pass | Candidate handles the modelled cases |
| Full candidate unit suite | 1,481 run, 5 skipped, no failures/errors | Full unit suite succeeds in the official dependency environment |
| Ruff lint and format | Pass | Changed Python files conform |
| Pyright and ty | Pass | No reported type errors in changed Python files |
| Translation-string check | Pass: 0 unexpected errors | Translator-comment checks succeed |
| Markdown lint | Pass | Candidate changelog conforms |
| Robot model parsing | Pass | Both prepared suites parse; not an execution pass |
| External runner safety checks with mocks | Pass | Locked sessions launch nothing; a simulated test exception triggers installed-NVDA restoration |
| Standalone HTML preview | Pass in integrated browser | Correct list hierarchy, button names, light/dark rendering and no overflow at 360 px |
| Clean official NVDA + real Chrome keyboard test | **Not run: locked session** | Still required |
| Candidate NVDA + real Chrome keyboard test | **Not run: locked session** | Still required |

The unit tests use `BasicTextInfo` and controlled boundary behaviour, not real COM text ranges.
The final official-module unit control loads source retrieved by `git show` in a separate process; it is explicitly not an installed/source NVDA launch.
The full test output includes five skips and benign pre-existing environment messages; “pass” does not mean every test was executed.

Coverage includes omitted LF/CR and a modelled CRLF character unit, ordinary following text, spaces, tabs, nonbreaking spaces, an embedded-object character, a supplementary Unicode character, already-complete ranges, subsequent blank lines, empty ranges, backward expansion at document end, nearest-container selection, landmark fallback, comma, shift+comma, document bottom and say-all resumption.

## Prepared real-browser validation

[The standalone page](container-navigation.html) has unordered, ordered, description and div-wrapped description lists, each ending in an ordinary nested list and followed by a clearly named button.
It has no script, external dependency or network requirement.

The external harness opens this actual page, rather than a similar generated fragment.
It forces IA2/UIA separately, records speech and braille for both direct comma navigation and a return from the inner list, and saves all observations before asserting.
Only the test helper's window-title matcher and Chrome launch arguments are adapted; NVDA production methods are not patched.

The prepared repository system tests use the existing Chrome framework and `chrome_list`/`chrome_container` tags.
Still required before submitting the issue/PR:

1. Run the external page against the pristine official checkout and record actual speech, braille, backend, source version and NVDA log.
2. Run exactly the same page against the candidate, then the repository's `chrome_list` suite.
3. Confirm following blank lines, adjacent content/controls, EOF, nested lists and line wrapping with the real provider.
4. Check Edge or explicitly leave its coverage unclaimed.
5. Review the fresh log for personal information before attachment.
6. Replace provisional wording in the bug-form draft with the measured pristine/candidate results.

The runner refuses to launch on a locked/unavailable Windows session.
When it does launch, it uses a fresh isolated Chrome profile and the standard NVDA system-test sandbox.
Its `finally` restores installed NVDA and terminates only Chrome processes using that exact test profile.
The spy captures speech without audible synthesis; a temporary silence during the run is expected.

At handoff, the isolated worktree has been returned to detached official `c22a509337c0b94ac5459ab2a749eeeb9cb06116` for the first real run.
The candidate is preserved on its remote branch; switching to it afterwards changes only the five committed fix/test/changelog files.
No native library change is part of the candidate.

## Related reports checked

No exact duplicate was identified in the targeted issue and PR searches performed; this is not a guarantee of exhaustive coverage.

| Report | Title | Relationship |
| --- | --- | --- |
| [#15732](https://github.com/nvaccess/nvda/issues/15732) | Redisign the container navigation in browse mode to avoid loss of information for the user | Requests different end-of-container behaviour; the candidate preserves current intended “move past” semantics |
| [#12808](https://github.com/nvaccess/nvda/issues/12808) | Some UIA text ranges have no apparent bottom | Related provider endpoint concerns, different review-navigation command |
| [#7382](https://github.com/nvaccess/nvda/issues/7382) | Unexpected behavior with table and container navigation for nested tables | Layout-table inclusion/ancestor eligibility issue, not this terminal-newline mismatch |

The changelog intentionally has no fabricated issue/PR number.
Add the real reference after human submission and triage.
