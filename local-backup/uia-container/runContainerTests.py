"""Run the isolated reproduction and always restore the installed screen reader."""

import argparse
import ctypes
import os
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

import psutil
import robot
from desktopState import isSessionUnlocked


def _runInstalledReader(installedReader: Path, arguments: str, waitForExit: bool) -> int | None:
	"""Use Windows' shell broker for the installed reader's UIAccess manifest."""
	from winBindings import kernel32, shell32, user32

	isReady = False

	@user32.WINEVENTPROC
	def onWindowEvent(hook, event, hwnd, objectId, childId, threadId, eventTime):
		nonlocal isReady
		if not hwnd or objectId != 0:
			return
		className = ctypes.create_unicode_buffer(256)
		user32.GetClassName(hwnd, className, len(className))
		if className.value != "wxWindowClassNR":
			return
		title = ctypes.create_unicode_buffer(256)
		user32.InternalGetWindowText(hwnd, title, len(title))
		if title.value == "NVDA":
			isReady = True

	info = shell32.SHELLEXECUTEINFOW(
		fMask=0x40 | 0x100,  # SEE_MASK_NOCLOSEPROCESS | SEE_MASK_NOASYNC
		lpVerb="open",
		lpFile=str(installedReader),
		lpParameters=arguments,
		lpDirectory=str(installedReader.parent),
		nShow=1,
	)
	# UIAccess prevents WaitForInputIdle from working on this installation.
	# Observe creation/name changes of NVDA's window instead, without fixed sleeps.
	hook = None if waitForExit else user32.SetWinEventHook(0x8000, 0x800C, None, onWindowEvent, 0, 0, 0)
	if not waitForExit and not hook:
		raise ctypes.WinError()
	try:
		if not shell32.ShellExecuteEx(ctypes.byref(info)):
			raise ctypes.WinError()
		if not info.hProcess:
			raise RuntimeError("Windows did not return a handle for the installed reader")
		if waitForExit:
			if kernel32.WaitForSingleObject(info.hProcess, 30000) != 0:
				raise RuntimeError("Installed NVDA running check did not finish")
			exitCode = wintypes.DWORD()
			if not kernel32.GetExitCodeProcess(info.hProcess, ctypes.byref(exitCode)):
				raise ctypes.WinError()
			return exitCode.value
		isReady = bool(user32.FindWindow("wxWindowClassNR", "NVDA"))
		deadline = time.monotonic() + 30
		message = wintypes.MSG()
		while not isReady:
			while user32.PeekMessage(ctypes.byref(message), None, 0, 0, 1):
				user32.TranslateMessage(ctypes.byref(message))
				user32.DispatchMessage(ctypes.byref(message))
			if isReady:
				break
			remainingMilliseconds = max(0, int((deadline - time.monotonic()) * 1000))
			if user32.MsgWaitForMultipleObjects(0, None, False, remainingMilliseconds, 0x04FF) != 0:
				raise RuntimeError("Installed NVDA window did not become available")
		print("INSTALLED_NVDA_WINDOW_READY", isReady)
		return None
	finally:
		if info.hProcess:
			kernel32.CloseHandle(info.hProcess)
		if hook:
			user32.UnhookWinEvent(hook)


def _closeChromeProfile(profile: Path) -> None:
	"""Close only processes belonging to the profile created for this run."""
	processes: dict[int, psutil.Process] = {}
	for process in psutil.process_iter(["name", "cmdline"]):
		try:
			if (process.info["name"] or "").lower() == "chrome.exe" and (
				f"--user-data-dir={profile}" in (process.info["cmdline"] or [])
			):
				processes.update((child.pid, child) for child in process.children(recursive=True))
				processes[process.pid] = process
		except (psutil.NoSuchProcess, psutil.AccessDenied):
			continue
	for process in processes.values():
		try:
			process.terminate()
		except psutil.NoSuchProcess:
			continue
	_, alive = psutil.wait_procs(list(processes.values()), timeout=10)
	if alive:
		raise RuntimeError(f"{len(alive)} test Chrome processes did not terminate")


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("checkout", type=Path)
	parser.add_argument("output", type=Path)
	parser.add_argument(
		"--check-only", action="store_true", help="Report lock state without launching anything"
	)
	parser.add_argument("--official-suite", action="store_true", help="Run the checkout's chrome_list tests")
	args = parser.parse_args()
	isUnlocked = isSessionUnlocked()
	if args.check_only:
		print("SESSION_UNLOCKED", isUnlocked)
		return 0
	if not isUnlocked:
		print("BLOCKED: Windows session is locked or unavailable. NVDA and Chrome were not started.")
		return 2
	checkout = args.checkout.resolve()
	output = args.output.resolve()
	suite = (
		checkout / "tests/system/robot/chromeTests.robot"
		if args.official_suite
		else Path(__file__).with_name("containerNavigationTests.robot")
	)
	os.chdir(checkout)
	os.environ["UV_NO_SYNC"] = "1"
	os.environ["UV_PYTHON_PREFERENCE"] = "managed"
	os.environ["PATH"] = (
		str(Path.home() / "AppData/Local/Microsoft/WinGet/Links") + os.pathsep + os.environ["PATH"]
	)
	sys.path.insert(0, str(checkout / "source"))
	sys.path.insert(0, str(checkout / "tests/system/libraries"))
	import _chromeArgs

	profile = Path(tempfile.mkdtemp(prefix="nvda-container-chrome-"))
	originalArgs = _chromeArgs.getChromeArgs()
	_chromeArgs.getChromeArgs = lambda: (
		originalArgs
		+ f' --user-data-dir="{profile}"'
		+ " --disable-features=CalculateNativeWinOcclusion"
		+ " --disable-backgrounding-occluded-windows"
	)
	installedReader = Path(os.environ["ProgramFiles"]) / "NVDA/nvda.exe"
	try:
		return robot.run_cli(
			[
				"--argumentfile",
				str(checkout / "tests/system/robotArgs.robot"),
				"--outputdir",
				str(output),
				"--include",
				"chrome_list" if args.official_suite else "container_reproduction",
				str(suite),
			],
			exit=False,
		)
	finally:
		print("ISOLATED_CHROME_PROFILE", profile)
		try:
			_closeChromeProfile(profile)
		finally:
			_runInstalledReader(installedReader, "-r", waitForExit=False)
			checkResult = _runInstalledReader(installedReader, "--check-running", waitForExit=True)
			print("INSTALLED_NVDA_RUNNING_CHECK", checkResult)
			if checkResult != 0:
				raise RuntimeError("Installed NVDA could not be confirmed running")


if __name__ == "__main__":
	raise SystemExit(main())
