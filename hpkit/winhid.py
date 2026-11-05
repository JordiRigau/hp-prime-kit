# -*- coding: utf-8 -*-
"""A HID device on Windows, through hid.dll, with timeouts on every read.

Imported only on Windows, since ctypes.WinDLL exists nowhere else. This moves
bytes on and off the cable and knows nothing of what they mean: hpkit/usb.py
holds that, and can be tested with no device at all.
"""
from __future__ import unicode_literals
import ctypes
from ctypes import wintypes as w

ERROR_SHARING_VIOLATION = 32
ERROR_IO_PENDING = 997
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3
FILE_FLAG_OVERLAPPED = 0x40000000
DIGCF_PRESENT = 2
DIGCF_DEVICEINTERFACE = 0x10
WAIT_OBJECT_0 = 0
INVALID = w.HANDLE(-1).value

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
setupapi = ctypes.WinDLL('setupapi', use_last_error=True)
hid = ctypes.WinDLL('hid', use_last_error=True)


class Busy(Exception):
    """Another program holds the device, and Windows gives it to one at a
    time."""


class GUID(ctypes.Structure):
    _fields_ = [('a', w.DWORD), ('b', w.WORD), ('c', w.WORD),
                ('d', ctypes.c_ubyte * 8)]


class InterfaceData(ctypes.Structure):
    _fields_ = [('cbSize', w.DWORD), ('guid', GUID), ('flags', w.DWORD),
                ('reserved', ctypes.c_size_t)]


class Caps(ctypes.Structure):
    _fields_ = [('Usage', w.USHORT), ('UsagePage', w.USHORT),
                ('InputReportByteLength', w.USHORT),
                ('OutputReportByteLength', w.USHORT),
                ('FeatureReportByteLength', w.USHORT),
                ('Reserved', w.USHORT * 17),
                ('Counts', w.USHORT * 10)]


class Overlapped(ctypes.Structure):
    _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                ('Offset', w.DWORD), ('OffsetHigh', w.DWORD),
                ('hEvent', w.HANDLE)]


kernel32.CreateFileW.restype = w.HANDLE
kernel32.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID, w.DWORD,
                                 w.DWORD, w.HANDLE]
kernel32.CloseHandle.argtypes = [w.HANDLE]
kernel32.CreateEventW.restype = w.HANDLE
kernel32.CreateEventW.argtypes = [w.LPVOID, w.BOOL, w.BOOL, w.LPCWSTR]
kernel32.ResetEvent.argtypes = [w.HANDLE]
kernel32.ReadFile.argtypes = [w.HANDLE, w.LPVOID, w.DWORD, w.LPVOID,
                              ctypes.POINTER(Overlapped)]
kernel32.WriteFile.argtypes = [w.HANDLE, w.LPCVOID, w.DWORD, w.LPVOID,
                               ctypes.POINTER(Overlapped)]
kernel32.GetOverlappedResult.argtypes = [w.HANDLE, ctypes.POINTER(Overlapped),
                                         ctypes.POINTER(w.DWORD), w.BOOL]
kernel32.WaitForSingleObject.restype = w.DWORD
kernel32.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
kernel32.CancelIo.argtypes = [w.HANDLE]
setupapi.SetupDiGetClassDevsW.restype = w.HANDLE
setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), w.LPCWSTR,
                                          w.HWND, w.DWORD]
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    w.HANDLE, w.LPVOID, ctypes.POINTER(GUID), w.DWORD,
    ctypes.POINTER(InterfaceData)]
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [
    w.HANDLE, ctypes.POINTER(InterfaceData), w.LPVOID, w.DWORD,
    ctypes.POINTER(w.DWORD), w.LPVOID]
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [w.HANDLE]
hid.HidD_GetHidGuid.argtypes = [ctypes.POINTER(GUID)]
hid.HidD_FlushQueue.argtypes = [w.HANDLE]
hid.HidD_GetPreparsedData.argtypes = [w.HANDLE, ctypes.POINTER(ctypes.c_void_p)]
hid.HidD_FreePreparsedData.argtypes = [ctypes.c_void_p]
hid.HidP_GetCaps.restype = w.LONG
hid.HidP_GetCaps.argtypes = [ctypes.c_void_p, ctypes.POINTER(Caps)]


def paths(vendor, product):
    """-> the paths of the devices present with these numbers. They are read
    off the path and not asked of the device, because a device some program
    holds cannot be opened to be asked, and that one has to be found too."""
    guid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(guid))
    devices = setupapi.SetupDiGetClassDevsW(ctypes.byref(guid), None, None,
                                            DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
    if devices == INVALID:
        raise ctypes.WinError(ctypes.get_last_error())
    wanted = 'vid_%04x&pid_%04x' % (vendor, product)
    found = []
    try:
        index = 0
        while True:
            iface = InterfaceData()
            iface.cbSize = ctypes.sizeof(InterfaceData)
            if not setupapi.SetupDiEnumDeviceInterfaces(
                    devices, None, ctypes.byref(guid), index, ctypes.byref(iface)):
                return found
            index += 1
            need = w.DWORD(0)
            setupapi.SetupDiGetDeviceInterfaceDetailW(
                devices, ctypes.byref(iface), None, 0, ctypes.byref(need), None)
            buf = ctypes.create_string_buffer(need.value)
            # The structure's own size, which is not the buffer's: a DWORD and
            # one character, aligned, so 8 on 64-bit and 6 on 32-bit.
            size = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            ctypes.cast(buf, ctypes.POINTER(w.DWORD))[0] = size
            if setupapi.SetupDiGetDeviceInterfaceDetailW(
                    devices, ctypes.byref(iface), buf, need.value, None, None):
                path = ctypes.wstring_at(ctypes.addressof(buf) + 4)
                if wanted in path.lower():
                    found.append(path)
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(devices)


class Device(object):
    """One open device. Reports are whole: the report number, then the rest."""

    def __init__(self, path):
        self.handle = kernel32.CreateFileW(
            path, GENERIC_READ | GENERIC_WRITE,
            FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING,
            FILE_FLAG_OVERLAPPED, None)
        if self.handle in (INVALID, None):
            error = ctypes.get_last_error()
            if error == ERROR_SHARING_VIOLATION:
                raise Busy()
            raise ctypes.WinError(error)
        self.event = kernel32.CreateEventW(None, True, False, None)
        prepared = ctypes.c_void_p()
        caps = Caps()
        if hid.HidD_GetPreparsedData(self.handle, ctypes.byref(prepared)):
            hid.HidP_GetCaps(prepared, ctypes.byref(caps))
            hid.HidD_FreePreparsedData(prepared)
        self.input_size = caps.InputReportByteLength
        self.output_size = caps.OutputReportByteLength
        hid.HidD_FlushQueue(self.handle)

    def close(self):
        kernel32.CloseHandle(self.event)
        kernel32.CloseHandle(self.handle)

    def _finish(self, overlapped, timeout_ms, started):
        """Wait for a call that may still be running. -> the bytes it moved,
        or None if it ran out of time and was cancelled."""
        count = w.DWORD(0)
        if not started:
            error = ctypes.get_last_error()
            if error != ERROR_IO_PENDING:
                raise ctypes.WinError(error)
            if kernel32.WaitForSingleObject(self.event, timeout_ms) != WAIT_OBJECT_0:
                kernel32.CancelIo(self.handle)
                kernel32.GetOverlappedResult(self.handle, ctypes.byref(overlapped),
                                             ctypes.byref(count), True)
                return None
        if not kernel32.GetOverlappedResult(self.handle, ctypes.byref(overlapped),
                                            ctypes.byref(count), True):
            raise ctypes.WinError(ctypes.get_last_error())
        return count.value

    def write(self, frame, timeout_ms=8000):
        """Send one report: report number 0, the frame, then zeros to its
        size, since Windows refuses a report of any other length. The limit
        leaves room for a device that holds a report back while it is busy:
        the G2 was measured doing so for 2.7 s."""
        data = (b'\x00' + frame).ljust(self.output_size, b'\x00')
        buf = ctypes.create_string_buffer(data, self.output_size)
        overlapped = Overlapped()
        overlapped.hEvent = self.event
        kernel32.ResetEvent(self.event)
        started = kernel32.WriteFile(self.handle, buf, self.output_size, None,
                                     ctypes.byref(overlapped))
        if self._finish(overlapped, timeout_ms, started) is None:
            raise OSError('writing to the device took more than %d ms'
                          % timeout_ms)

    def read(self, timeout_ms):
        """-> one report as bytes, or None if none came in time."""
        buf = ctypes.create_string_buffer(self.input_size)
        overlapped = Overlapped()
        overlapped.hEvent = self.event
        kernel32.ResetEvent(self.event)
        started = kernel32.ReadFile(self.handle, buf, self.input_size, None,
                                    ctypes.byref(overlapped))
        count = self._finish(overlapped, timeout_ms, started)
        return None if count is None else buf.raw[:count]
