import struct

from manipulation.memory import MemoryWrapper

class Job:
    JOB_SIZE = 12
    JOB_NAME = 0x54
    PHYSICS_DATAMODEL = 0x4C

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetName(self) -> str:
        ( embeddedName, length, maxLength ) = struct.unpack("16sII", self.memory.ReadBytes(self.address + Job.JOB_NAME, 24))

        if maxLength > 15:
            return self.memory.ReadBytes(struct.unpack("I", embeddedName[:4])[0], length).decode()
        
        return embeddedName[:length].decode()

    def GetDataModel(self) -> int:
        "TODO: return `Instance` when it is implemented"

        if self.GetName() != "Physics":
            raise ValueError("Not a `Physics` job")
        
        return self.memory.ReadUInt(self.address + Job.PHYSICS_DATAMODEL)

class TaskScheduler:
    JOBS_VECTOR = 0x228

    memory = None
    address = None

    def __init__(self, memory : MemoryWrapper, address : int):
        self.memory = memory
        self.address = address

    def GetAllJobs(self) -> list[Job]:
        jobs = []

        ( start, end ) = struct.unpack("II", self.memory.ReadBytes(self.address + TaskScheduler.JOBS_VECTOR, 8))

        allJobsBytes = self.memory.ReadBytes(start, end - start)

        for job in range(start, end, Job.JOB_SIZE):
            jobs.append(Job(self.memory, struct.unpack("I", allJobsBytes[job - start:job - start + 4])[0]))

        return jobs