from ctypes import *

OpenProcess = windll.kernel32.OpenProcess
OpenProcess.argtypes = [ c_int, c_int, c_int ]
OpenProcess.restype = c_void_p

CloseHandle = windll.kernel32.CloseHandle
CloseHandle.argtypes = [ c_void_p ]
CloseHandle.restype = c_int

EnumProcesses = windll.psapi.EnumProcesses
EnumProcesses.argtypes = [ c_void_p, c_int, POINTER(c_int) ]
EnumProcesses.restype = c_int

GetModuleFileNameExW = windll.psapi.GetModuleFileNameExW
GetModuleFileNameExW.argtypes = [ c_void_p, c_void_p, c_wchar_p, c_int ]
GetModuleFileNameExW.restype = c_int

EnumProcessModules = windll.psapi.EnumProcessModules
EnumProcessModules.argtypes = [ c_void_p, c_void_p, c_int, POINTER(c_int) ]
EnumProcessModules.restype = c_int

NtSuspendProcess = windll.ntdll.NtSuspendProcess
NtSuspendProcess.argtypes = [ c_void_p ]
NtSuspendProcess.restype = c_int

NtResumeProcess = windll.ntdll.NtResumeProcess
NtResumeProcess.argtypes = [ c_void_p ]
NtResumeProcess.restype = c_int

class Process:
    PROCESS_ALL_ACCESS = 0x000F0000 | 0x00100000 | 0xFFF
    PROCESS_ARRAY_SIZE = 4096
    PROCESS_NAME_LENGTH = 1024
    MODULES_ARRAY_SIZE = 1024

    handle = None

    def __init__(self, pid : int):
        self.handle = OpenProcess(c_int(Process.PROCESS_ALL_ACCESS), c_int(False), c_int(pid))

        if self.handle == None:
            raise WinError(GetLastError())

    def __del__(self):
        if self.handle != None:
            CloseHandle(self.handle)

    def GetExecutableName(self):
        return self.GetModuleName(0)

    def GetAllModules(self) -> list[int]:
        modules = (c_void_p * Process.MODULES_ARRAY_SIZE)()
        count = c_int(0)

        if EnumProcessModules(self.handle, pointer(modules), sizeof(modules), pointer(count)) == 0:
            raise WinError(GetLastError())
        
        return list(modules)[0:int(count.value / sizeof(c_void_p))]

    def GetModuleName(self, moduleBase) -> str:
        name = (c_wchar * Process.PROCESS_NAME_LENGTH)()

        if GetModuleFileNameExW(self.handle, moduleBase, cast(name, c_wchar_p), sizeof(name) // sizeof(c_wchar)) == 0:
            raise WinError(GetLastError())
        
        return name.value
    
    def Suspend(self):
        if NtSuspendProcess(self.handle) != 0:
            raise WinError(GetLastError())
        
    def Resume(self):
        if NtResumeProcess(self.handle) != 0:
            raise WinError(GetLastError())
        
    @staticmethod
    def GetAllProcessIDs() -> list[int]:
        processes = (c_int * Process.PROCESS_ARRAY_SIZE)()
        count = c_int(0)

        EnumProcesses(pointer(processes), sizeof(processes), pointer(count))
        
        return list(processes)[0:int(count.value / sizeof(c_int))]