"""Run the isolated reproduction and always restore the installed screen reader."""

import argparse
import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import psutil
import robot

from desktopState import isSessionUnlocked


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("checkout", type=Path)
	parser.add_argument("output", type=Path)
	parser.add_argument("--check-only", action="store_true", help="Report lock state without launching anything")
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
		readerProcess = subprocess.Popen([str(installedReader), "-r"])
		# Wait for the GUI input queue, not a fixed sleep or a terminal polling loop.
		user32 = ctypes.WinDLL("user32", use_last_error=True)
		user32.WaitForInputIdle.argtypes = [wintypes.HANDLE, wintypes.DWORD]
		user32.WaitForInputIdle.restype = wintypes.DWORD
		user32.WaitForInputIdle(int(readerProcess._handle), 15000)
		for process in psutil.process_iter(["name", "cmdline"]):
			try:
				if (process.info["name"] or "").lower() == "chrome.exe" and any(
					argument == f"--user-data-dir={profile}" for argument in process.info["cmdline"] or []
				):
					for child in process.children(recursive=True):
						child.terminate()
					process.terminate()
			except (psutil.NoSuchProcess, psutil.AccessDenied):
				continue
		print("INSTALLED_NVDA_RUNNING_CHECK", subprocess.run([str(installedReader), "--check-running"]).returncode)
		print("ISOLATED_CHROME_PROFILE", profile)


if __name__ == "__main__":
	raise SystemExit(main())
