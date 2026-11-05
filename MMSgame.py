import time

t = time.time()
#initializing memory - these are just 20 random hardcoded numbers from 0-99!
memory = [33, 84, 9, 56, 91, 74, 34, 36, 94, 76, 3, 70, 26, 88, 4, 54, 72, 20, 19, 63]

#initializing cache levels - assigns hardcoded, random cache levels to memory addresses.
#L1 cache takes 1 sec to access, L2 takes 3 secs, main mem takes 5 secs
ones = [5, 11, 14]
threes = [2, 6, 8, 12, 13, 16, 19]
cacheLevel = [
        1 if i in ones
        else 3 if i in threes
        else 5
        for i in range(20)
    ]

# creating instruction class - it's just 3 strings. 
# format is type, parameter 1, parameter 2
class Instruction:
    def __init__(self, type, p1, p2):
        self.type = type
        self.p1 = p1
        self.p2 = p2

    def __str__(self):
        return f"{self.type} {self.p1} {self.p2}"

# defining nop and halt instructions.
# a cpu simulation is prefilled with nop's when it's created
# and fills up with halt's after the last instruction
# no halt instruction at the end of the code file!!!
# print out either "nop nop nop" or "halt halt halt" when printed in a cpu frame
nop = Instruction("nop", "nop", "nop")
halt = Instruction("halt", "halt", "halt")

#creating CPUstate class
#represents the state of the CPu during 1 cycle
class CPUstate:
    def __init__(self):
        self.fetch = nop
        self.decode = nop
        self.execute = nop
        self.memory = nop
        self.writeback = nop
        self.r1 = None
        self.r2 = None
        self.r3 = None

    # prints out CPU state
    def __str__(self):
        return (
            f"--------\n"
            f"IF:{self.fetch}\n"
            f"DE:{self.decode}\n"
            f"EX:{self.execute}\n"
            f"ME:{self.memory}\n"
            f"WB:{self.writeback}\n\n"
            f"r1:{self.r1}\n"
            f"r2:{self.r2}\n"
            f"r3:{self.r3}"
        )

    # this is a beefier method than I thought it was going to be.
    # as I kept adding things (lw delay, writing to registers) it kind of was just easier to keep adding to advance vs. create another method
    # going to try my best to make this make sense
    def advance(self, instruction):

        #print out time last instruction took
        print(time.time()-t)

        # once a halt gets to writeback, every other previous instruction has completed, so program can end
        if self.writeback == halt:
            return

        # Handling memory delay + writing to registers registers for LW instructions
        # does this when a lw instruction is in memory phase
        # if type is lw, wait for time according to cache level of mem address being accessed
        if self.memory.type == "lw":
            delay = cacheLevel[int(self.memory.p2)]
            time.sleep(delay)
            if self.memory.p1 == "r1":
                self.r1 = memory[int(self.memory.p2)]
            if self.memory.p1 == "r2":
                self.r2 = memory[int(self.memory.p2)]
            if self.memory.p1 == "r3":
                self.r3 = memory[int(self.memory.p2)]

        # Advance pipeline
        self.writeback = self.memory
        self.memory = self.execute
        self.execute = self.decode
        self.decode = self.fetch
        self.fetch = instruction

        #printing cpu state
        print(self)

        # Flush pipeline, complete all previous instructions when halt is received
        if instruction == halt:
            self.advance(halt)

#creating instance of CPUstate class
cpustate1 = CPUstate()

#opening the text file, reading, and creating array of Instructions from the file
f = open("ACPAtext.txt", "r")
instructions = []
for line in f:
    type, p1, p2 = line.strip().split()
    instructions.append(Instruction(type, p1, p2))

#advances cpustate1 for each instruction in instructions[]
#calls a halt at the end so no need for a halt in the text file!!
for i in instructions:
    cpustate1.advance(i)
cpustate1.advance(halt)