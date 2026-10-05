"""Read Windows session lock state without interacting with the secure desktop."""

import ctypes
from ctypes import wintypes


class _WTSINFOEX_LEVEL1(ctypes.Structure):
	_fields_ = [
		("SessionId", wintypes.DWORD),
		("SessionState", wintypes.DWORD),
		("SessionFlags", wintypes.LONG),
		("WinStationName", wintypes.WCHAR * 33),
		("UserName", wintypes.WCHAR * 21),
		("DomainName", wintypes.WCHAR * 18),
		("LogonTime", ctypes.c_longlong),
		("ConnectTime", ctypes.c_longlong),
		("DisconnectTime", ctypes.c_longlong),
		("LastInputTime", ctypes.c_longlong),
		("CurrentTime", ctypes.c_longlong),
		("IncomingBytes", wintypes.DWORD),
		("OutgoingBytes", wintypes.DWORD),
		("IncomingFrames", wintypes.DWORD),
		("OutgoingFrames", wintypes.DWORD),
		("IncomingCompressedBytes", wintypes.DWORD),
		("OutgoingCompressedBytes", wintypes.DWORD),
	]


class _WTSINFOEX(ctypes.Structure):
	_fields_ = [("Level", wintypes.DWORD), ("Data", _WTSINFOEX_LEVEL1)]


def isSessionUnlocked() -> bool:
	"""Fail closed if the session is locked, disconnected or cannot be queried.

	This uses the Windows 10/11 meaning of WTS_SESSIONSTATE_UNLOCK (1).
	No username, window title or content from the secure desktop is returned.
	"""
	wts = ctypes.WinDLL("wtsapi32", use_last_error=True)
	wts.WTSQuerySessionInformationW.argtypes = [
		wintypes.HANDLE,
		wintypes.DWORD,
		ctypes.c_int,
		ctypes.POINTER(ctypes.c_void_p),
		ctypes.POINTER(wintypes.DWORD),
	]
	wts.WTSQuerySessionInformationW.restype = wintypes.BOOL
	wts.WTSFreeMemory.argtypes = [ctypes.c_void_p]
	wts.WTSFreeMemory.restype = None
	buffer = ctypes.c_void_p()
	size = wintypes.DWORD()
	WTS_CURRENT_SESSION = 0xFFFFFFFF
	WTSSessionInfoEx = 25
	if not wts.WTSQuerySessionInformationW(
		None, WTS_CURRENT_SESSION, WTSSessionInfoEx, ctypes.byref(buffer), ctypes.byref(size)
	):
		return False
	try:
		if not buffer or size.value < ctypes.sizeof(_WTSINFOEX):
			return False
		info = ctypes.cast(buffer, ctypes.POINTER(_WTSINFOEX)).contents
		return info.Level == 1 and info.Data.SessionState == 0 and info.Data.SessionFlags == 1
	finally:
		wts.WTSFreeMemory(buffer)
