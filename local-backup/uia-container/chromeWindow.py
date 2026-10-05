"""Activate only the test Chrome window, without enumerating personal task titles."""

import ctypes
from ctypes import wintypes

import psutil
from desktopState import isSessionUnlocked


def focusChromeWindow(hwnd: int) -> bool:
	"""Use attached input queues only while the normal desktop is unlocked."""
	if not isSessionUnlocked():
		raise RuntimeError("Windows session is locked or unavailable")
	from winBindings import kernel32, user32

	processId = wintypes.DWORD()
	targetThread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(processId))
	if not targetThread or psutil.Process(processId.value).name().lower() != "chrome.exe":
		raise RuntimeError("The test window no longer belongs to Chrome")
	foreground = user32.GetForegroundWindow()
	if foreground == hwnd:
		return True
	foregroundThread = user32.GetWindowThreadProcessId(foreground, None) if foreground else 0
	currentThread = kernel32.GetCurrentThreadId()
	attached: list[int] = []
	try:
		for thread in sorted({foregroundThread, targetThread} - {0, currentThread}):
			if user32.AttachThreadInput(currentThread, thread, True):
				attached.append(thread)
		user32.ShowWindow(hwnd, 9)  # SW_RESTORE: make an occluded/minimized test window available.
		user32.SetForegroundWindow(hwnd)
		return user32.GetForegroundWindow() == hwnd
	finally:
		for thread in reversed(attached):
			user32.AttachThreadInput(currentThread, thread, False)
