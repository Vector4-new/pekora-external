# shika try not to get groomed challenge

import time

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
            perVmState.SetThreadIdentity(6)

    time.sleep(0.01)

print("Injected")