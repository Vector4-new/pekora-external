# shika try not to get groomed challenge

import time
import struct
from numpy import seterr

from manipulation.process import Process
from manipulation.memory import MemoryWrapper
from structs.TaskScheduler import TaskScheduler
from structs.ModuleScript import ModuleScript
from bytecode.parser import ParseLuaBytecode
from bytecode.writer import SerialiseAndCompressProto
from bytecode.compiler import CompileSource

seterr("ignore")

TARGET = "ProjectXPlayerBeta.exe"

process = None
memory = None
baseAddress = None

for pid in Process.GetAllProcessIDs():
    try:
        process = Process(pid)

        if process.GetExecutableName().find(TARGET) != -1:
            memory = MemoryWrapper(process)
            
            for mod in process.GetAllModules():
                if process.GetModuleName(mod).find(TARGET) != -1:
                    baseAddress = mod

                    break
            
            break
    except:
        pass

if process == None:
    print("The process is not open!")

    exit()

if baseAddress == None:
    print("Failed to find base address of executable")

    exit()

print(f"Module name: \"{process.GetModuleName(baseAddress)}\"")
print(f"Base address: 0x{baseAddress:X}")
print(f"Process ID: {process.GetId()}")

TASK_SCHEDULER_OFFSET = 0x1462C90
STATE_BASE_OFFSET = 16
STATE_TOP_OFFSET = 12
STRING_LENGTH_OFFSET = 12
STRING_START_OFFSET = 0x18

process.Suspend()

scheduler = TaskScheduler(memory, memory.ReadUInt(baseAddress + TASK_SCHEDULER_OFFSET))

if scheduler.address == 0:
    print("Failed to find TaskScheduler")
    
    process.Resume()
    exit()

waitingScriptJob = scheduler.GetJob("WaitingScriptJob")

if waitingScriptJob == None:
    print("Failed to find WaitingScriptJob")

    process.Resume()
    exit()

dataModel = waitingScriptJob.GetScriptContext().GetParent()
coreGui = dataModel.FindFirstChildOfClass("CoreGui")
robloxGui = coreGui.FindFirstChild("RobloxGui")

if robloxGui == None:
    print("Failed to find CoreGui.RobloxGui")

    process.Resume()
    exit()

modules = robloxGui.FindFirstChild("Modules")

if modules == None:
    print("Failed to find CoreGui.RobloxGui.Modules")

    process.Resume()
    exit()

playerlistModule = modules.FindFirstChild("PlayerlistModule")

if playerlistModule == None:
    print("Failed to find CoreGui.RobloxGui.Modules.PlayerlistModule")

    process.Resume()
    exit()

if playerlistModule.GetClassName() != "ModuleScript":
    print("CoreGui.RobloxGui.Modules.PlayerlistModule is not a ModuleScript")

    process.Resume()
    exit()

module = ModuleScript(playerlistModule)
perVmState = module.GetPerVMState()

if perVmState == None:
    print("Failed to get PerVMState for PlayerlistModule")

    process.Resume()
    exit()

bytecode = None

try:
    f = open("scripts/init.lua", "r")
    source = f.read()

    f.close()

    bytecode = CompileSource(source)
except Exception as ex:
    print(f"Failed to compile init script: {ex}")

    process.Resume()
    exit()

proto = ParseLuaBytecode(bytecode)

module.OverwriteBytecode(SerialiseAndCompressProto(proto, 866186343))

# when we load the new bytecode it will overwrite the registry index
# so we wait for it to be changed then restore it back so require returns the correct value
# also we save the old threadref because otherwise it will get gced and PROBABLY crash
# this will cause a slight memory leak when we replace back the old ref after it succeeds running but we want the thread alive so not really a mem leak
regIndex = perVmState.GetRegistryIndex()
oldNode = perVmState.GetNode()

# this will hold the address of the string buffer we use to communicate back and forth to Lua
# this is 8mb
buffer = None

perVmState.SetNode(0)
perVmState.SetLoadingState(perVmState.STATE_NOT_RUN_YET)

process.Resume()

print("Press Escape to finalise injection")

while True:
    process.Suspend()

    match perVmState.GetLoadingState():
        case perVmState.STATE_COMPLETED_ERROR:
            print("Failed to run init script")

            perVmState.SetLoadingState(perVmState.STATE_COMPLETED_SUCCESS)
            perVmState.SetRegistryIndex(regIndex)

            exit()
        case perVmState.STATE_COMPLETED_SUCCESS:
            perVmState.SetRegistryIndex(regIndex)

            break
        case perVmState.STATE_RUNNING:
            if buffer == None:
                state = perVmState.GetModuleThread()
                base = memory.ReadUInt(state + STATE_BASE_OFFSET)
                top = memory.ReadUInt(state + STATE_TOP_OFFSET)

                stack = memory.ReadBytes(base, top - base)

                # 16 = sizeof TValue
                for obj in range(0, top - base, 16):
                    ( ptr, _, objType ) = struct.unpack("III", stack[obj:obj + 12])

                    if objType == 4:
                        encodedStrLen = memory.ReadUInt(ptr + STRING_LENGTH_OFFSET)

                        if (encodedStrLen + ptr + STRING_LENGTH_OFFSET) & 0xFFFFFFFF == 8 * 1024 * 1024:
                            # buffer has size of 8mb
                            buffer = ptr + STRING_START_OFFSET

                if buffer == None:
                    print("Couldn't find buffer; stuck in infinite loop")

                    exit()

                # signal that step 1 done
                memory.WriteUByte(buffer, 1)

                perVmState.SetThreadIdentity(6)

    process.Resume()

    time.sleep(0.01)

print("Injected")

process.Resume()

# wait a little bit for everything to be done
time.sleep(1)

process.Suspend()

victim = playerlistModule.FindFirstChild("dummymodule")

if victim == None:
    print("Failed to find victim script")

    process.Resume()
    exit()

victimMod = ModuleScript(victim)

# write custom bytecode thing
buf = struct.pack("I", buffer) + b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" + struct.pack("I", 0) + struct.pack("I", 0x800000)

memory.WriteBytes(victimMod.address + ModuleScript.BYTECODE_ADDRESS, buf)

victimPerVmState = victimMod.GetPerVMState()

process.Resume()

while True:
    i = input("> ")
    
    process.Suspend()

    if i == "load":
        print("Attempting to run ./script.lua")

        try:
            f = open("./script.lua", "r")
            source = f.read()

            f.close()

            bytecode = CompileSource(source)

            proto = ParseLuaBytecode(bytecode)

            victimMod.OverwriteBytecode(SerialiseAndCompressProto(proto, 866186343))
            
            victimPerVmState.SetLoadingState(victimPerVmState.STATE_NOT_RUN_YET)
        except Exception as ex:
            print(f"Failed to compile script: {ex}")
    else:
        try:
            bytecode = CompileSource(i)

            proto = ParseLuaBytecode(bytecode)

            victimMod.OverwriteBytecode(SerialiseAndCompressProto(proto, 866186343))
            
            victimPerVmState.SetLoadingState(victimPerVmState.STATE_NOT_RUN_YET)
        except Exception as ex:
            print(f"Failed to compile script: {ex}")

    process.Resume()