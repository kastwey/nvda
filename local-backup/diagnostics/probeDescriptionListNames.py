"""Read real browser providers without starting NVDA or sending keyboard input.

The NVDA unit bootstrap disables speech. Presentation is called in this process;
this is not a foreground keyboard/system-test run.
"""

import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
import winreg

import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "source")]
import tests.unit  # noqa: E402, F401
import IAccessibleHandler  # noqa: E402
import aria  # noqa: E402
import config  # noqa: E402
import controlTypes  # noqa: E402
import oleacc  # noqa: E402
import textInfos  # noqa: E402
import UIAHandler  # noqa: E402
from braille.regions.properties import getControlFieldBraille  # noqa: E402
from comInterfaces import IAccessible2Lib as IA2  # noqa: E402
import comtypes.client  # noqa: E402
from comtypes import COMError  # noqa: E402
from comtypes.gen import UIAutomationClient as UIA  # noqa: E402
from NVDAObjects.UIA import chromium, web  # noqa: E402
from speech.speech import getControlFieldSpeech  # noqa: E402
from virtualBuffers.gecko_ia2 import Gecko_ia2_TextInfo  # noqa: E402


def getBrowserPath(browser: str) -> str:
	for registryRoot in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
		try:
			with winreg.OpenKey(
				registryRoot,
				rf"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\{browser}.exe",
			) as key:
				path, _ = winreg.QueryValueEx(key, "")
			if Path(path).is_file():
				return path
		except OSError:
			continue
	raise FileNotFoundError(browser)


def presentation(field: textInfos.ControlField) -> dict[str, Any]:
	formatConfig = config.conf["documentFormatting"].copy()
	formatConfig["reportLists"] = True
	return {
		"role": field["role"].name,
		"name": field.get("name"),
		"content": field.get("content"),
		"alwaysReportName": field.get("alwaysReportName"),
		"speech": [
			item
			for item in getControlFieldSpeech(
				field, [], "start_relative", formatConfig, reason=controlTypes.OutputReason.CARET,
			)
			if isinstance(item, str) and item
		],
		"braille": getControlFieldBraille(None, field, [], True, formatConfig),
	}


def probeUIA(client: Any, document: Any) -> None:
	pattern = document.GetCurrentPattern(UIA.UIA_TextPatternId).QueryInterface(UIA.IUIAutomationTextPattern)
	cache = client.CreateCacheRequest()
	cache.AddProperty(UIA.UIA_ControlTypePropertyId)
	nodes = document.FindAll(UIA.TreeScope_Descendants, client.CreateTrueCondition())
	info = chromium.ChromiumUIATextInfo.__new__(chromium.ChromiumUIATextInfo)
	root = SimpleNamespace(
		UIATextPattern=pattern,
		makeTextInfo=lambda obj: SimpleNamespace(text=pattern.RangeFromChild(obj.UIAElement).GetText(-1)),
	)
	info._obj = lambda: root
	with patch.object(UIAHandler, "handler", SimpleNamespace(clientObject=client)):
		for index in range(nodes.Length):
			element = nodes.GetElement(index)
			identifier = element.CurrentAutomationId
			if not identifier or identifier in ("probe-ready", "external-term-label", "external-definition-label"):
				continue
			roleString = element.GetCurrentPropertyValue(UIA.UIA_AriaRolePropertyId)
			role = next(
				(aria.ariaRolesToNVDARoles[token] for token in roleString.split() if token in aria.ariaRolesToNVDARoles),
				controlTypes.Role.UNKNOWN,
			)
			obj = SimpleNamespace(
				UIAElement=element.BuildUpdatedCache(cache),
				role=role,
				name=element.CurrentName,
				states=set(),
				description=element.CurrentHelpText,
				positionInfo={},
				landmark=None,
				isCurrent=controlTypes.IsCurrent.NO,
				placeholder=None,
				value=None,
				_getUIACacheablePropertyValue=element.GetCurrentPropertyValue,
			)
			field = info._getControlFieldForUIAObject(obj, startOfNode=True, endOfNode=True)
			ancestor = client.RawViewWalker.GetParentElement(element)
			listInfo = None
			while ancestor and not client.CompareElements(ancestor, document):
				if ancestor.GetCurrentPropertyValue(UIA.UIA_AriaRolePropertyId) == "list":
					listInfo = chromium._getDescriptionListInfo(ancestor)
					break
				ancestor = client.RawViewWalker.GetParentElement(ancestor)
			listField = textInfos.ControlField(
				role=controlTypes.Role.DESCRIPTIONLIST if listInfo else controlTypes.Role.LIST,
				_descriptionListInfo=listInfo,
			)
			fields = [
				textInfos.FieldCommand("controlStart", listField),
				textInfos.FieldCommand("controlStart", field),
			]
			chromium._normalizeDescriptionListTerms(fields)
			info._removeDuplicateDescriptionListNames(fields)
			if identifier in ("label-term", "label-definition", "labelledby-term", "labelledby-definition"):
				assert field.get("name") == element.CurrentName, identifier
				assert element.CurrentName in presentation(field)["speech"], identifier
				assert element.CurrentName in presentation(field)["braille"], identifier
			elif identifier in ("plain-term", "same-term", "same-definition"):
				assert "name" not in field, identifier
			print(json.dumps({
				"api": "UIA",
				"id": identifier,
				"providerRole": roleString,
				"providerName": element.CurrentName,
				"providerText": pattern.RangeFromChild(element).GetText(-1),
				"providerAria": element.GetCurrentPropertyValue(UIA.UIA_AriaPropertiesPropertyId),
				"nvdaField": presentation(field),
			}, ensure_ascii=False))


def probeIA2(windowHandle: int) -> None:
	root = IAccessibleHandler.normalizeIAccessible(oleacc.AccessibleObjectFromWindow(windowHandle, -4))
	pending = [(root, 0)]
	visited = 0
	found = 0
	while pending and visited < 1000:
		obj, childId = pending.pop()
		visited += 1
		if childId:
			continue
		if isinstance(obj, IA2.IAccessible2):
			attributes = IAccessibleHandler.splitIA2Attribs(obj.attributes)
			identifier = attributes.get("id")
			if identifier and identifier.endswith(("-term", "-definition")):
				name = obj.accName(0)
				try:
					text = obj.QueryInterface(IA2.IAccessibleText).text(0, -1)
				except COMError:
					text = None
				field = textInfos.ControlField({
					"IAccessible::role": str(obj.role()),
					"name": name,
					**{f"IAccessible2::attribute_{key}": value for key, value in attributes.items()},
				})
				# For aria-label/hidden labels the native backend sets this on non-content-name roles.
				if attributes.get("explicit-name") == "true":
					field["alwaysReportName"] = "true"
				Gecko_ia2_TextInfo.__new__(Gecko_ia2_TextInfo)._normalizeControlField(field)
				print(json.dumps({
					"api": "IA2 (provider data passed to Python normalization)",
					"id": identifier,
					"providerRole": obj.role(),
					"providerName": name,
					"providerText": text,
					"providerAttributes": attributes,
					"nvdaField": presentation(field),
				}, ensure_ascii=False))
				found += 1
		pending.extend(reversed(IAccessibleHandler.accessibleChildren(obj, 0, obj.accChildCount)))
	print("IA2_NODES", visited, "TEST_ELEMENTS", found)


def main() -> None:
	parser = argparse.ArgumentParser()
	parser.add_argument("browser", choices=("chrome", "msedge", "firefox"))
	options = parser.parse_args()
	client = comtypes.client.CreateObject(UIA.CUIAutomation8, interface=UIA.IUIAutomation)
	profile = tempfile.TemporaryDirectory(prefix="nvda-name-probe-", ignore_cleanup_errors=True)
	url = (ROOT / "testOutput" / "descriptionListAccessibleNames.html").as_uri()
	command = [getBrowserPath(options.browser)]
	if options.browser == "firefox":
		command.extend(["-no-remote", "-profile", profile.name, url])
	else:
		command.extend([
			f"--user-data-dir={profile.name}", "--no-first-run", "--no-default-browser-check",
			"--force-renderer-accessibility", "--disable-default-apps", "--disable-notifications",
			"--disable-features=CalculateNativeWinOcclusion", "--disable-backgrounding-occluded-windows",
			"--disable-renderer-backgrounding", "--window-position=60,60", "--window-size=800,700", url,
		])
	startup = subprocess.STARTUPINFO()
	startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	startup.wShowWindow = 1
	process = subprocess.Popen(command, startupinfo=startup, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	owned: list[psutil.Process] = []
	try:
		ctypes.windll.user32.WaitForInputIdle(ctypes.c_void_p(process._handle), 15000)
		condition = client.CreatePropertyCondition(UIA.UIA_ProcessIdPropertyId, process.pid)
		deadline = time.monotonic() + 30
		document = None
		window = None
		while time.monotonic() < deadline:
			window = client.GetRootElement().FindFirst(UIA.TreeScope_Children, condition)
			if not window:
				if options.browser == "firefox" and psutil.pid_exists(process.pid):
					for child in psutil.Process(process.pid).children(recursive=True):
						window = client.GetRootElement().FindFirst(
							UIA.TreeScope_Children,
							client.CreatePropertyCondition(UIA.UIA_ProcessIdPropertyId, child.pid),
						)
						if window:
							break
			if not window:
				continue
			if options.browser == "firefox" and "accessible-name probe" in window.CurrentName:
				break
			document = window.FindFirst(
				UIA.TreeScope_Descendants,
				client.CreatePropertyCondition(UIA.UIA_ControlTypePropertyId, UIA.UIA_DocumentControlTypeId),
			)
			if document and document.FindFirst(
				UIA.TreeScope_Descendants,
				client.CreatePropertyCondition(UIA.UIA_AutomationIdPropertyId, "probe-ready"),
			):
				break
		if not window or (
			options.browser != "firefox"
			and (not document or document.CurrentName != "NVDA isolated accessible-name probe 3858")
		):
			raise RuntimeError("No accessible document in the isolated browser")
		print("BROWSER", options.browser, "PID", process.pid, "WINDOW", window.CurrentName)
		if options.browser != "firefox":
			probeUIA(client, document)
		probeIA2(window.CurrentNativeWindowHandle)
	finally:
		try:
			owned = psutil.Process(process.pid).children(recursive=True)
		except psutil.NoSuchProcess:
			pass
		for child in owned:
			try:
				child.terminate()
			except psutil.NoSuchProcess:
				pass
		if process.poll() is None:
			process.terminate()
		process.wait(timeout=15)
		psutil.wait_procs(owned, timeout=10)
		profile.cleanup()


if __name__ == "__main__":
	main()