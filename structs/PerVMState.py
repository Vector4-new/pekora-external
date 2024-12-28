from manipulation.memory import MemoryWrapper

class PerVMState:
    SCRIPT_LOADING_STATE = 0x4
    GLOBAL_STATE = 0xC
    REGISTRY_INDEX = 0x10

    STATE_NOT_RUN_YET = 0
    STATE_RUNNING = 1
    STATE_COMPLETED_ERROR = 2
    STATE_COMPLETED_SUCCESS = 3

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetLoadingState(self):
        return self.memory.ReadUInt(self.address + PerVMState.SCRIPT_LOADING_STATE)
    
    def GetGlobalState(self):
        "This global state holds the result of the require"

        return self.memory.ReadUInt(self.address + PerVMState.GLOBAL_STATE)
    
    def GetRegistryIndex(self):
        return self.memory.ReadUInt(self.address + PerVMState.REGISTRY_INDEX)

    def SetLoadingState(self, state : int):
        self.memory.WriteUInt(self.address + PerVMState.SCRIPT_LOADING_STATE, state)
    
    def SetRegistryIndex(self, index : int):
        self.memory.WriteUInt(self.address + PerVMState.REGISTRY_INDEX, index)