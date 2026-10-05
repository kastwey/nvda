# NVDA Chromium UIA container-navigation reproduction package

**Status: verified real NVDA/Chrome comparison on 2026-10-05.**
Official source c22a509 reproduces the UIA failure in all eight routes; candidate ae1594b passes those routes.
IAccessible2 passes all eight routes with both builds.
No issue or pull request has been created.

## Contents

* [container-navigation.html](container-navigation.html): standalone page with UL, OL, DL and wrapped-DL examples.
* [technical-notes.md](technical-notes.md): observations, candidate design, version/build provenance and coverage limitations.
* [official-reproduction.log](official-reproduction.log): reviewed excerpts of fresh official NVDA debug logs for this exact page, including the failed comma output.
* [candidate-reproduction.log](candidate-reproduction.log): equivalent candidate log excerpts with correct destination output.
* [browser-observations.json](browser-observations.json): all 32 measured routes, literal speech/braille and raw-log hashes.
* [earlier-feature-run-excerpt.log](earlier-feature-run-excerpt.log): a labelled excerpt from the original failure in a different, feature-development worktree.
It is not a pristine-build log for this page.

## Minimal steps

1. Extract the archive and open the HTML page in Chrome.
2. Force Chromium UI Automation to **Yes** in NVDA's Advanced settings and reopen the test browser.
3. In browse mode, press Control+Home, **2**, **L**, then **comma**.
4. The intended destination is the “After unordered list” button, not “Last nested unordered item”.
5. Repeat with the Chromium UIA setting **No** for the IA2 comparison and restore the original setting afterwards.

The page has no script or external resources and works offline.
The button only marks the expected navigation destination; activating it has no action.

## Evidence limits

The logs are excerpts, not full personal session logs: retained records are verbatim; unrelated windows/configuration are omitted.
The tests use the repository's temporary scratchpad speech/braille instrumentation, not a physical braille display.
A separate official UIA list-count/braille exception remains outside the candidate; it explains stale heading text in the official braille snapshots.
Candidate button destinations are verified in both speech and braille.
Reboot, an add-ons-disabled restart and the System Accessibility Repair Tool were not performed.
Edge, Firefox and installed NVDA 2026.2 have not been validated for this issue.
