# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.

"""Opt-in real Firefox and MSHTML tests using isolated, locally generated documents."""

import os
import re
import subprocess
import tempfile
import winreg
from pathlib import Path

import NvdaLib
from robot.libraries.BuiltIn import BuiltIn
from SystemTestSpy import _blockUntilConditionMet
from SystemTestSpy.windows import (
	CloseWindow,
	GetForegroundHwnd,
	GetWindowWithTitle,
	SetForegroundWindow,
	Window,
	sendKeyboardEvent,
)


class descriptionListTests:
	"""Keep the test host separate from the user's browser windows and profile."""

	ROBOT_LIBRARY_SCOPE = "SUITE"

	def __init__(self) -> None:
		self._temporaryDirectory: tempfile.TemporaryDirectory | None = None
		self._process: subprocess.Popen | None = None
		self._window: Window | None = None

	def _firefoxPath(self) -> str:
		configured = BuiltIn().get_variable_value("${firefoxPath}", None)
		if configured:
			return str(Path(configured).resolve(strict=True))
		for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
			try:
				with winreg.OpenKey(
					root, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe"
				) as key:
					path, _ = winreg.QueryValueEx(key, "")
				if Path(path).is_file():
					return path
			except OSError:
				continue
		BuiltIn().fail("Firefox not found; supply --variable firefoxPath:absolute-path-to-firefox.exe")

	def _prepare(self, host: str, wrapped: bool) -> None:
		self._temporaryDirectory = tempfile.TemporaryDirectory(prefix="nvda-description-lists-")
		root = Path(self._temporaryDirectory.name)
		title = root.name
		group = """
			<dt>Alpha</dt><dt>Alias</dt>
			<dd><p>First paragraph</p><p>Second paragraph</p></dd>
			<dd id="additionalDefinition">Another definition
				<dl><dt>Nested</dt><dd>One</dd><dd>Two</dd><dd>Three</dd></dl>
			</dd>
		"""
		otherGroup = "<dt>Solo</dt><dd>Only definition<ul><li>Ordinary item</li></ul></dd>"
		if wrapped:
			group = f"<div>{group}</div>"
			otherGroup = f"<div>{otherGroup}</div>"
		path = root / ("test.hta" if host == "mshtml" else "test.html")
		path.write_text(
			f"""<!doctype html>
			<html lang="en"><head><meta http-equiv="X-UA-Compatible" content="IE=edge">
			<title>{title}</title></head><body>
			<h1>Definition counts</h1>
			<dl>{group}{otherGroup}</dl>
			<button onclick="
				if (!this.definition) {{
					this.definition = document.getElementById('additionalDefinition');
					this.definitionParent = this.definition.parentNode;
					this.nextElement = this.definition.nextSibling;
				}}
				if (this.definition.parentNode) {{ this.definitionParent.removeChild(this.definition); }}
				else {{ this.definitionParent.insertBefore(this.definition, this.nextElement); }}
			">Toggle definition</button>
			<p>After list</p></body></html>""",
			encoding="utf-8",
		)
		if host == "firefox":
			profile = root / "profile"
			profile.mkdir()
			(profile / "user.js").write_text(
				'user_pref("browser.shell.checkDefaultBrowser", false);\n'
				'user_pref("browser.aboutwelcome.enabled", false);\n'
				'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
				'user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);\n',
				encoding="utf-8",
			)
			command = [self._firefoxPath(), "-no-remote", "-profile", str(profile), path.as_uri()]
		elif host == "mshtml":
			command = [str(Path(os.environ["WINDIR"]) / "System32" / "mshta.exe"), str(path)]
		else:
			raise ValueError(f"Unsupported host: {host}")
		self._process = subprocess.Popen(command)
		_, self._window = _blockUntilConditionMet(
			getValue=lambda: GetWindowWithTitle(re.compile(f"^{re.escape(title)}"), BuiltIn().log),
			shouldStopEvaluator=lambda window: window is not None,
			giveUpAfterSeconds=30,
			errorMessage=f"No {host} test window",
		)
		assert self._window is not None
		if GetForegroundHwnd() != self._window.hwndVal:
			# Release Alt before requesting foreground; do not cycle through unrelated windows.
			sendKeyboardEvent(0x12, 0, 0, 0)
			sendKeyboardEvent(0x12, 0, 2, 0)
			SetForegroundWindow(self._window, BuiltIn().log)
		spy = NvdaLib.getSpyLib()
		spy.wait_for_speech_to_finish()
		# The foreground workaround can activate a menu if the window gained focus concurrently.
		spy.emulateKeyPress("escape")
		if host == "firefox":
			spy.emulateKeyPress("control+l")
			spy.emulateKeyPress("escape")
			spy.emulateKeyPress("f6")
		spy.emulateKeyPress("control+home")
		BuiltIn().should_contain(NvdaLib.getSpeechAfterKey("NVDA+upArrow"), "Definition counts")
		spy.dump_speech_to_log()
		# Verify buffer creation in NVDA's own log, rather than inferring it from the executable name.
		expectedBackend = (
			"virtualBuffers.gecko_ia2.Gecko_ia2" if host == "firefox" else "virtualBuffers.MSHTML.MSHTML"
		)
		_blockUntilConditionMet(
			getValue=lambda: (
				f"Adding new treeInterceptor to runningTable: <{expectedBackend} object"
				in Path(NvdaLib._locations.logPath).read_text(encoding="utf-8")
			),
			giveUpAfterSeconds=10,
			errorMessage=f"NVDA did not use {expectedBackend}",
		)

	def check_description_lists(self, host: str, wrapped: bool) -> None:
		"""Assert roles, group/shared counts, nesting, paragraphs, navigation, and DOM updates."""
		self._prepare(host, wrapped)
		for key, label, count, content in (
			("l", "description list", 2, "Alpha"),
			("l", "description list", 1, "Nested"),
			("l", "list", 1, "Ordinary item"),
			("shift+l", "description list", 1, "Nested"),
			("shift+l", "description list", 2, "Alpha"),
		):
			speech, braille = NvdaLib.getSpeechAndBrailleAfterKey(key)
			BuiltIn().should_contain(speech, f"{label}  with {count} item")
			BuiltIn().should_contain(speech, content)
			BuiltIn().should_contain(braille, f"{'dlst' if label == 'description list' else 'lst'}{count}")
			if label == "list":
				BuiltIn().should_not_contain(speech, "description list  with 1 item")
				BuiltIn().should_not_contain(braille, "dlst1")
		BuiltIn().should_contain(NvdaLib.getSpeechAfterKey(","), "Toggle definition")
		NvdaLib.getSpeechAfterKey("control+home")
		for term, count in (("Alpha", 2), ("Alias", 2), ("Nested", 3), ("Solo", 1)):
			speech, braille = NvdaLib.getSpeechAndBrailleAfterKey("i")
			BuiltIn().log(f"{host}: {speech!r}; braille={braille!r}")
			BuiltIn().should_contain(
				speech, f"{term}  term" + (f"  with {count} definitions" if count > 1 else "")
			)
			BuiltIn().should_contain(braille, f"trm {count} defs" if count > 1 else "trm")
			BuiltIn().should_contain(braille, term)
			if count == 1:
				BuiltIn().should_not_contain(speech, "with 1 definition")
				BuiltIn().should_not_contain(braille, "defs")
			if term == "Alpha":
				BuiltIn().should_contain(speech, "description list  with 2 items")
		# Reverse navigation visits terms, not definitions.
		for term in ("Nested", "Alias", "Alpha"):
			BuiltIn().should_contain(NvdaLib.getSpeechAfterKey("shift+i"), f"{term}  term")
		BuiltIn().should_contain(NvdaLib.getSpeechAfterKey("downArrow"), "term  with 2 definitions  Alias")
		BuiltIn().should_contain(NvdaLib.getSpeechAfterKey("downArrow"), "definition  First paragraph")
		for count in (1, 2):
			NvdaLib.getSpeechAfterKey("b")
			NvdaLib.getSpyLib().emulateKeyPress("enter")
			NvdaLib.getSpeechAfterKey("control+home")
			for term in ("Alpha", "Alias"):
				speech, braille = NvdaLib.getSpeechAndBrailleAfterKey("i")
				BuiltIn().should_end_with(
					speech, f"{term}  term" + (f"  with {count} definitions" if count > 1 else "")
				)
				if count > 1:
					BuiltIn().should_contain(braille, "trm 2 defs")
				else:
					BuiltIn().should_not_contain(speech, "definitions")
					BuiltIn().should_not_contain(braille, "defs")

	def close_description_list_host(self) -> None:
		"""Close only the isolated host created by this test."""
		if self._window:
			CloseWindow(self._window)
			self._window = None
		if self._process:
			try:
				self._process.wait(timeout=15)
			except subprocess.TimeoutExpired:
				self._process.terminate()
				self._process.wait(timeout=10)
			self._process = None
		if self._temporaryDirectory:

			def cleanup() -> bool:
				try:
					self._temporaryDirectory.cleanup()
				except OSError as error:
					if error.winerror not in (5, 32, 145):
						raise
					# Firefox children can retain/recreate profile files while shutting down.
					return False
				return True

			_blockUntilConditionMet(
				cleanup, giveUpAfterSeconds=15, errorMessage="Test profile is still locked"
			)
			self._temporaryDirectory = None
