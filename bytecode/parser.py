import struct

from bytecode.objects import Proto, LocVar

def ReadString(bytecode : bytes, sizeofSizeT : int, offset : int):
    if sizeofSizeT == 4:
        size = struct.unpack("I", bytecode[offset:offset + 4])[0]
    else:
        size = struct.unpack("Q", bytecode[offset:offset + 8])[0]

    if size == 0:
        return ( offset + sizeofSizeT, b"" )

    # -1 for null byte
    return ( offset + sizeofSizeT + size, struct.unpack(f"{size - 1}s", bytecode[offset + sizeofSizeT:offset + sizeofSizeT + size - 1])[0] )

def ReadProto(bytecode : bytes, sizeofSizeT : int, offset : int):
    p = Proto()

    ( offset, source ) = ReadString(bytecode, sizeofSizeT, offset)
    ( lineDefined, lastLineDefined, nups, numParams, isVararg, maxStackSize ) = struct.unpack("iiBBBB", bytecode[offset:offset + 12])

    sizeCode = struct.unpack("I", bytecode[offset + 12:offset + 16])[0]
    instructions = []

    offset += 16

    for _ in range(sizeCode):
        instructions.append(struct.unpack("I", bytecode[offset:offset + 4])[0])

        offset += 4

    sizeK = struct.unpack("I", bytecode[offset:offset + 4])[0]
    constants = []

    offset += 4

    for _ in range(sizeK):
        constType = struct.unpack("B", bytecode[offset:offset + 1])[0]

        match constType:
            case 0:
               constants.append(None)

               offset += 1
            case 1: # LUA_TBOOLEAN
                constants.append(struct.unpack("B", bytecode[offset + 1:offset + 2])[0] == 1)

                offset += 2
            case 3: # LUA_NUMBER
                constants.append(struct.unpack("d", bytecode[offset + 1:offset + 9])[0])

                offset += 9
            case 4: # LUA_STRING
                ( offset, s ) = ReadString(bytecode, sizeofSizeT, offset + 1)

                constants.append(s)
            case _:
                raise ValueError(f"invalid bytecode: bad constant type {constType}")

    sizeP = struct.unpack("I", bytecode[offset:offset + 4])[0]
    protos = []

    offset += 4

    for _ in range(sizeP):
        ( offset, proto ) = ReadProto(bytecode, sizeofSizeT, offset)

        protos.append(proto)

    sizeLineInfo = struct.unpack("I", bytecode[offset:offset + 4])[0]
    lineInfo = []

    offset += 4

    for _ in range(sizeLineInfo):
        lineInfo.append(struct.unpack("I", bytecode[offset:offset + 4])[0])

        offset += 4

    sizeLocVars = struct.unpack("I", bytecode[offset:offset + 4])[0]
    locVars = []

    offset += 4

    for _ in range(sizeLocVars):
        lv = LocVar()

        ( offset, lv.varName ) = ReadString(bytecode, sizeofSizeT, offset)
        ( lv.startPC, lv.endPC ) = struct.unpack("II", bytecode[offset:offset + 8])

        locVars.append(lv)

        offset += 8

    sizeUpvalues = struct.unpack("I", bytecode[offset:offset + 4])[0]
    upvalues = []

    offset += 4

    for _ in range(sizeUpvalues):
        ( offset, upvalName ) = ReadString(bytecode, sizeofSizeT, offset)

        upvalues.append(upvalName)

    p.source = source
    p.lineDefined = lineDefined
    p.lastLineDefined = lastLineDefined
    p.nups = nups
    p.numParams = numParams
    p.isVararg = isVararg
    p.maxStackSize = maxStackSize
    p.code = instructions
    p.constants = constants
    p.protos = protos
    p.lineInfo = lineInfo
    p.locVars = locVars
    p.upvalues = upvalues

    return ( offset, p )

def ParseLuaBytecode(bytecode : bytes):
    ( magic, version, format, endianness, intSize, sizetSize, instructionSize, doubleSize, isIntegral ) = struct.unpack("4sbbbbbbbb", bytecode[:12])

    if magic != b"\x1BLua" or version != 0x51 or format != 0 or endianness != 1 or intSize != 4 or (sizetSize != 4 and sizetSize != 8) or instructionSize != 4 or doubleSize != 8 or isIntegral != 0:
        raise ValueError("invalid bytecode")
    
    ( _, mainProto ) = ReadProto(bytecode, sizetSize, 12)

    return mainProto