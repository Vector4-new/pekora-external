from __future__ import annotations

class LocVar:
    varName : bytes = None
    startPC : int = None
    endPC : int = None

class Proto:
    source : bytes = None
    lineDefined : int = None
    lastLineDefined : int = None
    nups : int = None
    numParams : int = None
    isVararg : int = None
    maxStackSize : int = None

    code : list[int] = None
    constants : list[int] = None
    protos : list[Proto] = None
    lineInfo : list[int] = None
    locVars : list[LocVar] = None
    upvalues : list[bytes] = None