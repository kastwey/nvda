# NVDA Chromium UIA container-navigation reproduction package

**Status: prepared reproduction; the pristine NVDA/Chrome keyboard comparison is not yet complete.**
The Windows session was locked during preparation, so the new real-browser tests were not launched.
No issue or pull request has been created.

## Contents

* [container-navigation.html](container-navigation.html): standalone page with UL, OL, DL and wrapped-DL examples.
* [technical-notes.md](technical-notes.md): observations, candidate design, version/build provenance and completed/pending tests.
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

## Required before publishing the report

Capture the actual page's speech and braille output and a fresh NVDA log with the separately built official NVDA, then with the candidate.
Keep those results distinct from the modelled unit tests and earlier feature-worktree evidence.
Review logs for unnecessary private information before attachment.
