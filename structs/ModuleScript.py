import struct

from manipulation.memory import MemoryWrapper
from structs.Instance import Instance
from structs.PerVMState import PerVMState

class ModuleScript(Instance):
    BYTECODE_ADDRESS = 0x100
    VM_STATE_MAP = 0x14C
    NUM_BUCKETS = 16

    def __init__(self, instance : Instance):
        self.memory = instance.memory
        self.address = instance.address

    def OverwriteBytecode(self, bytecode : bytes):
        ( embeddedName, _, maxLength ) = struct.unpack("16sII", self.memory.ReadBytes(self.address + ModuleScript.BYTECODE_ADDRESS, 24))

        if len(bytecode) > maxLength:
            raise ValueError("bytecode is too long")
        
        # there is no valid bytecode that fits in 15 bytes, so we just assume embeddedName is actually just a pointer
        bcAddress = struct.unpack("I", embeddedName[:4])[0]

        self.memory.WriteBytes(bcAddress, bytecode)
        self.memory.WriteUInt(self.address + ModuleScript.BYTECODE_ADDRESS + 16, len(bytecode))

    def GetPerVMState(self):
        # we just assume 1 global state has required this so far...
        # this is a really ass method of extracting it but idk what else I can reasonably do considering I have no clue how maps are actually stored
        # also im not sure if num_buckets is right or the offset where buckets start
        buckets = self.memory.ReadUInt(self.address + ModuleScript.VM_STATE_MAP)
        entries = self.memory.ReadBytes(buckets + 8, self.NUM_BUCKETS * 4)

        for i in range(16):
            ptr = struct.unpack("I", entries[i * 4:i * 4 + 4])[0]

            if ptr != 0:
                # not 0 is object at end of bucket? idk
                endOfBucket = self.memory.ReadUInt(ptr)

                if endOfBucket != 0:
                    # 12 is offset from bucket/whatever to actual VMState object
                    return PerVMState(self.memory, endOfBucket + 12)
                else:
                    # hopefully this is pervmstate
                    return PerVMState(self.memory, ptr + 12)

        return None