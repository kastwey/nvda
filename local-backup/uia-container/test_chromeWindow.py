"""Safety regressions for the external, non-production window activation helper."""

import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, patch

import chromeWindow


class TestChromeWindow(unittest.TestCase):
	def setUp(self) -> None:
		self.user32 = Mock()
		self.kernel32 = Mock()
		self.kernel32.GetCurrentThreadId.return_value = 10
		self.user32.GetWindowThreadProcessId.side_effect = (20, 30)
		self.user32.GetForegroundWindow.side_effect = (456, 123)
		self.user32.AttachThreadInput.return_value = True
		self.bindings = SimpleNamespace(user32=self.user32, kernel32=self.kernel32)
		self.addCleanup(patch.stopall)
		patch.dict(sys.modules, {"winBindings": self.bindings}).start()
		self.isUnlocked = patch.object(chromeWindow, "isSessionUnlocked", return_value=True).start()
		process = patch.object(chromeWindow.psutil, "Process").start()
		process.return_value.name.return_value = "chrome.exe"
		self.process = process

	def test_lockedDesktopDoesNotActivateAnything(self) -> None:
		self.isUnlocked.return_value = False
		with self.assertRaisesRegex(RuntimeError, "locked"):
			chromeWindow.focusChromeWindow(123)
		self.assertEqual([], self.user32.mock_calls)
		self.process.assert_not_called()

	def test_rejectsUnrelatedApplication(self) -> None:
		self.process.return_value.name.return_value = "Code.exe"
		with self.assertRaisesRegex(RuntimeError, "no longer belongs to Chrome"):
			chromeWindow.focusChromeWindow(123)
		self.user32.AttachThreadInput.assert_not_called()
		self.user32.SetForegroundWindow.assert_not_called()

	def test_alreadyForegroundDoesNotAttach(self) -> None:
		self.user32.GetForegroundWindow.side_effect = (123,)
		self.assertTrue(chromeWindow.focusChromeWindow(123))
		self.user32.AttachThreadInput.assert_not_called()

	def test_attachesAndDetachesBothQueues(self) -> None:
		self.assertTrue(chromeWindow.focusChromeWindow(123))
		self.assertEqual(
			[call(10, 20, True), call(10, 30, True), call(10, 30, False), call(10, 20, False)],
			self.user32.AttachThreadInput.call_args_list,
		)
		self.user32.SetForegroundWindow.assert_called_once_with(123)

	def test_detachesOnError(self) -> None:
		self.user32.SetForegroundWindow.side_effect = OSError("Test error")
		with self.assertRaises(OSError):
			chromeWindow.focusChromeWindow(123)
		self.assertEqual(call(10, 20, False), self.user32.AttachThreadInput.call_args_list[-1])

	def test_verifiesActualForeground(self) -> None:
		self.user32.GetForegroundWindow.side_effect = (456, 456)
		self.assertFalse(chromeWindow.focusChromeWindow(123))

	def test_doesNotDetachFailedAttachments(self) -> None:
		self.user32.AttachThreadInput.return_value = False
		self.assertTrue(chromeWindow.focusChromeWindow(123))
		self.assertEqual(
			[call(10, 20, True), call(10, 30, True)],
			self.user32.AttachThreadInput.call_args_list,
		)


if __name__ == "__main__":
	unittest.main()
