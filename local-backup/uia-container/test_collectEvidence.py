"""Verify the log export is verbatim, narrowly scoped and fails closed on private data."""

import unittest

from collectEvidence import selectRecords


class TestEvidenceSelection(unittest.TestCase):
	def test_retainsVersionAndCommandVerbatim(self) -> None:
		version = "INFO - __main__ (12:00:00.000) - MainThread (1):\nStarting NVDA version 2027.1.0dev AMD64"
		command = "IO - inputCore.InputManager.executeGesture (12:00:01.000):\nInput: kb(desktop):,"
		records, errors = selectRecords(version + "\n\n" + command + "\n", "uia")
		self.assertEqual([version, command], records)
		self.assertEqual(0, errors)

	def test_omitsUnrelatedSpeechAndConfiguration(self) -> None:
		text = (
			"IO - speech.speech.speak (12:00:00.000):\nSpeaking ['Private unrelated window']\n"
			"INFO - config.ConfigManager (12:00:00.000):\n{'password': 'example-not-a-real-secret'}\n"
		)
		self.assertEqual(([], 0), selectRecords(text, "uia"))

	def test_keepsFixtureSpeech(self) -> None:
		record = "IO - speech.speech.speak (12:00:00.000):\nSpeaking ['After unordered list', 'button']"
		self.assertEqual(([record], 0), selectRecords(record, "uia"))

	def test_excludesUnrelatedInput(self) -> None:
		record = "IO - inputCore.InputManager.executeGesture (12:00:00.000):\nInput: kb(desktop):alt+tab"
		self.assertEqual(([], 0), selectRecords(record, "uia"))

	def test_rejectsPrivateDataEvenWithFixtureMarker(self) -> None:
		for value in (r"C:\Users\Example\notes", "person@example.invalid", "https://example.invalid/private"):
			with self.subTest(value=value), self.assertRaises(ValueError):
				selectRecords(
					f"IO - speech.speech.speak (12:00:00.000):\nSpeaking ['After unordered list', '{value}']",
					"uia",
				)

	def test_retainsOnlyFirstBrailleErrorButCountsAll(self) -> None:
		record = (
			"DEBUGWARNING - braille.brailleHandler.BrailleHandler._handlePendingUpdate (12:00:00.000):\n"
			'TypeError: can only concatenate str (not "int") to str'
		)
		self.assertEqual(([record], 2), selectRecords(record + "\n" + record, "uia"))


if __name__ == "__main__":
	unittest.main()
