"""External reproduction against an otherwise unmodified NVDA checkout."""

import json
import re
from pathlib import Path
from unittest.mock import patch

import NvdaLib
import WindowsLib
from ChromeLib import ChromeLib
from chromeWindow import focusChromeWindow
from robot.libraries.BuiltIn import BuiltIn
from SystemTestSpy import _getLib


def test_container_navigation(useUIA: bool) -> None:
	"""Capture the same comma-navigation cases through both browser backends."""
	builtIn = BuiltIn()
	spy = NvdaLib.getSpyLib()
	spy.set_configValue(["UIA", "allowInChromium"], 2 if useUIA else 3)
	spy.setBrailleCellCount(200)
	chrome: ChromeLib = _getLib("ChromeLib")
	fixture = Path(__file__).with_name("container-navigation.html")
	titlePattern = re.compile(r"^NVDA container navigation reproduction(?: - .+)? - Google Chrome$")
	# Adapt only the external browser-launch helper's title matcher. The fixture is
	# opened directly, and no NVDA production methods or text ranges are replaced.
	with patch.object(ChromeLib, "getUniqueTestCaseTitleRegex", return_value=titlePattern):
		window = chrome.start_chrome(str(fixture), "container navigation")

	def ensureForeground() -> None:
		"""Never send a test key to an unrelated application."""
		if not WindowsLib.isWindowInForeground(window):
			focusChromeWindow(window.hwndVal)
		builtIn.should_be_true(WindowsLib.isWindowInForeground(window), "Test Chrome lost foreground")

	def getSpeech(key: str) -> str:
		ensureForeground()
		return NvdaLib.getSpeechAfterKey(key)

	def getSpeechAndBraille(key: str) -> tuple[str, str]:
		ensureForeground()
		return NvdaLib.getSpeechAndBrailleAfterKey(key)

	addressSpeech = getSpeech("alt+d")
	builtIn.should_contain(addressSpeech, "Address and search bar")
	getSpeech("control+f6")
	startSpeech = getSpeech("control+home")
	builtIn.should_contain(startSpeech, "NVDA container navigation reproduction")
	results: list[dict[str, str]] = []
	backend = "uia" if useUIA else "ia2"
	outputDir = Path(builtIn.get_variable_value("${OUTPUT DIR}"))

	def record(result: dict[str, str]) -> None:
		"""Preserve completed measurements even if a later step is interrupted."""
		results.append(result)
		outputDir.joinpath(f"{backend}-observations.json").write_text(
			json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
		)

	for case in ("unordered", "ordered", "description", "wrapped"):
		getSpeech("2")
		entrySpeech = getSpeech("l")
		builtIn.should_contain(entrySpeech, f"Alpha {case}")
		directSpeech, directBraille = getSpeechAndBraille(",")
		record(
			{
				"case": f"{case} direct",
				"entrySpeech": entrySpeech,
				"commaSpeech": directSpeech,
				"commaBraille": directBraille,
				"expected": f"After {case} list",
			},
		)
		# Also exercise returning from the inner list to its enclosing list.
		getSpeech("shift+2")
		getSpeech("l")
		innerSpeech = getSpeech("l")
		builtIn.should_contain(innerSpeech, f"Last nested {case} item")
		returnSpeech = getSpeech("shift+l")
		builtIn.should_contain(returnSpeech, f"Alpha {case}")
		speech, braille = getSpeechAndBraille(",")
		record(
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
		getSpeech("shift+2")
	failures = [
		f"{result['case']}: speech={result['commaSpeech']!r}; braille={result['commaBraille']!r}"
		for result in results
		if result["expected"] not in result["commaSpeech"] or result["expected"] not in result["commaBraille"]
	]
	if failures:
		raise AssertionError("Comma did not move past the outer container:\n" + "\n".join(failures))
