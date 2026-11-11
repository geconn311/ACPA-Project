## right now this handles lw, some r-types, and beq (NOT beqz, or with immediates!)
## need to include data hazard detection and pipeline stalls/flush to be able to do spectre attack

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
# format is type, parameter 1, parameter 2, parameter 3
class Instruction:
    def __init__(self, type, p1, p2, p3):
        self.type = type
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.result = None

    def __str__(self):
        return f"{self.type} {self.p1} {self.p2} {self.p3}"

# defining nop and halt instructions.
# a cpu simulation is prefilled with nop's when it's created
# and fills up with halt's after the last instruction
# no halt instruction at the end of the code file!!!
# print out either "nop nop nop" or "halt halt halt" when printed in a cpu frame
nop = Instruction("nop", "x", "x", "x")
halt = Instruction("halt", "x", "x", "x")

#creating CPUstate class
#represents the state of the CPU during 1 cycle
class CPUstate:
    def __init__(self, program):
        self.program = program
        self.fetch = nop
        self.decode = nop
        self.execute = nop
        self.memory = nop
        self.writeback = nop
        self.r1 = None
        self.r2 = None
        self.r3 = None
        self.pc = 0
        self.jumper = 0

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

    # this is a beefier method than I thought it was going to be
    #originally going to do different methods for different instruction types, and then it became "run a whole cycle"
    #now it's recursive to run the whole program
    # going to try my best to make this make sense
    def run(self):

        #creating delay for cycle - takes as long as the bottleneck
        delay = 0

        #print out time last instruction took
        print(time.time()-t)

        # once a halt gets to writeback, every other previous instruction has completed, so program can end
        if self.writeback == halt:
            return


        # R-type and B-type instructions
        if self.execute.type in ["add", "sub", "and", "or", "beq"]:

            # Get source register values
            source1 = getattr(self, self.execute.p2)
            source2 = getattr(self, self.execute.p3)

            # Execute operation
            if self.execute.type == "add":
                self.execute.result = source1 + source2

            elif self.execute.type == "sub":
                self.execute.result = source1 - source2

            elif self.execute.type == "and":
                self.execute.result = source1 & source2

            elif self.execute.type == "or":
                self.execute.result = source1 | source2

            #both parameters are registers and not immediates
            elif self.execute.type == "beq":
                if (source1-source2 == 0): self.jumper = 1
                

        # Handling memory delay + writing to registers registers for LW instructions
        # does this when a lw instruction is in memory phase
        # if type is lw, wait for time according to cache level of mem address being accessed
        if self.memory.type == "lw":
            if (delay < cacheLevel[int(self.memory.p2)]):
                delay = cacheLevel[int(self.memory.p2)]
            if self.memory.p1 == "r1":
                self.r1 = memory[int(self.memory.p2)]
            if self.memory.p1 == "r2":
                self.r2 = memory[int(self.memory.p2)]
            if self.memory.p1 == "r3":
                self.r3 = memory[int(self.memory.p2)]

        # R-type writeback
        if self.writeback.type in ["add", "sub", "and", "or"]:
            if self.writeback.p1 == "r1":
                self.r1 = self.writeback.result

            elif self.writeback.p1 == "r2":
                self.r2 = self.writeback.result

            elif self.writeback.p1 == "r3":
                self.r3 = self.writeback.result

        #jump to pc = p1
        if self.writeback.type == "beq":
            if self.jumper == 1:
                self.pc = int(self.writeback.p1)-1
            self.jumper = 0

        if self.writeback.type == "halt":
            return

        # Advance pipeline
        time.sleep(delay)
        self.writeback = self.memory
        self.memory = self.execute
        self.execute = self.decode
        self.decode = self.fetch

        # Fetch next instruction
        if self.pc < len(self.program):
            self.fetch = self.program[self.pc]
            self.pc += 1
        else:
            self.fetch = halt

        #printing cpu state
        print(self)
        print(self.pc)
        self.run()



#opening the text file, reading, and creating array of Instructions from the file
f = open("ACPAtext.txt", "r")
instructions = []
for line in f:
    type, p1, p2, p3 = line.strip().split()
    instructions.append(Instruction(type, p1, p2, p3))

#creating instance of CPUstate class
cpustate1 = CPUstate(instructions)

#advances cpustate1 for each instruction in instructions[]
#calls a halt at the end so no need for a halt in the text file!!

cpustate1.run()
