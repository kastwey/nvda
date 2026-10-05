"""Export narrowly reviewed evidence, never the full personal NVDA session logs."""

import hashlib
import json
import re
from pathlib import Path


def digest(path: Path) -> str:
	return hashlib.sha256(path.read_bytes()).hexdigest()


def selectRecords(text: str, backend: str) -> tuple[list[str], int]:
	"""Keep version, relevant keys, fixture output, backend and one braille error."""
	records = re.split(
		r"(?=^(?:DEBUG|DEBUGWARNING|IO|INFO|WARNING|ERROR|CRITICAL) - )", text, flags=re.MULTILINE
	)
	selected: list[str] = []
	errorCount = 0
	fixtureMarkers = (
		"Alpha unordered",
		"Alpha ordered",
		"Alpha description",
		"Alpha wrapped",
		"Last nested unordered item",
		"Last nested ordered item",
		"Last nested description item",
		"Last nested wrapped item",
		"After unordered list",
		"After ordered list",
		"After description list",
		"After wrapped list",
		"h2 Unordered list",
		"h2 Ordered list",
		"h2 Description list",
		"h2 Wrapped description list",
		"'Unordered list', 'heading'",
		"'Ordered list', 'heading'",
		"'Description list', 'heading'",
		"'Wrapped description list', 'heading'",
	)
	backendClass = "ChromiumUIATreeInterceptor" if backend == "uia" else "ChromeVBuf"
	for record in records:
		header, _, body = record.partition("\n")
		keep = False
		if (
			(header.startswith("INFO - __main__") and body.startswith("Starting NVDA version"))
			or (
				header.startswith("INFO - core.main")
				and body.startswith(("Windows version:", "Using Python version", "Using comtypes version"))
			)
			or (header.startswith("DEBUG - treeInterceptorHandler.update") and backendClass in body)
		):
			keep = True
		elif header.startswith("IO - inputCore.InputManager.executeGesture"):
			keep = body.strip() in {
				f"Input: kb(desktop):{key}" for key in ("control+home", "2", "l", "shift+l", "shift+2", ",")
			}
		elif header.startswith(
			(
				"IO - speech.speech.speak",
				"IO - braille.buffers.BrailleBuffer.update",
				"DEBUG - external:synthDrivers.speechSpySynthDriver.SpeechSpySynthDriver.speak ",
			)
		):
			keep = any(marker in body for marker in fixtureMarkers)
		elif header.startswith("DEBUGWARNING - braille.brailleHandler") and (
			'TypeError: can only concatenate str (not "int") to str' in body
		):
			errorCount += 1
			keep = errorCount == 1
		if keep:
			if re.search(r"C:\\Users\\|https?://|[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", record):
				raise ValueError("Selected record requires additional privacy review")
			selected.append(record.rstrip())
	return selected, errorCount


def main() -> None:
	root = Path(__file__).resolve().parent
	runs = {
		"official": ("baseline-system-05", "c22a509337c0b94ac5459ab2a749eeeb9cb06116"),
		"candidate": ("candidate-system-03", "ae1594bced4d2ce60dcaa7d1fd975d9f019bb2b8"),
	}
	evidence = {"date": "2026-10-05", "fixtureSha256": digest(root / "container-navigation.html"), "runs": {}}
	for label, (directory, commit) in runs.items():
		logParts = [
			"REVIEWED EXCERPTS OF FRESH NVDA DEBUG LOGS -- NOT THE COMPLETE SESSION LOGS",
			f"Date: 2026-10-05; source commit: {commit}; run: {directory}",
			"The production source was not patched by the external test harness.",
			"Only startup versions, backend, fixture navigation/output and one repeated braille error are retained.",
			"Unrelated window titles, configuration and session records are omitted; retained records are verbatim.",
			"Raw speech records precede symbol processing; synth Sequence records and JSON contain spoken symbols.",
		]
		runEvidence = {"commit": commit, "directory": directory, "backends": {}}
		for backend in ("ia2", "uia"):
			observationsPath = root / directory / f"{backend}-observations.json"
			observations = json.loads(observationsPath.read_text(encoding="utf-8"))
			assert len(observations) == 8
			passed = sum(
				result["expected"] in result["commaSpeech"] and result["expected"] in result["commaBraille"]
				for result in observations
			)
			assert passed == (0 if label == "official" and backend == "uia" else 8)
			logPath = (
				root
				/ directory
				/ "nvdaTestRunLogs"
				/ (f"containerNavigationTests-Move_past_lists_with_{backend.upper()}-nvda.log")
			)
			raw = logPath.read_text(encoding="utf-8-sig")
			records, errorCount = selectRecords(raw, backend)
			assert records and all(record in raw for record in records)
			assert sum("Input: kb(desktop):," in record for record in records) == 8
			runEvidence["backends"][backend] = {
				"routes": 8,
				"passed": passed,
				"failed": 8 - passed,
				"rawLogSha256": digest(logPath),
				"repeatedBrailleTypeErrors": errorCount,
				"observations": observations,
			}
			logParts.extend(
				[
					f"\n===== {backend.upper()} =====",
					f"Raw log SHA256: {digest(logPath)}",
					f"Related repeated braille TypeErrors: {errorCount} (first retained; not fixed by this candidate)",
					"\n\n".join(records),
				]
			)
		evidence["runs"][label] = runEvidence
		output = root / f"{label}-reproduction.log"
		output.write_text("\n\n".join(logParts) + "\n", encoding="utf-8")
		print("VERIFIED_LOG_EXCERPT", output.name, digest(output))
	(root / "browser-observations.json").write_text(
		json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
	)
	print("BROWSER_ROUTES_VERIFIED", "official IA2=8/8 UIA=0/8; candidate IA2=8/8 UIA=8/8")


if __name__ == "__main__":
	main()
