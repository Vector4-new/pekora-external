from enum import Enum
from numpy import uint32

# This shit actually made me go crazy
# Should have bit the bullet and just had a c++ bytecode converter but I like to reinvent the wheel sometimes

class InstructionEnum(Enum):
    MOVE = 0
    LOADK = 1
    LOADBOOL = 2
    LOADNIL = 3
    GETUPVAL = 4
    GETGLOBAL = 5
    GETTABLE = 6
    SETGLOBAL = 7
    SETUPVAL = 8
    SETTABLE = 9
    NEWTABLE = 10
    SELF = 11
    ADD = 12
    SUB = 13
    MUL = 14
    DIV = 15
    MOD = 16
    POW = 17
    UNM = 18
    NOT = 19
    LEN = 20
    CONCAT = 21
    JMP = 22
    EQ = 23
    LT = 24
    LE = 25
    TEST = 26
    TESTSET = 27
    CALL = 28
    TAILCALL = 29
    RETURN = 30
    FORLOOP = 31
    FORPREP = 32
    TFORLOOP = 33
    SETLIST = 34
    CLOSE = 35
    CLOSURE = 36
    VARARG = 37

class OpMode(Enum):
    ABC = 0
    ABx = 1
    AsBx = 2

opModes = [ 
    OpMode.ABC, OpMode.ABx, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABx, OpMode.ABC, OpMode.ABx, OpMode.ABC,
    OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC,
    OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.AsBx, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC,
    OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.ABC, OpMode.AsBx, OpMode.AsBx, OpMode.ABC, OpMode.ABC, OpMode.ABC,
    OpMode.ABx, OpMode.ABC
]

luaToRobloxInstruction = [
    6, 4, 0, 7, 2, 8, 1, 3, 5,
    15, 13, 9, 16, 11, 17, 10, 12, 14,
    24, 22, 18, 25, 20, 26, 19, 21, 23,
    33, 31, 27, 34, 29, 35, 28, 30, 32,
    37, 36
]

dword_10381F0 = [
	0x64181041, 0x25700080, 0x0A9540100, 0x0B240200,
	0x60DC0400, 0x0C5D80800, 0x0CA9C1000, 0x7943040,
	0x82C4082, 0x26808104, 0x0EA6D0208, 0x83A60410,
	0x0E3580820, 0x0A8041040, 0x0AB3C0082, 0x1D900104,
	0x4D680208, 0x3FC80410, 0x491C0820, 0x65CC0001,
	0x5E43040, 0x80904082, 0x1748104, 0x25990208,
	0x8D260410, 0x8D480820, 0x46EC0000, 0x0EF080000,
	0x17200000, 0x0B340000, 0x3F580000, 0x0CAD00000
]

def DaxEncodeOp(x : int, mulEven : int, addEven : int, mulOdd : int, addOdd : int):
    result = uint32(0)
    mask = uint32(1)

    for i in range(32):
        bitDesired = mask & x
        bitOdd = mask & (result * mulOdd + addOdd)
        bitEven = mask & (result * mulEven + addEven)

        if ((bitEven ^ bitOdd) != bitDesired):
            result |= mask

        mask <<= 1
	
    return result

def __popcnt(v : int):
    return v.bit_count()

def __ROL4__(num : int, bits : int):
    return (num << bits) | (num >> (32 - bits))

def JumpEncryption(a1 : int):
    v1 = uint32(1)
    v2 = uint32(0)

    for i in range(32):
        v4 = v1
        if ((__popcnt((a1 & 0x3FFFF | 0x10000000) & dword_10381F0[i]) & 1) == 0):
            v4 = 0
        v2 |= v4
        v1 = __ROL4__(v1, 1)

    return v2

SIZE_OP = 6
SIZE_A = 8
SIZE_B = 9
SIZE_C = 9
SIZE_BX = SIZE_C + SIZE_B

def CreateMask(size, off):
    return (uint32(1) << size) - uint32(1) << off

def CreateInverseMask(size, off):
    return ~CreateMask(size, off)

class LuaInstruction:
    POS_OP = 0
    POS_A = POS_OP + SIZE_OP
    POS_C = POS_A + SIZE_A
    POS_B = POS_C + SIZE_C
    POS_BX = POS_C
    
    @staticmethod
    def GetOpcode(ins : int):
        return (ins >> LuaInstruction.POS_OP) & ((1 << SIZE_OP) - 1)

    @staticmethod
    def GetArgA(ins : int):
        return (ins >> LuaInstruction.POS_A) & ((1 << SIZE_A) - 1)
    
    @staticmethod
    def GetArgB(ins : int):
        return (ins >> LuaInstruction.POS_B) & ((1 << SIZE_B) - 1)
    
    @staticmethod
    def GetArgC(ins : int):
        return (ins >> LuaInstruction.POS_C) & ((1 << SIZE_C) - 1)

    @staticmethod
    def GetArgBx(ins : int):
        return (ins >> LuaInstruction.POS_BX) & ((1 << SIZE_BX) - 1)

    @staticmethod
    def GetArgSBx(ins : int):
        return LuaInstruction.GetArgBx(ins) - (((1 << SIZE_BX) - 1) >> 1)

    @staticmethod
    def SetOpcode(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_OP, LuaInstruction.POS_OP)) | (value << LuaInstruction.POS_OP)

    @staticmethod
    def SetArgA(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_A, LuaInstruction.POS_A)) | (value << LuaInstruction.POS_A)
    
    @staticmethod
    def SetArgB(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_B, LuaInstruction.POS_B)) | (value << LuaInstruction.POS_B)
    
    @staticmethod
    def SetArgC(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_C, LuaInstruction.POS_C)) | (value << LuaInstruction.POS_C)
    
    @staticmethod
    def SetArgBx(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_BX, LuaInstruction.POS_BX)) | (value << LuaInstruction.POS_BX)
    
    @staticmethod
    def SetArgSBx(ins : int, value : int):
        return LuaInstruction.SetArgBx((ins & CreateInverseMask(SIZE_BX, LuaInstruction.POS_BX)), value + (((1 << SIZE_BX) - 1) >> 1))

class RbxInstruction:
    POS_B = 0
    POS_BX = 0
    POS_C = POS_B + SIZE_B
    POS_A = POS_C + SIZE_C
    POS_OP = POS_A + SIZE_A

    @staticmethod
    def GetOpcode(ins : int):
        return (ins >> RbxInstruction.POS_OP) & ((1 << SIZE_OP) - 1)

    @staticmethod
    def GetArgA(ins : int):
        return (ins >> RbxInstruction.POS_A) & ((1 << SIZE_A) - 1)
    
    @staticmethod
    def GetArgB(ins : int):
        return (ins >> RbxInstruction.POS_B) & ((1 << SIZE_B) - 1)
    
    @staticmethod
    def GetArgC(ins : int):
        return (ins >> RbxInstruction.POS_C) & ((1 << SIZE_C) - 1)

    @staticmethod
    def GetArgBx(ins : int):
        return (ins >> RbxInstruction.POS_BX) & ((1 << SIZE_BX) - 1)

    @staticmethod
    def GetArgSBx(ins : int):
        return RbxInstruction.GetArgBx(ins) - (((1 << SIZE_BX) - 1) >> 1)

    @staticmethod
    def SetOpcode(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_OP, RbxInstruction.POS_OP)) | (value << RbxInstruction.POS_OP)

    @staticmethod
    def SetArgA(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_A, RbxInstruction.POS_A)) | (value << RbxInstruction.POS_A)
    
    @staticmethod
    def SetArgB(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_B, RbxInstruction.POS_B)) | (value << RbxInstruction.POS_B)
    
    @staticmethod
    def SetArgC(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_C, RbxInstruction.POS_C)) | (value << RbxInstruction.POS_C)
    
    @staticmethod
    def SetArgBx(ins : int, value : int):
        return (ins & CreateInverseMask(SIZE_BX, RbxInstruction.POS_BX)) | (value << RbxInstruction.POS_BX)
    
    @staticmethod
    def SetArgSBx(ins : int, value : int):
        return RbxInstruction.SetArgBx((ins & CreateInverseMask(SIZE_BX, RbxInstruction.POS_BX)), value + (((1 << SIZE_BX) - 1) >> 1))