import lz4.frame
import xxhash
import struct
from numpy import uint32

from bytecode.objects import Proto
from manipulation.instruction import InstructionEnum, OpMode, LuaInstruction, RbxInstruction, JumpEncryption, DaxEncodeOp, opModes, luaToRobloxInstruction

def SerialiseString(s : bytes, strings : list[bytes]):
    try:
        return struct.pack("I", strings.index(s) + 1)
    except ValueError:
        strings.append(s)

        return struct.pack("I", len(strings))

def SerialiseProto(proto : Proto, encodeKey : int, strings : list[bytes]):
    chunk = struct.pack("IIIIIIBBBB", len(proto.protos), len(proto.constants), len(proto.code), len(proto.locVars), len(proto.lineInfo), len(proto.upvalues), proto.maxStackSize, proto.isVararg, proto.nups, proto.numParams)

    for const in proto.constants:
        if type(const) == None:
            chunk += b"\x00"
        elif type(const) == bool:
            if const:
                chunk += b"\x02"
            else:
                chunk += b"\x01"
        elif type(const) == float:
            chunk += b"\x03"
            chunk += struct.pack("d", const)
        elif type(const) == bytes:
            print(const)
            chunk += b"\x04"
            chunk += SerialiseString(const, strings)
            print(len(strings))

    lineIndex = 0
    lastLine = 0

    for line in proto.lineInfo:
        lineData = line ^ ((lineIndex << 8) & 0xFFFFFFFF)
        chunk += struct.pack("I", lineData - lastLine)

        lastLine = lineData
        lineIndex += 1

    for locvar in proto.locVars:
        chunk += struct.pack("II", locvar.startPC, locvar.endPC)
        chunk += SerialiseString(locvar.varName, strings)

    for upval in proto.upvalues:
        chunk += SerialiseString(upval, strings)

    i = 0

    for code in proto.code:
        converted = RbxInstruction.SetOpcode(uint32(0), luaToRobloxInstruction[LuaInstruction.GetOpcode(code)])

        # tailcalls not generated
        if LuaInstruction.GetOpcode(code) == InstructionEnum.TAILCALL.value:
            converted = RbxInstruction.SetOpcode(converted, luaToRobloxInstruction[InstructionEnum.CALL.value])

        match opModes[LuaInstruction.GetOpcode(code)]:
            case OpMode.ABC:
                converted = RbxInstruction.SetArgA(converted, LuaInstruction.GetArgA(code))
                converted = RbxInstruction.SetArgB(converted, LuaInstruction.GetArgB(code))
                converted = RbxInstruction.SetArgC(converted, LuaInstruction.GetArgC(code))
            case OpMode.ABx:
                converted = RbxInstruction.SetArgA(converted, LuaInstruction.GetArgA(code))
                converted = RbxInstruction.SetArgBx(converted, LuaInstruction.GetArgBx(code))
            case OpMode.AsBx:
                converted = RbxInstruction.SetArgA(converted, LuaInstruction.GetArgA(code))
                converted = RbxInstruction.SetArgSBx(converted, LuaInstruction.GetArgSBx(code))

        match LuaInstruction.GetOpcode(code):
            case InstructionEnum.MOVE.value:
                converted = RbxInstruction.SetArgC(converted, 1)
            case InstructionEnum.JMP.value:
                converted = JumpEncryption(converted ^ (-10065 * i))
                converted = RbxInstruction.SetOpcode(converted, luaToRobloxInstruction[LuaInstruction.GetOpcode(code)])
            case InstructionEnum.CALL.value:
                converted = DaxEncodeOp(converted, uint32(0x72394BC8), uint32(i) + 1470882913, uint32(0xA1F3D8AF), uint32(i))
                converted = RbxInstruction.SetOpcode(converted, luaToRobloxInstruction[LuaInstruction.GetOpcode(code)])
            case InstructionEnum.RETURN.value:
                converted = DaxEncodeOp(converted, i, uint32(0x57ABE461), uint32(i) - uint32(1577854801), uint32(0x263F433D))
                converted = RbxInstruction.SetOpcode(converted, luaToRobloxInstruction[LuaInstruction.GetOpcode(code)])
            case InstructionEnum.CLOSURE.value:
                converted = DaxEncodeOp(converted, 0x961C86, i, 0xA1F3D8AF, i + 641680189)
                converted = RbxInstruction.SetOpcode(converted, luaToRobloxInstruction[LuaInstruction.GetOpcode(code)])

        converted = converted * encodeKey

        chunk += struct.pack("I", converted)

        i += 1

    for child in proto.protos:
        chunk += SerialiseProto(child, encodeKey, strings)

    return chunk

def SerialiseMainProto(proto : Proto, encodeKey : int):
    bytecode = b""
    strings = []

    bytecode += struct.pack("B", 0)

    # string table offset
    pos = len(bytecode)

    bytecode += struct.pack("I", 0)

    bytecode += SerialiseProto(proto, encodeKey, strings)

    stringsStart = len(bytecode)

    bytecode += struct.pack("I", len(strings))

    for string in strings:
        bytecode += struct.pack("I", len(string))

    for string in strings:
        bytecode += string

    bytecode = bytecode[0:pos] + struct.pack("I", stringsStart - pos) + bytecode[pos+4:]

    return bytecode

def CompressBytecode(bytecode : bytes):
    # TODO: does this work fine lol
    compressed = lz4.frame.compress(bytecode, store_size=False)

    # remove frame so we only have compressed data
    compressed = compressed[11:-4]

    preFinal = b"RSB1" + struct.pack("I", len(bytecode)) + compressed

    hash = xxhash.xxh32(preFinal, seed=42).intdigest()

    final = b""

    for i in range(len(preFinal)):
        hashByte = (hash >> ((i % 4) * 8)) & 0xFF
        char = preFinal[i]
        final += chr((char ^ hashByte + ((i * 41) & 0xFF)) & 0xFF).encode("latin-1")

    return final

def SerialiseAndCompressProto(proto : Proto, encodeKey : int):
    bytecode = SerialiseMainProto(proto, encodeKey)
    compressed = CompressBytecode(bytecode)

    return compressed