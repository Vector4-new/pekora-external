from ctypes import *
from manipulation.process import Process

ReadProcessMemory = windll.kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [ c_void_p, c_void_p, c_void_p, c_size_t, POINTER(c_size_t) ]
ReadProcessMemory.restype = c_int

WriteProcessMemory = windll.kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [ c_void_p, c_void_p, c_void_p, c_size_t, POINTER(c_size_t) ]
WriteProcessMemory.restype = c_int

VirtualQueryEx = windll.kernel32.VirtualQueryEx
VirtualQueryEx.argtypes = [ c_void_p, c_void_p, c_void_p, c_size_t ]
VirtualQueryEx.restype = c_size_t

VirtualProtectEx = windll.kernel32.VirtualProtectEx
VirtualProtectEx.argtypes = [ c_void_p, c_void_p, c_size_t, c_int, POINTER(c_int) ]
VirtualProtectEx.restype = c_int

class MemoryBasicInformation(Structure):
    _fields_ = [
        ( "BaseAddress", c_void_p ),
        ( "AllocationBase", c_void_p ),
        ( "AllocationProtect", c_int ),
        ( "PartitionId", c_short ),
        ( "RegionSize", c_size_t ),
        ( "State", c_int ),
        ( "Protect", c_int ),
        ( "Type", c_int )
    ]

    BaseAddress : c_void_p = 0
    AllocationBase : c_void_p = 0
    AllocationProtect : c_int = 0
    PartitionId : c_short = 0
    RegionSize : c_size_t = 0
    State : c_int = 0
    Protect : c_int = 0
    Type : c_int = 0

class MemoryWrapper:
    MAX_ADDRESS = 0x7FFFFFFF0000

    STATE_MEM_COMMIT = 0x1000
    STATE_MEM_FREE = 0x10000
    STATE_MEM_RESERVE = 0x2000

    TYPE_MEM_IMAGE = 0x1000000
    TYPE_MEM_MAPPED = 0x40000
    TYPE_MEM_PRIVATE = 0x20000

    PROTECT_PAGE_EXECUTE = 0x10
    PROTECT_PAGE_EXECUTE_READ = 0x20
    PROTECT_PAGE_EXECUTE_READWRITE = 0x40
    PROTECT_PAGE_EXECUTE_WRITECOPY = 0x80
    PROTECT_PAGE_NOACCESS = 0x1
    PROTECT_PAGE_READONLY = 0x2
    PROTECT_PAGE_READWRITE = 0x4
    PROTECT_PAGE_WRITECOPY = 0x8
    PROTECT_PAGE_TARGETS_INVALID = 0x40000000
    PROTECT_PAGE_TARGETS_NO_UPDATE = 0x40000000
    PROTECT_PAGE_GUARD = 0x100
    PROTECT_PAGE_NOCACHE = 0x200
    PROTECT_PAGE_WRITECOMBINE = 0x400

    process = None

    def __init__(self, process : Process):
        self.process = process
    
    def GetRegions(self) -> list[MemoryBasicInformation]:
        regions = []
        address = 0

        while True:
            mbi = MemoryBasicInformation()

            if VirtualQueryEx(self.process.handle, address, pointer(mbi), sizeof(mbi)) == 0:
                raise WinError(GetLastError())

            if mbi.Protect & 0xFE != 0:
                regions.append(mbi)

            address = (0 if mbi.BaseAddress == None else mbi.BaseAddress) + mbi.RegionSize

            if address >= MemoryWrapper.MAX_ADDRESS:
                break
            
        return regions
    
    def GetProtection(self, address : int) -> int:
        mbi = MemoryBasicInformation()

        if VirtualQueryEx(self.process.handle, address, pointer(mbi), sizeof(mbi)) == 0:
                raise WinError(GetLastError())
        
        return mbi.Protect

    def SetProtection(self, address : int, size : int, protection : int) -> int:
        "Returns the original protection of the page"
        
        oldProtect = c_int()

        if VirtualProtectEx(self.process.handle, address, size, protection, pointer(oldProtect)) == 0:
            raise WinError(GetLastError())
        
        return oldProtect.value

    def ReadBytes(self, address : int, size : int) -> bytes:
        arr = (c_byte * size)()

        if ReadProcessMemory(self.process.handle, address, pointer(arr), size, None) == 0:
            raise WinError(GetLastError())
        
        return bytes(arr)
    
    def WriteBytes(self, address : int, value : bytes):
        arr = (c_byte * len(value)).from_buffer_copy(value)

        if WriteProcessMemory(self.process.handle, address, pointer(arr), len(value), None) == 0:
            raise WinError(GetLastError())