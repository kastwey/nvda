"""External reproduction against an otherwise unmodified NVDA checkout."""

import json
from pathlib import Path
import re
from unittest.mock import patch

from robot.libraries.BuiltIn import BuiltIn
from ChromeLib import ChromeLib
import NvdaLib
from SystemTestSpy import _getLib
import WindowsLib


def test_container_navigation(useUIA: bool) -> None:
	"""Capture the same comma-navigation cases through both browser backends."""
	builtIn = BuiltIn()
	spy = NvdaLib.getSpyLib()
	spy.set_configValue(["UIA", "allowInChromium"], 2 if useUIA else 3)
	spy.setBrailleCellCount(200)
	chrome: ChromeLib = _getLib("ChromeLib")
	fixture = Path(__file__).with_name("container-navigation.html")
	titlePattern = re.compile(r"^NVDA container navigation reproduction")
	# Adapt only the external browser-launch helper's title matcher. The fixture is
	# opened directly, and no NVDA production methods or text ranges are replaced.
	with patch.object(ChromeLib, "getUniqueTestCaseTitleRegex", return_value=titlePattern):
		window = chrome.start_chrome(str(fixture), "container navigation")
	if not WindowsLib.isWindowInForeground(window):
		WindowsLib.taskSwitchToItemMatching(titlePattern)
	NvdaLib.getSpeechAfterKey("alt+d")
	NvdaLib.getSpeechAfterKey("control+f6")
	startSpeech = NvdaLib.getSpeechAfterKey("control+home")
	builtIn.should_contain(startSpeech, "NVDA container navigation reproduction")
	results: list[dict[str, str]] = []
	for case in ("unordered", "ordered", "description", "wrapped"):
		NvdaLib.getSpeechAfterKey("2")
		entrySpeech = NvdaLib.getSpeechAfterKey("l")
		builtIn.should_contain(entrySpeech, f"Alpha {case}")
		directSpeech, directBraille = NvdaLib.getSpeechAndBrailleAfterKey(",")
		results.append(
			{
				"case": f"{case} direct",
				"entrySpeech": entrySpeech,
				"commaSpeech": directSpeech,
				"commaBraille": directBraille,
				"expected": f"After {case} list",
			},
		)
		# Also exercise returning from the inner list to its enclosing list.
		NvdaLib.getSpeechAfterKey("shift+2")
		NvdaLib.getSpeechAfterKey("l")
		innerSpeech = NvdaLib.getSpeechAfterKey("l")
		builtIn.should_contain(innerSpeech, f"Last nested {case} item")
		returnSpeech = NvdaLib.getSpeechAfterKey("shift+l")
		builtIn.should_contain(returnSpeech, f"Alpha {case}")
		speech, braille = NvdaLib.getSpeechAndBrailleAfterKey(",")
		results.append(
			{
				"case": f"{case} nested round trip",
				"entrySpeech": entrySpeech,
				"returnSpeech": returnSpeech,
				"commaSpeech": speech,
				"commaBraille": braille,
				"expected": f"After {case} list",
			},
		)
		# Restart from the current example's heading. This is independent of
		# whether comma reached the button or remained in the final nested list.
		NvdaLib.getSpeechAfterKey("shift+2")
	backend = "uia" if useUIA else "ia2"
	outputDir = Path(builtIn.get_variable_value("${OUTPUT DIR}"))
	outputDir.joinpath(f"{backend}-observations.json").write_text(
		json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
	)
	failures = [
		f"{result['case']}: speech={result['commaSpeech']!r}; braille={result['commaBraille']!r}"
		for result in results
		if result["expected"] not in result["commaSpeech"] or result["expected"] not in result["commaBraille"]
	]
	if failures:
		raise AssertionError("Comma did not move past the outer container:\n" + "\n".join(failures))