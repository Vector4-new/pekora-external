import struct

from manipulation.memory import MemoryWrapper
from structs.ClassDescriptor import ClassDescriptor

class Instance:
    CLASS_DESCRIPTOR = 0xC
    INSTANCE_NAME_PTR = 0x28
    INSTANCE_PARENT_PTR = 0x34
    INSTANCE_CHILDREN_VECTOR_PTR = 0x2C

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetClassDescriptor(self):
        return ClassDescriptor(self.memory, self.memory.ReadUInt(self.address + Instance.CLASS_DESCRIPTOR))
    
    def GetName(self):
        return self.memory.ReadCPPString(self.memory.ReadUInt(self.address + Instance.INSTANCE_NAME_PTR))
    
    def GetClassName(self):
        return self.GetClassDescriptor().GetClassName()
    
    def GetParent(self):
        addr = self.memory.ReadUInt(self.address + Instance.INSTANCE_PARENT_PTR)

        if addr == 0:
            return None
        
        return Instance(self.memory, addr)
    
    def GetChildren(self):
        children : list[Instance] = []
        childrenPtr = self.memory.ReadUInt(self.address + Instance.INSTANCE_CHILDREN_VECTOR_PTR)

        if childrenPtr != 0:            
            ( start, end ) = struct.unpack("II", self.memory.ReadBytes(childrenPtr, 8))

            childrenBytes = self.memory.ReadBytes(start, end - start)

            for child in range(start, end, 8):
                childAddr = struct.unpack("I", childrenBytes[child - start:child - start + 4])[0]

                if childAddr != 0:
                    children.append(Instance(self.memory, childAddr))

        return children
    
    def FindFirstChild(self, name : str):
        for child in self.GetChildren():
            if child.GetName() == name:
                return child
            
        return None
    
    def FindFirstChildOfClass(self, className : str):
        for child in self.GetChildren():
            if child.GetClassName() == className:
                return child
            
        return None