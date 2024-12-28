import typing
import struct

from manipulation.memory import MemoryWrapper

class ClassDescriptor:
    CLASSNAME_PTR = 0x4
    BASE_CLASS = 0x1D8
    DERIVED_CLASSES_VECTOR = 0x1CC

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetClassName(self):
        return self.memory.ReadCPPString(self.memory.ReadUInt(self.address + ClassDescriptor.CLASSNAME_PTR))
    
    def GetRootDescriptor(self):
        "The root descriptor is the descriptor that every object inherits from"

        base = self.GetBaseClass()

        if base == None:
            return typing.cast(ClassDescriptor, self)
        
        return typing.cast(ClassDescriptor, base.GetRootDescriptor())
    
    def GetBaseClass(self):
        basePtr = self.memory.ReadUInt(self.address + ClassDescriptor.BASE_CLASS)

        if basePtr == 0:
            return None
        
        return ClassDescriptor(self.memory, basePtr)

    def GetDerivedClasses(self):
        deriveds : list[ClassDescriptor] = []
        ( start, end ) = struct.unpack("II", self.memory.ReadBytes(self.address + ClassDescriptor.DERIVED_CLASSES_VECTOR, 8))

        derivedBytes = self.memory.ReadBytes(start, end - start)

        for derived in range(start, end, 8):
            derivedAddr = struct.unpack("I", derivedBytes[derived - start:derived - start + 4])[0]

            if derivedAddr != 0:
                deriveds.append(ClassDescriptor(self.memory, derivedAddr))

        return deriveds

    # TODO: reflection maybe