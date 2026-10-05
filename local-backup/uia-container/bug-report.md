# Bug-report form draft

**NOT READY TO SUBMIT: clean-build keyboard reproduction and a fresh NVDA log are still pending because the Windows session was locked.**
This document deliberately reports only existing evidence.
Read [the Spanish submission checklist](README.es.md) before using it.
Copy each section's content into its matching field in the **Bug report form**, not into a blank issue.

## Suggested title

Chrome with UI Automation: comma can remain on the final nested list item instead of moving past the container

## Brief summary

In browse mode with Chromium accessed through UI Automation, moving past the end of a list can leave NVDA reading the list's final nested item instead of the content immediately after the outer list.
This was found while running description-list tests, but a separate probe of Chrome's real UIA provider shows the same endpoint behaviour with ordinary unordered lists.

An independent candidate fix is prepared on official master, rather than on the description-list feature branch.
I plan to submit a pull request with the fix and regression tests once the reproduction has been confirmed and the issue has been discussed/triaged.
The pending work is explicitly listed below; I am not claiming a completed clean-build browser comparison.

## Steps to reproduce

Prepared minimal steps, **awaiting keyboard confirmation with the pristine official build**:

1. Extract the attached reproduction ZIP and open [container-navigation.html](container-navigation.html) in Google Chrome.
2. In NVDA Settings, open Advanced, acknowledge the warning about changing advanced settings, and set **Use UI Automation to access Microsoft Edge and other Chromium based browsers** to **Yes**.
Apply the change, close/reopen the test browser, and reopen the page.
3. Ensure NVDA is in browse mode, not focus mode; use NVDA+Space if necessary.
4. Press Control+Home, then **2** to reach the “Unordered list” level-two heading.
5. Press **L** once to enter the outer list at “Alpha unordered”.
6. Press **comma** once to move past that container.
7. Check speech and braille, then use right-arrow reading to verify the resulting position.
The intended destination is “After unordered list”, the button immediately following the outer list.
8. As an additional case, repeat steps 4–5, press L again to enter the nested list, then Shift+L to return to the outer list before pressing comma.
9. Repeat from the other level-two headings: “Ordered list”, “Description list” and “Wrapped description list”.
The corresponding destination buttons are named “After ordered list”, “After description list” and “After wrapped list”.
10. Repeat with the Chromium UIA option set to **No**, using a newly opened browser instance, for the IAccessible2 comparison.
Restore the original option afterwards.

The actual earlier failure used a larger description-list fixture, returned from its nested list to the outer list with Shift+L, and then pressed comma.
Its final definition contained an ordinary unordered list item named “Ordinary item”, followed outside the description list by a “Toggle definition” button.
The attached log excerpt is from that earlier case, not from this newly prepared minimal page.

## Actual behavior

In the earlier Chrome/UIA keyboard tests, both the direct-child and div-wrapped description-list cases spoke the last nested list item instead of reaching “Toggle definition”.

Verbatim speech captured by the NVDA system-test spy:

> list  with 1 item  bullet  Ordinary item  definition

Verbatim braille region text from the NVDA log:

> definition lst1 • Ordinary item lst end dlst end

The corresponding IAccessible2 cases passed.
Accessible-name tests passed with both APIs; these failures were at the separate comma-navigation assertion.

For the new standalone page, the suspected symptom is the analogous last nested item being read again instead of the following button.
**That page's pristine-build keyboard output has not yet been captured.**
Its browser preview and document structure have been checked, but that is not an NVDA end-to-end test.

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
This supports a pre-existing bug, but the clean official NVDA/Chrome keyboard confirmation remains pending.

## Expected behavior

Comma should move past the enclosing container and report the first following readable content, preserving its first character and control.
For the first attached example, it should reach the “After unordered list” button rather than “Last nested unordered item”.
It should continue to honour the nearest enclosing container and retain the existing behaviour at the bottom of the document.

### Proposed fix

Normalize the range in `ChromiumUIATreeInterceptor.getEnclosingContainerRange` after delegating container selection to the base implementation.
Extend its end only across a verified newline character unit starting exactly at that endpoint, and only if line expansion at the endpoint still resolves onto preceding content.
Do not consume an independent following blank line, move forward unconditionally, or change shared UIA navigation, ancestor selection, accessible names, or public APIs.

The candidate includes 16 focused unit tests and prepared Chrome/UIA and IA2 system tests.
The full candidate unit suite ran 1,481 tests with five skips and no failures/errors.
Ruff, Pyright, ty, translation checks and changelog lint passed.
Real-browser execution of the candidate is still required before submitting its PR.

## NVDA logs, crash dumps and other attachments

The prepared reproduction ZIP contains:

* [container-navigation.html](container-navigation.html): standalone UL/OL/DL/wrapped-DL examples; no script or network dependency.
* [technical-notes.md](technical-notes.md): provider observations, official build provenance, proposed fix, validation results and limitations.
* [earlier-feature-run-excerpt.log](earlier-feature-run-excerpt.log): clearly labelled relevant speech/braille/keyboard excerpts from the original feature-worktree failure, with unrelated session content omitted.

A fresh NVDA debug log from the pristine official build and the actual attached page **has not yet been collected**.
It must be added before considering this draft complete.
No crash dump is associated with the observed assertion failure; do not upload an unrelated old dump.

Related reports reviewed include [#15732](https://github.com/nvaccess/nvda/issues/15732), [#12808](https://github.com/nvaccess/nvda/issues/12808), and [#7382](https://github.com/nvaccess/nvda/issues/7382).
They concern a navigation redesign, end-of-document movement, and nested/layout tables respectively, rather than this demonstrated terminal-newline boundary.
No exact duplicate was identified in the targeted searches; the search was not exhaustive.

## NVDA type

Select: **source copy**.

## NVDA version

Observed earlier: source-description-lists-3858-c43cf6c AMD64, in the feature worktree later committed as 7cf80258277b596a85bb23af383ece1eba2be5df.

## Have you tried any other versions of NVDA? If so, please report their behaviors.

* Official master c22a509337c0b94ac5459ab2a749eeeb9cb06116, source version 2027.1.0dev: separately built from the pinned dependencies, without the feature changes.
The unit control demonstrates the modelled boundary failure, but this build has **not** yet been tested by keyboard in Chrome because the Windows session was locked.
* Independent candidate `fix/chromium-uia-container-end`: all 16 focused unit tests and the full unit suite pass; real-browser tests are pending.
* Installed NVDA 2026.2: version checked only, not tested for this issue.

## Windows version

Windows 11 Pro 25H2, build 26200.9550, 64-bit.

## Name and version of other software in use when reproducing the issue

* Google Chrome 154.0.8037.97.
* Original keyboard failure: NVDA's source system-test harness with the speech/braille spy, using actual Chrome and NVDA, not WebDriver.
* Official comparison environment prepared: Python 3.13.15 AMD64, wxPython 4.3.1, comtypes 1.4.16, Robot Framework 7.4.2 and SCons 4.11.0.
* Edge and Firefox have not been validated for this container-end candidate.

## Other information about your system

The keyboard tests use a temporary NVDA configuration in English and an isolated Chrome profile, not the user's normal browser profile.
The NVDA test sandbox contains no installed user add-ons, but it deliberately loads the repository's test spy and speech-capture synthesizer through scratchpad.
This is instrumentation, not an entirely uninstrumented runtime.
No claim is made about a physical braille display; the quoted output is NVDA's recorded braille text.

The installed screen reader was restored after the original tests and has not been replaced during the locked-session preparation.
No reboot or System Accessibility Repair Tool run was performed for this investigation.

## Does the issue still occur after restarting your computer?

Select: **I have not restarted my computer**.

## If NVDA add-ons are disabled, is your problem still occurring?

Select: **I have not restarted NVDA with add-ons disabled**.

The separate test sandbox had no installed user add-ons, but that is not the same as performing and verifying the requested restart-with-add-ons-disabled troubleshooting step.

## Does the issue still occur after you run the System Accessibility Repair Tool (COM Registration Fixing Tool in older versions) in NVDA's tools menu?

Select: **I have not run the System Accessibility Repair Tool**.
