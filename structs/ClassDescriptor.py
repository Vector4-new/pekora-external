from manipulation.memory import MemoryWrapper

class ClassDescriptor:
    CLASSNAME_PTR = 0x4

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetClassName(self):
        return self.memory.ReadCPPString(self.memory.ReadUInt(self.address + ClassDescriptor.CLASSNAME_PTR))