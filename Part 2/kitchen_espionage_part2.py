import tkinter as tk
from tkinter import messagebox
import time
import os
import sys
import subprocess
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

memory = [0] * 20
memory[5] = 12
memory[16] = 25
memory[17] = 40

ones = [1, 5, 8, 12]
threes = [3, 7, 10, 16]
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
        self.root.title("Kitchen Espionage - Part 2 (5-Stage RISC Pipeline & Memory Latency)")
        self.root.configure(bg="#070b14")

        # Fullscreen on launch
        self.is_fullscreen = False
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1400x900")
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

        # Load program instructions
        self.program = self._load_program()
        self._init_cpu_state()

        # Dynamic Canvas Dimensions
        self.canvas_width = 1200
        self.canvas_height = 420
        self.active_storage_tier = None
        self.token_norm_x = 0.10
        self.token_norm_y = 0.22

        # --- 1. FULL-WIDTH RESPONSIVE VECTOR CANVAS ---
        self.canvas = tk.Canvas(root, bg="#070b14", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=(10, 4))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # Audio Setup
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.music_on = True
        self.music_path = os.path.join(script_dir, "restaurant_music.mp3")
        if os.path.exists(self.music_path):
            start_bgm(self.music_path)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- 2. STATUS HUD ---
        hud_frame = tk.Frame(root, bg="#070b14")
        hud_frame.pack(fill="x", padx=20, pady=2)

        self.cycle_label = tk.Label(hud_frame, text="Cycle: 0 | CPU Initialized", bg="#070b14", fg="#facc15", font=("Consolas", 12, "bold"))
        self.cycle_label.pack(side="left")

        self.latency_label = tk.Label(hud_frame, text="Memory Latency: --", bg="#070b14", fg="#38bdf8", font=("Consolas", 12, "bold"))
        self.latency_label.pack(side="right")

        self.status_label = tk.Label(root, text="Pipeline ready. Click 'Step Next Cycle' or 'Auto Run' to observe instruction execution.", bg="#070b14", fg="#cbd5e1", font=("Arial", 11))
        self.status_label.pack(pady=2)

        # --- 3. PIPELINE STAGES HUD BOXES ---
        pipe_outer = tk.Frame(root, bg="#0f172a", bd=1, relief="solid", padx=12, pady=6)
        pipe_outer.pack(fill="x", padx=16, pady=4)

        stages = [
            ("IF", "Instruction Fetch", "fetch", "#0284c7"),
            ("DE", "Decode & Regs", "decode", "#d97706"),
            ("EX", "Execute ALU", "execute", "#9333ea"),
            ("ME", "Memory Access", "memory", "#16a34a"),
            ("WB", "Write Back", "writeback", "#ca8a04"),
        ]

        self.stage_widgets = {}
        self.stage_boxes = {}
        for idx, (abbr, name, attr, col) in enumerate(stages):
            box = tk.Frame(pipe_outer, bg="#111c33", bd=1, relief="solid")
            box.grid(row=0, column=idx, padx=4, pady=2, sticky="nsew")
            pipe_outer.grid_columnconfigure(idx, weight=1)

            title_lbl = tk.Label(box, text=abbr, bg=col, fg="white", font=("Consolas", 9, "bold"))
            title_lbl.pack(fill="x")

            sub_lbl = tk.Label(box, text=name, bg="#111c33", fg="#64748b", font=("Arial", 7))
            sub_lbl.pack()

            inst_lbl = tk.Label(box, text="nop", bg="#111c33", fg="#94a3b8", font=("Consolas", 10, "bold"))
            inst_lbl.pack(pady=2)

            self.stage_widgets[attr] = inst_lbl
            self.stage_boxes[attr] = (box, title_lbl)

        # --- 4. CONTROLS & ARCHITECTURE REGISTERS ---
        ctrl_frame = tk.Frame(root, bg="#070b14")
        ctrl_frame.pack(fill="x", padx=16, pady=(4, 10))

        # Register File Readout
        reg_frame = tk.Frame(ctrl_frame, bg="#0f172a", bd=1, relief="solid", padx=10, pady=4)
        reg_frame.pack(side="left")

        tk.Label(reg_frame, text="REGISTERS:", bg="#0f172a", fg="#38bdf8", font=("Consolas", 9, "bold")).pack(side="left", padx=4)
        self.pc_lbl = tk.Label(reg_frame, text="PC: 0", bg="#0f172a", fg="#facc15", font=("Consolas", 10, "bold"))
        self.pc_lbl.pack(side="left", padx=6)
        self.r1_lbl = tk.Label(reg_frame, text="r1: --", bg="#0f172a", fg="white", font=("Consolas", 10))
        self.r1_lbl.pack(side="left", padx=6)
        self.r2_lbl = tk.Label(reg_frame, text="r2: --", bg="#0f172a", fg="white", font=("Consolas", 10))
        self.r2_lbl.pack(side="left", padx=6)
        self.r3_lbl = tk.Label(reg_frame, text="r3: --", bg="#0f172a", fg="white", font=("Consolas", 10))
        self.r3_lbl.pack(side="left", padx=6)

        # Buttons
        btn_box = tk.Frame(ctrl_frame, bg="#070b14")
        btn_box.pack(side="right")

        self.btn_step = tk.Button(btn_box, text="⏩ Step Next Cycle", command=self.step_cycle, bg="#0284c7", fg="white", font=("Arial", 10, "bold"), padx=10)
        self.btn_step.pack(side="left", padx=4)

        self.btn_auto = tk.Button(btn_box, text="▶ Auto Run", command=self.toggle_auto_run, bg="#22c55e", fg="#070b14", font=("Arial", 10, "bold"), padx=10)
        self.btn_auto.pack(side="left", padx=4)

        self.btn_reset = tk.Button(btn_box, text="🔄 Reset", command=self.reset_pipeline, bg="#475569", fg="white", font=("Arial", 9, "bold"), padx=8)
        self.btn_reset.pack(side="left", padx=4)

        self.btn_audio = tk.Button(btn_box, text="🔊 Music", command=self.toggle_music, bg="#1e293b", fg="white", font=("Arial", 9, "bold"), padx=8)
        self.btn_audio.pack(side="left", padx=4)

        self.btn_help = tk.Button(btn_box, text="📋 Briefing", command=self.show_instructions, bg="#0f766e", fg="white", font=("Arial", 9, "bold"), padx=8)
        self.btn_help.pack(side="left", padx=4)

        self.btn_tech = tk.Button(btn_box, text="🔬 Section B", command=self.show_tech_details, bg="#9333ea", fg="white", font=("Arial", 9, "bold"), padx=8)
        self.btn_tech.pack(side="left", padx=4)

    def _toggle_fullscreen(self, event=None):
        self.is_fullscreen = not self.is_fullscreen
        self.root.attributes('-fullscreen', self.is_fullscreen)
        if not self.is_fullscreen:
            self.root.state('zoomed')

    def _exit_fullscreen(self, event=None):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.root.attributes('-fullscreen', False)
            self.root.state('zoomed')

    def _on_canvas_resize(self, event):
        if event.width > 200 and event.height > 150:
            self.canvas_width = event.width
            self.canvas_height = event.height
            self._redraw_pipeline_canvas()

    def _load_program(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        prog_path = os.path.join(script_dir, "ACPAtext.txt")
        instructions = []
        if os.path.exists(prog_path):
            with open(prog_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if not parts or parts[0].startswith("#"):
                        continue
                    while len(parts) < 4:
                        parts.append("x")
                    instructions.append(Instruction(parts[0], parts[1], parts[2], parts[3]))
        else:
            instructions = [
                Instruction("lw", "r1", "5", "x"),
                Instruction("lw", "r2", "16", "x"),
                Instruction("lw", "r3", "17", "x"),
                Instruction("add", "r3", "r1", "r2"),
                halt
            ]
        instructions.append(halt)
        return instructions

    def _init_cpu_state(self):
        self.cycle = 0
        self.pc = 0
        self.r1 = None
        self.r2 = None
        self.r3 = None
        self.fetch = nop
        self.decode = nop
        self.execute = nop
        self.memory = nop
        self.writeback = nop
        self.jumper = 0
        self.completed = False
        self.is_auto = False

    def reset_pipeline(self):
        self.is_auto = False
        self._init_cpu_state()
        self.active_storage_tier = None
        self.token_norm_x = 0.10
        self.token_norm_y = 0.22
        self.cycle_label.config(text="Cycle: 0 | CPU Initialized")
        self.status_label.config(text="Pipeline reset. Ready to run.", fg="#cbd5e1")
        self.latency_label.config(text="Memory Latency: --")
        self.btn_auto.config(text="▶ Auto Run", bg="#22c55e")
        self.btn_step.config(state="normal")
        self.btn_auto.config(state="normal")
        self._update_hud_labels()
        self._redraw_pipeline_canvas()

    # --- PROCEDURAL VECTOR 5-STAGE RISC PIPELINE RENDERER ---

    def _redraw_pipeline_canvas(self):
        self.canvas.delete("all")
        W = self.canvas_width
        H = self.canvas_height

        # 1. Silicon Wafer Background Grid
        grid_step = 40
        for x in range(0, W, grid_step):
            self.canvas.create_line(x, 0, x, H, fill="#0d1527", width=1)
        for y in range(0, H, grid_step):
            self.canvas.create_line(0, y, W, y, fill="#0d1527", width=1)

        # 2. Main Datapath Dimensions (Top 55% of canvas)
        top_y = 40
        stage_h = max(110, int(H * 0.44))
        stage_w = max(120, int((W - 80) / 5))

        # Top Writeback Loop Feedback Bus (WB -> DE)
        wb_center_x = 40 + 4 * stage_w + stage_w // 2
        de_center_x = 40 + 1 * stage_w + stage_w // 2
        self.canvas.create_line(wb_center_x, top_y, wb_center_x, top_y - 20, de_center_x, top_y - 20, de_center_x, top_y, fill="#facc15", width=2, dash=(6, 4))
        self.canvas.create_text((wb_center_x + de_center_x) // 2, top_y - 28, text="WRITEBACK FEEDBACK BUS: RegWrite (WB -> DE)", fill="#facc15", font=("Consolas", 8, "bold"))

        # Main Pipeline Interstage Wire
        wire_y = top_y + stage_h // 2
        self.canvas.create_line(40, wire_y, W - 40, wire_y, fill="#38bdf8", width=3)

        # 5 Stage Configurations
        stage_defs = [
            ("IF", "Fetch", str(self.fetch), f"PC: {self.pc}", "#0284c7"),
            ("DE", "Decode", str(self.decode), f"r1:{self.r1 or '--'} r2:{self.r2 or '--'}", "#d97706"),
            ("EX", "Execute ALU", str(self.execute), "ALU \\___/", "#9333ea"),
            ("ME", "Memory", str(self.memory), "L1/L2/DRAM Router", "#16a34a"),
            ("WB", "Writeback", str(self.writeback), f"Commit: r3={self.r3 or '--'}", "#ca8a04"),
        ]

        # Draw Stages and Latches
        for idx, (abbr, name, inst, sub, col) in enumerate(stage_defs):
            sx = 40 + idx * stage_w
            sw = stage_w - 20
            is_active = (inst not in ["nop", "halt", "x"])
            border_col = col if is_active else "#334155"

            # Stage Box
            self.canvas.create_rectangle(sx, top_y, sx + sw, top_y + stage_h, fill="#090e1a", outline=border_col, width=2 if is_active else 1)
            # Header
            self.canvas.create_rectangle(sx, top_y, sx + sw, top_y + 26, fill=col if is_active else "#1e293b", outline="")
            self.canvas.create_text(sx + sw // 2, top_y + 13, text=f"{abbr} ({name})", fill="white", font=("Consolas", 9, "bold"))

            # Active Instruction Tag
            inst_col = "#facc15" if is_active else "#64748b"
            self.canvas.create_text(sx + sw // 2, top_y + 50, text=inst, fill=inst_col, font=("Consolas", 11, "bold"))
            self.canvas.create_text(sx + sw // 2, top_y + 75, text=sub, fill="#94a3b8", font=("Consolas", 8))

            # EX Stage: Render Vector ALU Wedge Symbol (\___/)
            if abbr == "EX":
                alu_cx = sx + sw // 2
                alu_cy = top_y + stage_h - 22
                self.canvas.create_polygon(
                    alu_cx - 38, alu_cy - 14,
                    alu_cx + 38, alu_cy - 14,
                    alu_cx + 25, alu_cy + 14,
                    alu_cx - 25, alu_cy + 14,
                    fill="#581c87" if is_active else "#1e293b",
                    outline="#c084fc" if is_active else "#475569",
                    width=1.5
                )
                self.canvas.create_text(alu_cx, alu_cy, text="ALU", fill="white", font=("Consolas", 8, "bold"))

            # Interstage Pipeline Latches between stages
            if idx < 4:
                lx = sx + sw + 4
                self.canvas.create_rectangle(lx, top_y + 10, lx + 12, top_y + stage_h - 10, fill="#1e293b", outline="#475569")
                latch_names = ["IF/ID", "ID/EX", "EX/ME", "ME/WB"]
                self.canvas.create_text(lx + 6, top_y + stage_h // 2, text=latch_names[idx].replace("/", "\n"), fill="#94a3b8", font=("Consolas", 6, "bold"), justify="center")

        # 3. Storage Hierarchy Interconnect (Bottom 40% of canvas)
        mem_stage_cx = 40 + 3 * stage_w + (stage_w - 20) // 2
        bottom_y0 = top_y + stage_h + 16
        tier_h = max(70, H - bottom_y0 - 20)
        tier_w = max(180, int((W - 80) / 3))

        # Drop lines from ME stage down to storage hierarchy router
        self.canvas.create_line(mem_stage_cx, top_y + stage_h, mem_stage_cx, bottom_y0 - 4, fill="#16a34a", width=2)
        router_x1 = 40 + tier_w // 2
        router_x2 = W - 40 - tier_w // 2
        self.canvas.create_line(router_x1, bottom_y0 - 4, router_x2, bottom_y0 - 4, fill="#16a34a", width=2)

        tiers = [
            ("L1 DATA CACHE (Prep Counter)", "1.0s Latency (1 Cycle)", "#22c55e", 1, "ON-CHIP SRAM (FAST HIT)"),
            ("L2 UNIFIED CACHE (Spice Pantry)", "3.0s Latency (3 Cycles)", "#f59e0b", 3, "MID-LEVEL CACHE HIT"),
            ("MAIN DRAM MEMORY (Walk-In Freezer)", "5.0s Latency (5 Cycles - STALL)", "#ef4444", 5, "OFF-CHIP MEMORY WALL")
        ]

        for tidx, (title, delay, col, t_id, desc) in enumerate(tiers):
            tx = 40 + tidx * tier_w
            tw = tier_w - 20
            is_tier_active = (self.active_storage_tier == t_id)
            outline_col = col if is_tier_active else "#334155"

            # Drop line to tier
            tier_cx = tx + tw // 2
            self.canvas.create_line(tier_cx, bottom_y0 - 4, tier_cx, bottom_y0, fill=col if is_tier_active else "#334155", width=2 if is_tier_active else 1)

            # Tier Box
            self.canvas.create_rectangle(tx, bottom_y0, tx + tw, bottom_y0 + tier_h, fill="#090e1a", outline=outline_col, width=2 if is_tier_active else 1)
            # Header
            self.canvas.create_rectangle(tx, bottom_y0, tx + tw, bottom_y0 + 22, fill=col if is_tier_active else "#111c33", outline="")
            self.canvas.create_text(tier_cx, bottom_y0 + 11, text=title, fill="white" if is_tier_active else "#cbd5e1", font=("Consolas", 8, "bold"))

            # Delay badge & description
            self.canvas.create_text(tier_cx, bottom_y0 + 38, text=delay, fill=col, font=("Consolas", 10, "bold"))
            self.canvas.create_text(tier_cx, bottom_y0 + 56, text=desc, fill="#94a3b8", font=("Consolas", 8))

        # 4. Hardware Execution Token (Vector Diamond Core Token)
        tok_x = int(W * self.token_norm_x)
        tok_y = int(H * self.token_norm_y)
        self._draw_thread_token(tok_x, tok_y)

    def _draw_thread_token(self, cx, cy):
        r = 14
        self.canvas.create_polygon(cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill="#0284c7", outline="#38bdf8", width=2, tags="token")
        ir = 7
        self.canvas.create_polygon(cx, cy - ir, cx + ir, cy, cx, cy + ir, cx - ir, cy, fill="#ffffff", outline="", tags="token")

    # --- PIPELINE STEP & SIMULATION METHODS ---

    def toggle_auto_run(self):
        if self.is_auto:
            self.is_auto = False
            self.btn_auto.config(text="▶ Auto Run", bg="#22c55e")
        else:
            self.is_auto = True
            self.btn_auto.config(text="⏸ Pause", bg="#f59e0b")
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

        # Check halt at writeback
        if self.writeback == halt:
            self.completed = True
            self.status_label.config(text="Pipeline Complete: All instructions executed!", fg="#22c55e")
            self.btn_step.config(state="disabled")
            self.btn_auto.config(state="disabled")
            self.root.after(600, self.on_pipeline_completed)
            return True

        # 1. EX Phase: ALU Operations
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

        # 2. ME Phase: Storage Hierarchy Access
        if self.memory.type == "lw":
            try:
                addr = int(self.memory.p2)
                access_delay = cacheLevel[addr]
                val = memory[addr]
                self.active_storage_tier = access_delay

                if access_delay == 1:
                    tier_name = "L1 Data Cache (1.0s Hit)"
                    self.token_norm_x = 0.16
                    self.token_norm_y = 0.80
                elif access_delay == 3:
                    tier_name = "L2 Unified Cache (3.0s Access)"
                    self.token_norm_x = 0.50
                    self.token_norm_y = 0.80
                else:
                    tier_name = "Main DRAM Memory (5.0s STALL)"
                    self.token_norm_x = 0.84
                    self.token_norm_y = 0.80

                latency_str = f"{access_delay:.1f}s ({tier_name})"
                cycle_msg += f"ME accessing addr {addr} [{tier_name}]. "

                if self.memory.p1 == "r1":
                    self.r1 = val
                elif self.memory.p1 == "r2":
                    self.r2 = val
                elif self.memory.p1 == "r3":
                    self.r3 = val
            except (ValueError, IndexError):
                pass
        else:
            self.active_storage_tier = None
            self.token_norm_x = 0.10 + 0.18 * 2  # At ALU stage
            self.token_norm_y = 0.22

        # 3. WB Phase: Commit to Register
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

        # Advance Pipeline Stages
        self.writeback = self.memory
        self.memory = self.execute
        self.execute = self.decode
        self.decode = self.fetch

        if self.pc < len(self.program):
            self.fetch = self.program[self.pc]
            self.pc += 1
            cycle_msg += f"IF fetched '{self.fetch}'."
        else:
            self.fetch = halt
            cycle_msg += "Program ended; fetched 'halt'."

        # Update UI & HUD
        self._update_hud_labels(cycle_msg, latency_str)
        self._redraw_pipeline_canvas()

        # Check immediate halt condition
        if self.writeback == halt and self.memory == halt and self.execute == halt:
            self.completed = True
            self.status_label.config(text="Pipeline Complete: Program halted.", fg="#22c55e")
            self.btn_step.config(state="disabled")
            self.btn_auto.config(state="disabled")
            self.root.after(600, self.on_pipeline_completed)
            return True

        return False

    def _update_hud_labels(self, msg="", latency="--"):
        self.cycle_label.config(text=f"Cycle: {self.cycle} | PC: {self.pc}")
        if msg:
            self.status_label.config(text=msg)
        self.latency_label.config(text=f"Memory Latency: {latency}")

        # Update registers
        self.pc_lbl.config(text=f"PC: {self.pc}")
        self.r1_lbl.config(text=f"r1: {self.r1 if self.r1 is not None else '--'}")
        self.r2_lbl.config(text=f"r2: {self.r2 if self.r2 is not None else '--'}")
        self.r3_lbl.config(text=f"r3: {self.r3 if self.r3 is not None else '--'}")

        # Update stage HUD widgets
        stages_map = {
            "fetch": self.fetch,
            "decode": self.decode,
            "execute": self.execute,
            "memory": self.memory,
            "writeback": self.writeback,
        }
        stage_colors = {
            "fetch": "#0284c7",
            "decode": "#d97706",
            "execute": "#9333ea",
            "memory": "#16a34a",
            "writeback": "#ca8a04",
        }

        for attr, inst in stages_map.items():
            lbl = self.stage_widgets[attr]
            box, title_lbl = self.stage_boxes[attr]
            lbl.config(text=str(inst))
            if inst == nop:
                lbl.config(fg="#64748b")
                title_lbl.config(bg="#334155")
            elif inst == halt:
                lbl.config(fg="#ef4444")
                title_lbl.config(bg="#991b1b")
            else:
                lbl.config(fg="#facc15")
                title_lbl.config(bg=stage_colors.get(attr, "#0284c7"))

    def show_instructions(self):
        msg = (
            "🎯 PART 2 MISSION OBJECTIVE:\n"
            "Observe how a 5-stage RISC CPU pipeline executes instructions from 'ACPAtext.txt' and handles multi-tier memory latency!\n\n"
            "⚙️ THE 5 PIPELINE STAGES:\n"
            "• IF (Fetch)     : Retrieves next instruction from program memory using PC.\n"
            "• DE (Decode)    : Decodes opcode and reads operand registers from Register File.\n"
            "• EX (Execute)   : ALU performs arithmetic wedge operations or evaluates branch conditions.\n"
            "• ME (Memory)    : Accesses storage hierarchy: L1 Cache (1s), L2 (3s), or DRAM (5s).\n"
            "• WB (Writeback) : Commits ALU results or loaded memory data to destination registers.\n\n"
            "⚠️ THE MEMORY WALL:\n"
            "Notice how DRAM access (5.0s) stalls subsequent pipeline stages! At completion, you must solve a critical-thinking challenge to unlock Part 3."
        )
        messagebox.showinfo("Part 2 - Mission Briefing", msg)

    def show_tech_details(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🔬 Section B: CPU Pipeline & Memory Wall Deep Dive")
        dialog.geometry("800x600")
        dialog.configure(bg="#070b14")
        dialog.transient(self.root)

        header = tk.Frame(dialog, bg="#0f172a", pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🔬 SECTION B: PIPELINE ARCHITECTURE & MEMORY HIERARCHY", bg="#0f172a", fg="#facc15", font=("Consolas", 12, "bold")).pack()
        tk.Label(header, text="Hardware Datapath, Latency Hazards, and the Memory Wall", bg="#0f172a", fg="#cbd5e1", font=("Arial", 9)).pack()

        text_box = tk.Text(dialog, bg="#0f172a", fg="#ecf0f1", font=("Consolas", 10), padx=16, pady=16, wrap="word", relief="flat")
        text_box.pack(fill="both", expand=True, padx=20, pady=12)

        tech_doc = (
            "========================================================================\n"
            " 1. THE 5-STAGE CLASSIC RISC DATAPATH\n"
            "========================================================================\n"
            "Modern microprocessors split instruction execution into discrete pipeline\n"
            "stages separated by interstage register latches (IF/ID, ID/EX, EX/MEM, MEM/WB):\n\n"
            "  [IF]  Instruction Fetch : Program Counter (PC) addresses the Instruction Cache (I-Cache).\n"
            "  [DE]  Instruction Decode: Control Unit decodes opcode; reads dual register ports (rs, rt).\n"
            "  [EX]  Execution (ALU)   : ALU wedge calculates arithmetic/logic or branch target addresses.\n"
            "  [ME]  Memory Access     : Data Cache (D-Cache) read/write for load ('lw') and store ('sw').\n"
            "  [WB]  Writeback         : MUX routes memory data or ALU result back to destination register (rd).\n\n"
            "========================================================================\n"
            " 2. MEMORY HIERARCHY LATENCIES & THE MEMORY WALL\n"
            "========================================================================\n"
            "While CPU logic (ALU) operates at gigahertz clock speeds (~0.25 nanoseconds/cycle),\n"
            "off-chip DRAM access takes tens or hundreds of nanoseconds:\n\n"
            "  • L1 Data Cache   : ~1 - 4 clock cycles    (On-chip SRAM, 32KB)\n"
            "  • L2 Unified Cache: ~10 - 20 clock cycles  (On-chip SRAM, 512KB)\n"
            "  • Off-Chip DRAM   : ~200 - 300+ cycles     (Off-chip DDR4/DDR5 DIMM)\n\n"
            "The enormous performance gap between CPU speed and DRAM access latency is called\n"
            "THE MEMORY WALL. When an instruction misses L1 and L2, the entire pipeline must\n"
            "stall (insert pipeline bubbles), wasting valuable compute cycles!\n"
        )
        text_box.insert("1.0", tech_doc)
        text_box.config(state="disabled")

        tk.Button(dialog, text="Close Deep Dive", command=dialog.destroy, bg="#1e293b", fg="white", font=("Arial", 10)).pack(pady=(0, 10))

    def show_interactive_challenge(self):
        """Mandatory checkpoint: student must calculate multi-tier memory latency and bottleneck."""
        dialog = tk.Toplevel(self.root)
        dialog.title("🎓 Section B Checkpoint: Architectural Latency Analysis")
        dialog.geometry("740x560")
        dialog.configure(bg="#070b14")
        dialog.transient(self.root)
        dialog.grab_set()

        header = tk.Frame(dialog, bg="#0f172a", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="🎓 SECTION B MANDATORY CHECKPOINT: ARCHITECTURAL LATENCY ANALYSIS", bg="#0f172a", fg="#facc15", font=("Consolas", 11, "bold")).pack()
        tk.Label(header, text="To unlock Part 3, calculate program execution delays and identify the microarchitectural bottleneck.", bg="#0f172a", fg="#cbd5e1", font=("Arial", 9)).pack()

        content = tk.Frame(dialog, bg="#070b14", padx=20, pady=10)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Question 1 (Calculation):", bg="#070b14", fg="#38bdf8", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(5, 2))
        q1_text = (
            "During this program run, the CPU executed three distinct 'lw' (load word) instructions:\n"
            "  • lw r1, 5   (Accessing L1 Data Cache : 1.0s delay)\n"
            "  • lw r2, 16  (Accessing L2 Unified Cache : 3.0s delay)\n"
            "  • lw r3, 17  (Accessing Main Memory DRAM : 5.0s delay)\n\n"
            "What was the total cumulative memory access time (in seconds) spent waiting on storage across these 3 instructions?"
        )
        tk.Label(content, text=q1_text, bg="#070b14", fg="#cbd5e1", font=("Consolas", 9), justify="left").pack(anchor="w")

        q1_frame = tk.Frame(content, bg="#070b14")
        q1_frame.pack(anchor="w", pady=(6, 12))
        tk.Label(q1_frame, text="Your Answer (seconds):", bg="#070b14", fg="white", font=("Consolas", 10, "bold")).pack(side="left")
        latency_entry = tk.Entry(q1_frame, width=8, font=("Consolas", 11, "bold"))
        latency_entry.pack(side="left", padx=8)

        tk.Label(content, text="Question 2 (Critical Thinking):", bg="#070b14", fg="#38bdf8", font=("Consolas", 11, "bold")).pack(anchor="w", pady=(8, 2))
        q2_text = (
            "Why did the 'add r3, r1, r2' instruction execute almost instantaneously compared to the 'lw' instructions?\n"
            "Select the correct architectural explanation:"
        )
        tk.Label(content, text=q2_text, bg="#070b14", fg="#cbd5e1", font=("Consolas", 9), justify="left").pack(anchor="w")

        q2_var = tk.StringVar(value="")
        opts = [
            ("A", "A) The ALU operates purely on on-chip register file data, avoiding off-chip memory bus traversal delays (The Memory Wall)."),
            ("B", "B) The ALU bypasses the CPU clock and runs without executing cycles."),
            ("C", "C) The 'add' instruction skips the Writeback (WB) phase entirely.")
        ]
        for opt_key, opt_label in opts:
            r = tk.Radiobutton(content, text=opt_label, value=opt_key, variable=q2_var, bg="#070b14", fg="#cbd5e1", selectcolor="#1e293b", activebackground="#070b14", activeforeground="white", font=("Arial", 9), wraplength=680, justify="left")
            r.pack(anchor="w", pady=2)

        def verify_answers():
            ans1 = latency_entry.get().strip()
            ans2 = q2_var.get().strip()

            try:
                val1 = float(ans1)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for Question 1.", parent=dialog)
                return

            if abs(val1 - 9.0) > 0.05:
                messagebox.showerror("Question 1 Incorrect", f"Incorrect latency ({ans1}s).\nHint: Sum the three tier latencies: 1.0s + 3.0s + 5.0s.", parent=dialog)
                return

            if ans2 != "A":
                messagebox.showerror("Question 2 Incorrect", "Incorrect choice for Question 2.\nHint: Consider the speed difference between on-chip ALU execution and off-chip DRAM access (the Memory Wall).", parent=dialog)
                return

            messagebox.showinfo("Mastery Verified!", "🎉 Outstanding Work!\n\nYou correctly calculated the 9.0s multi-tier memory latency and identified the Memory Wall bottleneck.\n\nAdvancing to Part 3 (Double-Sided Rowhammer Attack)!", parent=dialog)
            dialog.destroy()
            self.root.destroy()
            self.launch_part_3()

        btn_submit = tk.Button(dialog, text="✔ Verify Answers & Unlock Part 3", command=verify_answers, bg="#22c55e", fg="#070b14", font=("Arial", 11, "bold"), pady=6)
        btn_submit.pack(pady=10)

    def toggle_music(self):
        if self.music_on:
            stop_bgm()
            self.music_on = False
            self.btn_audio.config(text="🔇 Music: OFF", bg="#334155")
        else:
            if os.path.exists(self.music_path):
                start_bgm(self.music_path)
                self.music_on = True
                self.btn_audio.config(text="🔊 Music: ON", bg="#1e293b")

    def _on_close(self):
        stop_bgm()
        self.root.destroy()

    def on_pipeline_completed(self):
        stop_bgm()
        self.show_interactive_challenge()

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
