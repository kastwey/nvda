# Bug-report form draft

**Verified on 2026-10-05: the unchanged official source reproduces the bug; the independent fix passes the same browser tests.**
The report is ready for your review and manual submission through the form.
Read [the Spanish submission checklist](README.es.md) before using it.
Copy each section's content into its matching field in the **Bug report form**, not into a blank issue.

## Suggested title

Chrome with UI Automation: comma can remain on the final nested list item instead of moving past the container

## Brief summary

In browse mode with Chromium accessed through UI Automation, moving past the end of a list can leave NVDA reading the list's final nested item instead of the content immediately after the outer list.
This is reproduced with unchanged official NVDA source, including ordinary unordered/ordered lists and description lists.
The equivalent IAccessible2 navigation works.

An independent candidate fix is prepared on official master, rather than on the description-list feature branch.
I plan to submit a pull request with the fix and regression tests after this report has been discussed/triaged.

## Steps to reproduce

These keyboard steps have been verified against the unchanged official source and the attached page:

1. Extract the attached reproduction ZIP and open its standalone HTML reproduction page in Google Chrome.
2. In NVDA Settings, open Advanced, acknowledge the warning about changing advanced settings, and set **Use UI Automation to access Microsoft Edge and other Chromium based browsers** to **Yes**.
Apply the change, close/reopen the test browser, and reopen the page.
3. Ensure NVDA is in browse mode, not focus mode; use NVDA+Space if necessary.
4. Press Control+Home, then **2** to reach the “Unordered list” level-two heading.
5. Press **L** once to enter the outer list at “Alpha unordered”.
6. Press **comma** once to move past that container.
7. Check speech and braille.
The intended destination is “After unordered list”, the button immediately following the outer list.
8. As an additional case, repeat steps 4–5, press L again to enter the nested list, then Shift+L to return to the outer list before pressing comma.
9. Repeat from the other level-two headings: “Ordered list”, “Description list” and “Wrapped description list”.
The corresponding destination buttons are named “After ordered list”, “After description list” and “After wrapped list”.
10. Repeat with the Chromium UIA option set to **No**, using a newly opened browser instance, for the IAccessible2 comparison.
Restore the original option afterwards.

Each list was tested both directly and after returning from its nested list: eight routes per accessibility API.
No production NVDA method or provider text range was replaced by the test harness.

## Actual behavior

With official NVDA 2027.1.0dev at c22a509337c0b94ac5459ab2a749eeeb9cb06116 and UIA enabled, all eight routes read the last nested item instead of the following button.

Verbatim speech for the first example, captured by the NVDA system-test spy:

> list  with 1 item  white bullet  Last nested unordered item

For the description-list example:

> list  with 1 item  bullet  Last nested description item

With UIA disabled (IAccessible2), all eight routes reach their expected buttons.
For the first example, the recorded speech is:

> After unordered list  button

The corresponding braille text is:

> btn After unordered list

**Separate braille observation:** in the official UIA run, the first example retained `h2 Unordered list` on the braille display.
The debug log records a distinct `TypeError: can only concatenate str (not "int") to str` in `getPropertiesBraille` while adding `childControlCount`.
That stale braille text is not evidence that the caret stayed on the heading; speech independently demonstrates the container-end failure.
The proposed navigation fix does not fix that separate list-count/braille exception.

### Technical findings

Chrome's real UIA provider returned these ranges in a separate diagnostic probe:

* Ordinary outer list text: `• Alpha\n◦ Last nested item`.
* Native description-list text: `Alpha\nDefinition\n• Last nested item`.
* Collapsing either range to its end and expanding to Line returned the last nested item's line.
* Expanding to Character at the same endpoint returned `\n`.
* Advancing one character for diagnosis and expanding to Line returned the following button's text.

The existing NVDA command collapses the container's element range at its end, sets the selection, and expands to Line for reporting.
An element endpoint before an omitted terminal newline therefore resolves back onto the last contained line.
The evidence does not indicate a wrong-ancestor choice, nor an accessible-name loss.

The relevant shared navigation code is unchanged from the original feature base.
Regression tests modelling the provider boundary fail with the exact official module and pass with the independent candidate.
The complete official/candidate browser comparison now confirms that the bug is independent of the description-list feature.

## Expected behavior

Comma should move past the enclosing container and report the first following readable content, preserving its first character and control.
For the first attached example, it should reach the “After unordered list” button rather than “Last nested unordered item”.
It should continue to honour the nearest enclosing container and retain the existing behaviour at the bottom of the document.

### Proposed fix

Normalize the range in `ChromiumUIATreeInterceptor.getEnclosingContainerRange` after delegating container selection to the base implementation.
Extend its end only across a verified newline character unit starting exactly at that endpoint, and only if line expansion at the endpoint still resolves onto preceding content.
Do not consume an independent following blank line, move forward unconditionally, or change shared UIA navigation, ancestor selection, accessible names, or public APIs.

The candidate includes 16 focused unit tests and Chrome/UIA and IA2 system tests.
The full candidate unit suite ran 1,481 tests with five skips and no failures/errors.
Ruff, Pyright, ty, translation checks and changelog lint passed.

Measured real-browser comparison using the same standalone page and external harness:

| Build | IA2 routes | UIA routes |
| --- | --- | --- |
| Unchanged official c22a509 | 8/8 pass | 0/8 pass: final nested item read again |
| Independent candidate ae1594b | 8/8 pass | 8/8 pass: following button in speech and braille |

All six repository `chrome_list` tests also pass with the candidate.
The fix remains limited to Chromium UIA container-end normalization; it does not incorporate the separate feature or braille changes.

## NVDA logs, crash dumps and other attachments

The reproduction ZIP contains:

* A standalone HTML page with UL/OL/DL/wrapped-DL examples; no script or network dependency.
* Reviewed excerpts of fresh official-source NVDA debug logs for this exact page, with version, backend, gestures, speech, braille and the separate braille exception.
* Equivalent log excerpts for the independent candidate.
* JSON observations of all 32 measured routes, exact speech/braille strings and raw-log hashes.
* Technical notes covering provider observations, official build provenance, proposed fix, validation results and limitations.
* A clearly labelled historical excerpt from the original feature-worktree failure, kept separate from the fresh official evidence.

The log attachments are explicitly labelled excerpts, not complete logs: unrelated personal windows, configuration and session content are omitted.
Retained NVDA records are verbatim and verified against the local originals; the full logs remain available locally for further review if requested.
No crash dump was produced by the definitive reproduction or candidate runs.

Related reports reviewed include [#15732](https://github.com/nvaccess/nvda/issues/15732), [#12808](https://github.com/nvaccess/nvda/issues/12808), and [#7382](https://github.com/nvaccess/nvda/issues/7382).
They concern a navigation redesign, end-of-document movement, and nested/layout tables respectively, rather than this demonstrated terminal-newline boundary.
No exact duplicate was identified in the targeted searches; the search was not exhaustive.

## NVDA type

Select: **source copy**.

## NVDA version

2027.1.0dev AMD64, unchanged official master c22a509337c0b94ac5459ab2a749eeeb9cb06116, separately built from its pinned dependencies.

## Have you tried any other versions of NVDA? If so, please report their behaviors.

* Independent candidate `fix/chromium-uia-container-end`, ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8, based directly on that official revision: all eight standalone-page routes pass with each API; all six repository Chrome list tests pass.
* Earlier feature-development copy, source-description-lists-3858-c43cf6c AMD64: the same navigation symptom was first observed there; it is not the sole evidence for this report.
* Installed NVDA 2026.2: version checked only, not tested for this issue.

## Windows version

Windows 11 Pro 25H2, build 26200.9550, 64-bit.

## Name and version of other software in use when reproducing the issue

* Google Chrome 154.0.8037.97.
* Keyboard comparison: NVDA's source system-test harness with the speech/braille spy, using actual Chrome and NVDA, not WebDriver.
* Official comparison environment: Python 3.13.15 AMD64, wxPython 4.3.1, comtypes 1.4.16, Robot Framework 7.4.2 and SCons 4.11.0.
* Edge and Firefox have not been validated for this container-end candidate.

## Other information about your system

The keyboard tests use a temporary NVDA configuration in English and an isolated Chrome profile, not the user's normal browser profile.
The NVDA test sandbox contains no installed user add-ons, but it deliberately loads the repository's test spy and speech-capture synthesizer through scratchpad.
This is instrumentation, not an entirely uninstrumented runtime.
No claim is made about a physical braille display; the quoted output is NVDA's recorded braille text.

The installed screen reader was restored and its running state verified after the browser tests.
No reboot or System Accessibility Repair Tool run was performed for this investigation.

## Does the issue still occur after restarting your computer?

Select: **I have not restarted my computer**.

## If NVDA add-ons are disabled, is your problem still occurring?

Select: **I have not restarted NVDA with add-ons disabled**.

The separate test sandbox had no installed user add-ons, but that is not the same as performing and verifying the requested restart-with-add-ons-disabled troubleshooting step.

## Does the issue still occur after you run the System Accessibility Repair Tool (COM Registration Fixing Tool in older versions) in NVDA's tools menu?

Select: **I have not run the System Accessibility Repair Tool**.
