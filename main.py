# shika try not to get groomed challenge

from manipulation.process import Process
from manipulation.memory import MemoryWrapper
from structs.TaskScheduler import TaskScheduler

TARGET_EXE = "ProjectXPlayerBeta.exe"
pekora = None
base = None
memory = None

for pid in Process.GetAllProcessIDs():
    try:
        process = Process(pid)

        if process.GetExecutableName().find(TARGET_EXE) != -1:
            pekora = process
            memory = MemoryWrapper(pekora)

            for mod in pekora.GetAllModules():
                if pekora.GetModuleName(mod).find(TARGET_EXE) != -1:
                    base = mod

                    break

            break
    except:
        pass

if pekora == None:
    print("Failed to find Roblox process!")

    exit()

if base == None:
    print("Failed to find base address!")

    exit()

print(f"Process ID {pekora.GetId()}, base @ 0x{base:X}")

TASK_SCHEDULER_OFFSET = 0x1462C90

scheduler = TaskScheduler(memory, memory.ReadUInt(base + TASK_SCHEDULER_OFFSET))

for job in scheduler.GetAllJobs():
    print(f"0x{job.address:X}: {job.GetName()}")