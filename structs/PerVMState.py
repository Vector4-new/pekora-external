from manipulation.memory import MemoryWrapper

class PerVMState:
    SCRIPT_LOADING_STATE = 0x4
    NODE = 0x8
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
    
    def GetNode(self):
        return self.memory.ReadUInt(self.address + PerVMState.NODE)

    def GetGlobalState(self):
        "This global state holds the result of the require"

        return self.memory.ReadUInt(self.address + PerVMState.GLOBAL_STATE)
    
    def GetRegistryIndex(self):
        return self.memory.ReadUInt(self.address + PerVMState.REGISTRY_INDEX)

    def SetLoadingState(self, state : int):
        self.memory.WriteUInt(self.address + PerVMState.SCRIPT_LOADING_STATE, state)
    
    def SetNode(self, node : int):
        self.memory.WriteUInt(self.address + PerVMState.NODE, node)

    def SetRegistryIndex(self, index : int):
        self.memory.WriteUInt(self.address + PerVMState.REGISTRY_INDEX, index)

    def GetModuleThread(self):
        # doesnt seem to be node, maybe they changed in this version

        nodeIntrusive = self.GetNode()
        weakFunctionRef = self.memory.ReadUInt(nodeIntrusive + 4)
        stateIntrusive = self.memory.ReadUInt(weakFunctionRef + 0x14)
        state = self.memory.ReadUInt(stateIntrusive + 8)

        return state

    # wrapper function because im not making seperate shit for it to be used exactly once
    def SetThreadIdentity(self, identity : int):
        state = self.GetModuleThread()
        bitfield = self.memory.ReadUByte(state - 32)

        # first 5 bits reserved for identity
        # rest are other flags
        self.memory.WriteUByte(state - 32, (bitfield & 0xE0) | (identity & 0x1F))