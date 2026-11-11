import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
import os
import sys
import subprocess
import time
import ctypes

def start_bgm(music_path):
    try:
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW('close bgm', None, 0, None)
        cmd = f'open "{music_path}" type mpegvideo alias bgm'
        winmm.mciSendStringW(cmd, None, 0, None)
        winmm.mciSendStringW('setaudio bgm volume to 100', None, 0, None)
        winmm.mciSendStringW('play bgm repeat', None, 0, None)
        winmm.mciSendStringW('setaudio bgm volume to 100', None, 0, None)
    except Exception:
        pass

def stop_bgm():
    try:
        winmm = ctypes.windll.winmm
        winmm.mciSendStringW('stop bgm', None, 0, None)
        winmm.mciSendStringW('close bgm', None, 0, None)
    except Exception:
        pass

# --- Memory & Cache Simulation Constants ---
# Memory array: 20 entries
memory = [33, 84, 9, 56, 91, 74, 34, 36, 94, 76, 3, 70, 26, 88, 4, 54, 72, 20, 19, 63]

# Cache tiers:
# L1 cache: 1s latency (addresses 5, 11, 14) -> Prep Counter
# L2 cache: 3s latency (addresses 2, 6, 8, 12, 13, 16, 19) -> Kitchen Pantry
# Main memory: 5s latency (all others) -> Walk-In Freezer
ones = [5, 11, 14]
threes = [2, 6, 8, 12, 13, 16, 19]
cacheLevel = [
    1 if i in ones
    else 3 if i in threes
    else 5
    for i in range(20)
]

class Instruction:
    def __init__(self, type_op, p1="x", p2="x", p3="x"):
        self.type = type_op
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3
        self.result = None

    def __str__(self):
        if self.type in ["nop", "halt"]:
            return self.type
        parts = [self.type, self.p1, self.p2]
        if self.p3 != "x":
            parts.append(self.p3)
        return " ".join(parts)

nop = Instruction("nop", "x", "x", "x")
halt = Instruction("halt", "x", "x", "x")


class KitchenPipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kitchen Espionage - Part 2 (Pipeline & Cache Latency)")
        self.root.geometry("740x720")
        self.root.configure(bg="#2c3e50")

        # Load program instructions
        self.program = self._load_program()
        self._init_cpu_state()

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # --- 1. VISUAL CANVAS ---
        self.canvas = tk.Canvas(root, width=700, height=200, bg="#ecf0f1", highlightthickness=0)
        self.canvas.pack(pady=10)

        # Draw Walk-In Freezer (Main Memory - 5s) - Right
        self.freezer_img = PhotoImage(file=os.path.join(script_dir, "freezer.png"))
        self.canvas.create_image(580, 95, image=self.freezer_img, tags="freezer")

        # Draw Pantry / Spice Rack (L2 Cache - 3s) - Center
        self.canvas.create_rectangle(310, 30, 430, 160, fill="#f39c12", outline="#d35400", width=2)
        self.canvas.create_text(370, 95, text="Kitchen Pantry\n(L2 Cache - 3s)", justify="center", font=("Arial", 10, "bold"), fill="white")

        # Draw Prep Counter (L1 Cache - 1s) - Left
        self.counter_img = PhotoImage(file=os.path.join(script_dir, "counter.png"))
        self.canvas.create_image(120, 140, image=self.counter_img, tags="counter")

        # Draw Chef Sprite
        self.chef_img = PhotoImage(file=os.path.join(script_dir, "chef.png"))
        self.chef_img = self.chef_img.subsample(2, 2)
        self.canvas.create_image(120, 60, image=self.chef_img, tags="chef")

        # Audio Setup
        self.music_on = True
        self.music_path = os.path.join(script_dir, "restaurant_music.mp3")
        if os.path.exists(self.music_path):
            start_bgm(self.music_path)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- 2. STATUS HUD ---
        self.cycle_label = tk.Label(root, text="Cycle: 0 | CPU Initialized", bg="#2c3e50", fg="#f1c40f", font=("Arial", 12, "bold"))
        self.cycle_label.pack(pady=2)

        self.status_label = tk.Label(root, text="Pipeline ready. Click 'Step Next Cycle' or 'Auto Run'.", bg="#2c3e50", fg="white", font=("Arial", 10))
        self.status_label.pack(pady=2)

        self.latency_label = tk.Label(root, text="Memory Access Latency: --", bg="#2c3e50", fg="#bdc3c7", font=("Arial", 10, "italic"))
        self.latency_label.pack(pady=2)

        # --- 3. PIPELINE STAGES DISPLAY ---
        pipe_outer = tk.LabelFrame(root, text="5-STAGE CPU PIPELINE", bg="#34495e", fg="white", font=("Arial", 11, "bold"), padx=10, pady=10)
        pipe_outer.pack(pady=8, fill="x", padx=20)

        stages = [
            ("IF", "Instruction Fetch", "fetch"),
            ("DE", "Decode", "decode"),
            ("EX", "Execute", "execute"),
            ("ME", "Memory Access", "memory"),
            ("WB", "Write Back", "writeback"),
        ]

        self.stage_widgets = {}
        for idx, (abbr, name, attr) in enumerate(stages):
            box = tk.Frame(pipe_outer, bg="#2c3e50", bd=2, relief="groove", width=120, height=75)
            box.grid(row=0, column=idx * 2, padx=4, pady=4, sticky="nsew")
            box.grid_propagate(False)

            title_lbl = tk.Label(box, text=abbr, bg="#1abc9c", fg="white", font=("Arial", 10, "bold"))
            title_lbl.pack(fill="x")

            sub_lbl = tk.Label(box, text=name, bg="#2c3e50", fg="#95a5a6", font=("Arial", 7))
            sub_lbl.pack()

            inst_lbl = tk.Label(box, text="nop", bg="#2c3e50", fg="#ecf0f1", font=("Consolas", 10, "bold"))
            inst_lbl.pack(expand=True)

            self.stage_widgets[attr] = inst_lbl

            if idx < len(stages) - 1:
                arrow = tk.Label(pipe_outer, text="➜", bg="#34495e", fg="#e67e22", font=("Arial", 14, "bold"))
                arrow.grid(row=0, column=idx * 2 + 1)

        # --- 4. REGISTERS & PROGRAM COUNTER HUD ---
        reg_frame = tk.Frame(root, bg="#2c3e50")
        reg_frame.pack(pady=6)

        self.pc_lbl = tk.Label(reg_frame, text="PC: 0", bg="#34495e", fg="#f1c40f", font=("Consolas", 11, "bold"), padx=12, pady=4, bd=1, relief="ridge")
        self.pc_lbl.pack(side="left", padx=5)

        self.r1_lbl = tk.Label(reg_frame, text="r1: None", bg="#34495e", fg="white", font=("Consolas", 11), padx=12, pady=4, bd=1, relief="ridge")
        self.r1_lbl.pack(side="left", padx=5)

        self.r2_lbl = tk.Label(reg_frame, text="r2: None", bg="#34495e", fg="white", font=("Consolas", 11), padx=12, pady=4, bd=1, relief="ridge")
        self.r2_lbl.pack(side="left", padx=5)

        self.r3_lbl = tk.Label(reg_frame, text="r3: None", bg="#34495e", fg="white", font=("Consolas", 11), padx=12, pady=4, bd=1, relief="ridge")
        self.r3_lbl.pack(side="left", padx=5)

        # --- 5. CONTROL PANEL ---
        ctrl_frame = tk.Frame(root, bg="#34495e", bd=2, relief="groove", padx=10, pady=8)
        ctrl_frame.pack(pady=10, fill="x", padx=20)

        self.btn_step = tk.Button(ctrl_frame, text="▶ Step Next Cycle", command=self.step_cycle, bg="#3498db", fg="white", font=("Arial", 10, "bold"), width=18)
        self.btn_step.pack(side="left", padx=10)

        self.btn_auto = tk.Button(ctrl_frame, text="⏩ Auto Run", command=self.toggle_auto_run, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), width=16)
        self.btn_auto.pack(side="left", padx=10)

        self.btn_reset = tk.Button(ctrl_frame, text="🔄 Reset", command=self.reset_pipeline, bg="#e74c3c", fg="white", font=("Arial", 10), width=12)
        self.btn_reset.pack(side="left", padx=10)

        self.btn_help = tk.Button(ctrl_frame, text="📋 Instructions", command=self.show_instructions, bg="#16a085", fg="white", font=("Arial", 10, "bold"), width=14)
        self.btn_help.pack(side="left", padx=10)

        self.btn_audio = tk.Button(ctrl_frame, text="🔊 Music: ON", command=self.toggle_music, bg="#2980b9", fg="white", font=("Arial", 10, "bold"), width=13)
        self.btn_audio.pack(side="left", padx=10)

        self.is_auto = False
        self.completed = False

    def _load_program(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        txt_path = os.path.join(script_dir, "ACPAtext.txt")
        instructions = []
        if os.path.exists(txt_path):
            with open(txt_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    while len(parts) < 4:
                        parts.append("x")
                    instructions.append(Instruction(parts[0], parts[1], parts[2], parts[3]))
        return instructions

    def _init_cpu_state(self):
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
        self.cycle = 0
        self.completed = False

    def reset_pipeline(self):
        self.is_auto = False
        self.btn_auto.config(text="⏩ Auto Run", bg="#2ecc71")
        self._init_cpu_state()
        self._update_ui("Pipeline reset to Cycle 0.")
        self.latency_label.config(text="Memory Access Latency: --")
        self.canvas.coords("chef", 120, 60)
        self.btn_step.config(state="normal")
        self.btn_auto.config(state="normal")

    def toggle_auto_run(self):
        if self.is_auto:
            self.is_auto = False
            self.btn_auto.config(text="⏩ Auto Run", bg="#2ecc71")
        else:
            self.is_auto = True
            self.btn_auto.config(text="⏸ Pause", bg="#f39c12")
            self._auto_step()

    def _auto_step(self):
        if not self.is_auto or self.completed:
            return
        finished = self.step_cycle()
        if not finished and self.is_auto:
            self.root.after(700, self._auto_step)

    def step_cycle(self):
        if self.completed:
            return True

        self.cycle += 1
        cycle_msg = f"Cycle {self.cycle}: "
        latency_str = "--"

        # Check if program has finished (halt arrived at writeback)
        if self.writeback == halt:
            self.completed = True
            self.status_label.config(text="Pipeline Complete: All instructions executed!", fg="#2ecc71")
            self.btn_step.config(state="disabled")
            self.btn_auto.config(state="disabled")
            self.root.after(600, self.on_pipeline_completed)
            return True

        # 1. EX: Execute R-type and B-type
        if self.execute.type in ["add", "sub", "and", "or", "beq"]:
            s1 = getattr(self, self.execute.p2, 0) or 0
            s2 = getattr(self, self.execute.p3, 0) or 0

            if self.execute.type == "add":
                self.execute.result = s1 + s2
            elif self.execute.type == "sub":
                self.execute.result = s1 - s2
            elif self.execute.type == "and":
                self.execute.result = s1 & s2
            elif self.execute.type == "or":
                self.execute.result = s1 | s2
            elif self.execute.type == "beq":
                if s1 - s2 == 0:
                    self.jumper = 1

        # 2. ME: Memory Phase (Cache Level check for 'lw')
        if self.memory.type == "lw":
            try:
                addr = int(self.memory.p2)
                access_delay = cacheLevel[addr]
                val = memory[addr]

                if access_delay == 1:
                    tier_name = "L1 Cache Hit (Prep Counter)"
                    target_x = 120
                elif access_delay == 3:
                    tier_name = "L2 Cache Hit (Kitchen Pantry)"
                    target_x = 370
                else:
                    tier_name = "Main Memory Access (Walk-In Freezer)"
                    target_x = 580

                latency_str = f"{access_delay:.1f}s Latency ({tier_name})"
                cycle_msg += f"ME accessing address {addr} [{tier_name}]. "

                # Move chef sprite towards active storage tier
                self._move_chef_to(target_x)

                if self.memory.p1 == "r1":
                    self.r1 = val
                elif self.memory.p1 == "r2":
                    self.r2 = val
                elif self.memory.p1 == "r3":
                    self.r3 = val
            except (ValueError, IndexError):
                pass
        else:
            self._move_chef_to(120)

        # 3. WB: Writeback
        if self.writeback.type in ["add", "sub", "and", "or"]:
            if self.writeback.p1 in ["r1", "r2", "r3"]:
                setattr(self, self.writeback.p1, self.writeback.result)

        if self.writeback.type == "beq":
            if self.jumper == 1:
                try:
                    self.pc = int(self.writeback.p1) - 1
                except ValueError:
                    pass
            self.jumper = 0

        # Advance Pipeline
        self.writeback = self.memory
        self.memory = self.execute
        self.execute = self.decode
        self.decode = self.fetch

        # Fetch next instruction
        if self.pc < len(self.program):
            self.fetch = self.program[self.pc]
            self.pc += 1
            cycle_msg += f"IF fetched '{self.fetch}'."
        else:
            self.fetch = halt
            cycle_msg += "No more instructions; fetched 'halt'."

        # Update UI
        self._update_ui(cycle_msg)
        self.latency_label.config(text=f"Memory Latency: {latency_str}")

        # Check for immediate halt condition after advance
        if self.writeback == halt and self.memory == halt and self.execute == halt:
            self.completed = True
            self.status_label.config(text="Pipeline Complete: Program halted.", fg="#2ecc71")
            self.btn_step.config(state="disabled")
            self.btn_auto.config(state="disabled")
            self.root.after(600, self.on_pipeline_completed)
            return True

        return False

    def _move_chef_to(self, target_x):
        cur_coords = self.canvas.coords("chef")
        if cur_coords:
            cur_x = cur_coords[0]
            dx = (target_x - cur_x) / 10
            for _ in range(10):
                self.canvas.move("chef", dx, 0)
                self.root.update()
                time.sleep(0.015)

    def _update_ui(self, msg):
        self.cycle_label.config(text=f"Cycle: {self.cycle} | PC: {self.pc}")
        self.status_label.config(text=msg)

        # Update stage labels
        stages_map = {
            "fetch": self.fetch,
            "decode": self.decode,
            "execute": self.execute,
            "memory": self.memory,
            "writeback": self.writeback,
        }

        for attr, inst in stages_map.items():
            lbl = self.stage_widgets[attr]
            lbl.config(text=str(inst))
            if inst == nop:
                lbl.config(fg="#7f8c8d")
            elif inst == halt:
                lbl.config(fg="#e74c3c")
            else:
                lbl.config(fg="#f1c40f")

        # Update register labels
        self.pc_lbl.config(text=f"PC: {self.pc}")
        self.r1_lbl.config(text=f"r1: {self.r1 if self.r1 is not None else '--'}")
        self.r2_lbl.config(text=f"r2: {self.r2 if self.r2 is not None else '--'}")
        self.r3_lbl.config(text=f"r3: {self.r3 if self.r3 is not None else '--'}")

    def show_instructions(self):
        """Displays interactive mission instructions in a dialog."""
        msg = (
            "🎯 PART 2 MISSION OBJECTIVE:\n"
            "Observe how a 5-stage CPU pipeline executes instructions from 'ACPAtext.txt' and manages multi-tier memory latency!\n\n"
            "⚙️ THE 5 PIPELINE STAGES:\n"
            "• IF (Fetch)     : Retrieves next instruction from program memory.\n"
            "• DE (Decode)    : Decodes instruction opcode & register operands.\n"
            "• EX (Execute)   : ALU performs arithmetic or evaluates branches.\n"
            "• ME (Memory)    : Accesses storage hierarchy (Prep Counter, Pantry, Freezer).\n"
            "• WB (Writeback) : Writes results into destination registers.\n\n"
            "⏱️ STORAGE TIER LATENCIES:\n"
            "• Prep Counter (L1 Cache) = 1.0s delay (Fast hit)\n"
            "• Kitchen Pantry (L2 Cache) = 3.0s delay (Medium hit)\n"
            "• Walk-In Freezer (Main DRAM) = 5.0s delay (Slow miss)\n\n"
            "🎮 CONTROLS:\n"
            "• '▶ Step Next Cycle': Advance 1 clock cycle to inspect stages & registers.\n"
            "• '⏩ Auto Run': Automatically step through all cycles until program halts.\n"
            "• Completing the program automatically starts Part 3 (Rowhammer Level)!"
        )
        messagebox.showinfo("Part 2 - Mission Briefing & Instructions", msg)

    def toggle_music(self):
        if self.music_on:
            stop_bgm()
            self.music_on = False
            self.btn_audio.config(text="🔇 Music: OFF", bg="#7f8c8d")
        else:
            if os.path.exists(self.music_path):
                start_bgm(self.music_path)
                self.music_on = True
                self.btn_audio.config(text="🔊 Music: ON", bg="#2980b9")

    def _on_close(self):
        stop_bgm()
        self.root.destroy()

    def on_pipeline_completed(self):
        stop_bgm()
        messagebox.showinfo(
            "Part 2 Cleared!",
            "Challenge Cleared!\n\nAll CPU pipeline stages have executed successfully.\n\nClick OK to advance to Part 3 (Rowhammer Attack)!"
        )
        self.root.destroy()
        self.launch_part_3()

    def launch_part_3(self):
        stop_bgm()
        part3_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Part 3"))
        part3_script = os.path.join(part3_dir, "kitchen_espionage_part3.py")
        if not os.path.exists(part3_script):
            part3_script = os.path.join(part3_dir, "kitchen_espionage_level3.py")
        if os.path.exists(part3_script):
            subprocess.run([sys.executable, part3_script], cwd=part3_dir)
        else:
            messagebox.showerror("Error", f"Could not find Part 3 script at:\n{part3_script}")


if __name__ == "__main__":
    root = tk.Tk()
    app = KitchenPipelineGUI(root)
    root.mainloop()
