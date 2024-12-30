# shika try not to get groomed challenge

import time
import struct

from manipulation.process import Process
from manipulation.memory import MemoryWrapper
from structs.TaskScheduler import TaskScheduler
from structs.ModuleScript import ModuleScript
from bytecode.parser import ParseLuaBytecode
from bytecode.writer import SerialiseAndCompressProto
from bytecode.compiler import CompileSource

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

scheduler = TaskScheduler(memory, memory.ReadUInt(baseAddress + TASK_SCHEDULER_OFFSET))

if scheduler.address == 0:
    print("Failed to find TaskScheduler")
    
    exit()

waitingScriptJob = scheduler.GetJob("WaitingScriptJob")

if waitingScriptJob == None:
    print("Failed to find WaitingScriptJob")

    exit()

dataModel = waitingScriptJob.GetScriptContext().GetParent()
robloxGui = dataModel.FindFirstChildOfClass("CoreGui").FindFirstChild("RobloxGui")

if robloxGui == None:
    print("Failed to find CoreGui.RobloxGui")

    exit()

modules = robloxGui.FindFirstChild("Modules")

if modules == None:
    print("Failed to find CoreGui.RobloxGui.Modules")

    exit()

playerlistModule = modules.FindFirstChild("PlayerlistModule")

if playerlistModule == None:
    print("Failed to find CoreGui.RobloxGui.Modules.PlayerlistModule")

    exit()

if playerlistModule.GetClassName() != "ModuleScript":
    print("CoreGui.RobloxGui.Modules.PlayerlistModule is not a ModuleScript")

module = ModuleScript(playerlistModule)
perVmState = module.GetPerVMState()

if perVmState == None:
    print("Failed to get PerVMState for PlayerlistModule")

    exit()

bytecode = None

try:
    f = open("scripts/init.lua", "r")
    source = f.read()

    f.close()

    bytecode = CompileSource(source)
except Exception as ex:
    print(f"Failed to compile init script: {ex}")

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

print("Press Escape to finalise injection")

while True:
    match perVmState.GetLoadingState():
        case perVmState.STATE_COMPLETED_ERROR:
            print("Failed to run init script")

            perVmState.SetLoadingState(perVmState.STATE_COMPLETED_SUCCESS)
            perVmState.SetNode(oldNode)
            perVmState.SetRegistryIndex(regIndex)

            exit()
        case perVmState.STATE_COMPLETED_SUCCESS:
            perVmState.SetNode(oldNode)
            perVmState.SetRegistryIndex(regIndex)

            break
        case perVmState.STATE_RUNNING:
            if buffer == None:
                # suspend so base/top don't move around
                process.Suspend()

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
                    print("Failed to get string buffer; stuck in infinite loop")

                    exit()

                # signal that we are done here
                memory.WriteUByte(buffer, 1)

                perVmState.SetThreadIdentity(6)

                process.Resume()

    time.sleep(0.01)

print("Injected")