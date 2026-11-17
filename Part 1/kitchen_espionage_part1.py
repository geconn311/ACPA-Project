import tkinter as tk
from tkinter import messagebox
import random
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

class InteractiveKitchen:
    def __init__(self, root):
        self.root = root
        self.root.title("Kitchen Espionage - Flush+Reload Attack (Silicon Hardware Model)")
        self.root.configure(bg="#070b14")

        # Fullscreen on launch
        self.is_fullscreen = False
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1400x900")
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

        # Core Game State (20 physical addresses 0-19, 6 VIP secrets)
        self.all_ingredients = list(range(20))
        self.secret_ingredients = random.sample(self.all_ingredients, 6)
        self.prep_counter = random.sample(self.all_ingredients, 6)
        self.max_probes = 18
        self.probes_remaining = 18
        self.last_probe_info = {"addr": None, "hit": None, "cycles": None}

        # Dynamic Canvas Dimensions
        self.canvas_width = 1200
        self.canvas_height = 420
        self.token_norm_x = 0.16  # Normalized X of execution core token
        self.token_norm_y = 0.50

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

        self.budget_label = tk.Label(hud_frame, text="Probe Budget Remaining: 18 / 18", bg="#070b14", fg="#22c55e", font=("Consolas", 12, "bold"))
        self.budget_label.pack(side="left")

        self.timer_label = tk.Label(hud_frame, text="Hardware RDTSC Latency: -- cycles", bg="#070b14", fg="#38bdf8", font=("Consolas", 12, "bold"))
        self.timer_label.pack(side="right")

        self.status_label = tk.Label(root, text="System Ready. Flush cache (clflush) and trigger victim order to begin attack.", bg="#070b14", fg="#facc15", font=("Arial", 11, "bold"))
        self.status_label.pack(pady=2)

        # --- 3. ATTACKER CONTROL PANEL ---
        control_frame = tk.Frame(root, bg="#0f172a", bd=1, relief="solid", padx=16, pady=8)
        control_frame.pack(fill="x", padx=16, pady=6)

        header_frame = tk.Frame(control_frame, bg="#0f172a")
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 6), sticky="ew")
        tk.Label(header_frame, text="⚡ HARDWARE ATTACK CONTROL CONSOLE", bg="#0f172a", fg="#38bdf8", font=("Consolas", 11, "bold")).pack(side="left")

        self.btn_audio = tk.Button(header_frame, text="🔊 Music: ON", command=self.toggle_music, bg="#1e293b", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_audio.pack(side="right", padx=(4, 0))
        self.btn_help = tk.Button(header_frame, text="📋 Briefing", command=self.show_instructions, bg="#0284c7", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_help.pack(side="right", padx=(4, 0))
        self.btn_tech = tk.Button(header_frame, text="🔬 Section B: Tech Deep Dive", command=self.show_tech_details, bg="#9333ea", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_tech.pack(side="right", padx=(4, 0))

        # Phase 1: Flush
        self.btn_flush = tk.Button(control_frame, text="1. Flush Cache (clflush)", command=self.flush_cache, bg="#d97706", fg="white", font=("Arial", 10, "bold"), width=28)
        self.btn_flush.grid(row=1, column=0, pady=3, padx=5, sticky="w")
        tk.Label(control_frame, text="Evicts all 64-byte lines from L1 SRAM to DRAM [V=0].", bg="#0f172a", fg="#94a3b8", font=("Consolas", 9)).grid(row=1, column=1, sticky="w")

        # Phase 2: Victim Execution
        self.btn_victim = tk.Button(control_frame, text="2. Trigger Victim (Load VIP Secret)", command=self.trigger_victim, bg="#7c3aed", fg="white", font=("Arial", 10, "bold"), width=28)
        self.btn_victim.grid(row=2, column=0, pady=3, padx=5, sticky="w")
        tk.Label(control_frame, text="Victim loads 6 secret VIP memory addresses into L1 Data Cache [V=1].", bg="#0f172a", fg="#94a3b8", font=("Consolas", 9)).grid(row=2, column=1, sticky="w")

        # Phase 3: Probe/Reload
        probe_frame = tk.Frame(control_frame, bg="#0f172a")
        probe_frame.grid(row=3, column=0, pady=3, padx=5, sticky="w")
        tk.Label(probe_frame, text="3. Probe Address (0-19):", bg="#0f172a", fg="white", font=("Consolas", 10)).pack(side="left")
        
        self.probe_spinbox = tk.Spinbox(probe_frame, from_=0, to=19, width=4, font=("Consolas", 11, "bold"))
        self.probe_spinbox.pack(side="left", padx=6)
        
        self.btn_probe = tk.Button(probe_frame, text="Time Access (rdtsc)", command=self.probe_ingredient, bg="#0284c7", fg="white", font=("Arial", 9, "bold"))
        self.btn_probe.pack(side="left")
        tk.Label(control_frame, text="Measures CPU clock cycles (<80 cycles = L1 Hit, >250 = DRAM Miss).", bg="#0f172a", fg="#94a3b8", font=("Consolas", 9)).grid(row=3, column=1, sticky="w")

        # Phase 4: Submit Attack
        submit_frame = tk.Frame(root, bg="#070b14")
        submit_frame.pack(fill="x", padx=20, pady=(2, 10))
        tk.Label(submit_frame, text="Enter 6 Recovered VIP Addresses (e.g., 2 5 7 11 14 18):", bg="#070b14", fg="white", font=("Consolas", 11)).pack(side="left")
        self.guess_entry = tk.Entry(submit_frame, width=20, font=("Consolas", 12, "bold"))
        self.guess_entry.pack(side="left", padx=10)
        self.btn_submit = tk.Button(submit_frame, text="SUBMIT ATTACK", command=self.verify_attack, bg="#22c55e", fg="#070b14", font=("Arial", 11, "bold"), padx=14)
        self.btn_submit.pack(side="left")

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
            self._redraw_silicon_canvas()

    # --- PROCEDURAL VECTOR HARDWARE MODEL RENDERER ---

    def _redraw_silicon_canvas(self):
        self.canvas.delete("all")
        W = self.canvas_width
        H = self.canvas_height

        # 1. Silicon Wafer Background Grid
        grid_step = 40
        for x in range(0, W, grid_step):
            self.canvas.create_line(x, 0, x, H, fill="#0d1527", width=1)
        for y in range(0, H, grid_step):
            self.canvas.create_line(0, y, W, y, fill="#0d1527", width=1)

        # Section Boundary Coordinates
        cpu_x1, cpu_y1 = 20, 20
        cpu_x2, cpu_y2 = int(W * 0.35), H - 20

        bus_x1, bus_y1 = cpu_x2 + 12, 20
        bus_x2, bus_y2 = int(W * 0.63), H - 20

        ram_x1, ram_y1 = bus_x2 + 12, 20
        ram_x2, ram_y2 = W - 20, H - 20

        # ==============================================================
        # MODEL 1: x86_64 CPU CORE & L1 SRAM DATA CACHE (VECTOR MODEL)
        # ==============================================================
        # Package Border & Metallic LGA Pins
        self.canvas.create_rectangle(cpu_x1, cpu_y1, cpu_x2, cpu_y2, fill="#090e1a", outline="#0284c7", width=2)
        pin_spacing = 18
        for px in range(cpu_x1 + 10, cpu_x2 - 10, pin_spacing):
            self.canvas.create_rectangle(px, cpu_y1 - 4, px + 8, cpu_y1, fill="#eab308", outline="")
            self.canvas.create_rectangle(px, cpu_y2, px + 8, cpu_y2 + 4, fill="#eab308", outline="")

        # Header Title
        self.canvas.create_text(cpu_x1 + (cpu_x2 - cpu_x1) // 2, cpu_y1 + 18, 
                                text="CPU CORE DIE: L1 DATA SRAM (32KB)", fill="#38bdf8", font=("Consolas", 11, "bold"))

        # 4-Set SRAM Tag & Data Matrix
        set_box_y = cpu_y1 + 38
        set_height = max(42, int((cpu_y2 - set_box_y - 65) / 4))
        is_flushed = (len(self.prep_counter) == 0)

        for s in range(4):
            sy = set_box_y + s * set_height
            cached_in_set = [x for x in sorted(self.prep_counter) if x % 4 == s]
            has_line = len(cached_in_set) > 0
            status_col = "#22c55e" if has_line else "#64748b"
            box_border = "#10b981" if has_line else "#1e293b"
            box_fill = "#0c2340" if has_line else "#090f1d"
            status_txt = "[V=1 VALID]" if has_line else "[V=0 EMPTY]"

            # Set Container
            self.canvas.create_rectangle(cpu_x1 + 14, sy, cpu_x2 - 14, sy + set_height - 6, fill=box_fill, outline=box_border, width=1.5 if has_line else 1)
            # Index Header block
            self.canvas.create_rectangle(cpu_x1 + 18, sy + 4, cpu_x1 + 105, sy + set_height - 10, fill="#111c33", outline="#1e293b")
            self.canvas.create_text(cpu_x1 + 61, sy + (set_height - 6) // 2, text=f"SET {s} [idx 0b{s:02b}]", fill="#38bdf8", font=("Consolas", 9, "bold"))
            # Valid Bit & Status
            self.canvas.create_text(cpu_x1 + 155, sy + (set_height - 6) // 2, text=status_txt, fill=status_col, font=("Consolas", 9, "bold"))

            # Specific cached memory tags/addresses
            if has_line:
                tags_str = "TAGS: " + ", ".join(f"0x{x:02x}" for x in cached_in_set)
                data_col = "#facc15"
            else:
                tags_str = "TAGS: [LINE INVALID / COLD]"
                data_col = "#475569"
            self.canvas.create_text(cpu_x2 - 18, sy + (set_height - 6) // 2, text=tags_str, fill=data_col, font=("Consolas", 9, "bold"), anchor="e")

        # Core State Badge
        state_col = "#ef4444" if is_flushed else "#22c55e"
        state_msg = "⚡ L1 STATUS: ALL LINES EVICTED (clflush)" if is_flushed else f"⚡ L1 STATUS: {len(self.prep_counter)} VIP LINES RESIDENT IN SRAM"
        self.canvas.create_rectangle(cpu_x1 + 14, cpu_y2 - 42, cpu_x2 - 14, cpu_y2 - 12, fill="#111c33", outline=state_col, width=1.5)
        self.canvas.create_text(cpu_x1 + (cpu_x2 - cpu_x1) // 2, cpu_y2 - 27, text=state_msg, fill=state_col, font=("Consolas", 10, "bold"))

        # ==============================================================
        # MODEL 2: QPI/UPI SYSTEM BUS & RDTSC OSCILLOSCOPE (VECTOR MODEL)
        # ==============================================================
        mid_y = (bus_y1 + bus_y2) // 2
        # System Bus Header and Traces (placed above oscilloscope)
        bus_trace_y1 = bus_y1 + 18
        bus_trace_y2 = bus_y1 + 28
        self.canvas.create_text(bus_x1 + (bus_x2 - bus_x1) // 2, bus_y1 + 8, text="HIGH-SPEED SYSTEM BUS (QPI/UPI 64-BYTE)", fill="#cbd5e1", font=("Consolas", 9, "bold"))
        self.canvas.create_line(cpu_x2, bus_trace_y1, ram_x1, bus_trace_y1, fill="#f59e0b", width=3)
        self.canvas.create_line(cpu_x2, bus_trace_y2, ram_x1, bus_trace_y2, fill="#f59e0b", width=3)

        # Draw Animated Bus Transmission Packet if probe happened
        if self.last_probe_info["addr"] is not None:
            pulse_x = bus_x1 + 40 + (int(self.token_norm_x * (bus_x2 - bus_x1)) % max(1, bus_x2 - bus_x1 - 80))
            self.canvas.create_rectangle(pulse_x - 10, bus_trace_y1 - 3, pulse_x + 10, bus_trace_y2 + 3, fill="#38bdf8", outline="#ffffff", width=1.5)

        # RDTSC Digital Storage Oscilloscope (Vertically Centered and Well-Proportioned)
        inst_y1 = bus_trace_y2 + 18
        inst_y2 = bus_y2 - 12
        self.canvas.create_rectangle(bus_x1 + 10, inst_y1, bus_x2 - 10, inst_y2, fill="#050a14", outline="#0284c7", width=2)
        
        # Oscilloscope Screen Bezel & Title
        self.canvas.create_rectangle(bus_x1 + 14, inst_y1 + 4, bus_x2 - 14, inst_y1 + 30, fill="#0f172a", outline="")
        self.canvas.create_text(bus_x1 + 24, inst_y1 + 17, text="⏱ RDTSC HARDWARE LATENCY OSCILLOSCOPE", fill="#38bdf8", font=("Consolas", 10, "bold"), anchor="w")
        self.canvas.create_text(bus_x2 - 24, inst_y1 + 17, text="TIMEBASE: 50 cyc/div", fill="#94a3b8", font=("Consolas", 9), anchor="e")

        # Oscilloscope Grid Display
        grid_top = inst_y1 + 36
        grid_bot = inst_y2 - 14
        grid_w = (bus_x2 - 20) - (bus_x1 + 20)
        grid_h = grid_bot - grid_top
        
        for gx in range(bus_x1 + 20, bus_x2 - 20, max(30, grid_w // 8)):
            self.canvas.create_line(gx, grid_top, gx, grid_bot, fill="#0f1d33", dash=(2, 4))
        for gy in range(grid_top, grid_bot, max(24, grid_h // 5)):
            self.canvas.create_line(bus_x1 + 20, gy, bus_x2 - 20, gy, fill="#0f1d33", dash=(2, 4))

        # Threshold Line (120 cycles)
        thresh_y = grid_top + int(grid_h * 0.45)
        self.canvas.create_line(bus_x1 + 20, thresh_y, bus_x2 - 20, thresh_y, fill="#eab308", dash=(4, 4), width=1.5)
        self.canvas.create_text(bus_x2 - 24, thresh_y - 8, text="THRESHOLD: ~120 CYCLES", fill="#eab308", font=("Consolas", 8, "bold"), anchor="e")

        # Waveform and Measurement Readout
        if self.last_probe_info["addr"] is not None:
            hit = self.last_probe_info["hit"]
            cyc = self.last_probe_info["cycles"]
            c_col = "#22c55e" if hit else "#ef4444"
            status_str = f"PROBED: ADDR 0x{self.last_probe_info['addr']:02x}  |  LATENCY: {cyc} CYCLES  |  RESULT: {'L1 CACHE HIT' if hit else 'DRAM MISS'}"
            self.canvas.create_text(bus_x1 + (bus_x2 - bus_x1) // 2, grid_top + 18, text=status_str, fill=c_col, font=("Consolas", 11, "bold"))

            # Draw Real-Time Oscilloscope Waveform
            wave_baseline = grid_bot - int(grid_h * 0.3)
            wave_x1 = bus_x1 + 25
            wave_x2 = bus_x2 - 25
            mid_x = (wave_x1 + wave_x2) // 2

            if hit:
                # Fast sharp transient spike (<80 cycles: 30-70 cycles)
                self.canvas.create_line(
                    wave_x1, wave_baseline,
                    mid_x - 40, wave_baseline,
                    mid_x - 15, wave_baseline - int(grid_h * 0.45),
                    mid_x + 15, wave_baseline,
                    wave_x2, wave_baseline,
                    fill="#22c55e", width=3
                )
                self.canvas.create_text(mid_x, wave_baseline - int(grid_h * 0.45) - 10, text=f"⚡ FAST ACCESS ({cyc} cyc)", fill="#22c55e", font=("Consolas", 9, "bold"))
            else:
                # Wide, delayed memory bus transaction wave (>250 cycles: 250-320 cycles)
                self.canvas.create_line(
                    wave_x1, wave_baseline,
                    mid_x - 90, wave_baseline,
                    mid_x - 60, wave_baseline - int(grid_h * 0.35),
                    mid_x + 60, wave_baseline - int(grid_h * 0.35),
                    mid_x + 90, wave_baseline,
                    wave_x2, wave_baseline,
                    fill="#ef4444", width=3
                )
                self.canvas.create_text(mid_x, wave_baseline - int(grid_h * 0.35) - 10, text=f"⏳ SYSTEM BUS STALL ({cyc} cyc)", fill="#ef4444", font=("Consolas", 9, "bold"))
        else:
            self.canvas.create_text(bus_x1 + (bus_x2 - bus_x1) // 2, grid_top + 24, text="OSCILLOSCOPE READY: PROBE ANY ADDRESS (0-19)", fill="#facc15", font=("Consolas", 10, "bold"))
            self.canvas.create_text(bus_x1 + (bus_x2 - bus_x1) // 2, grid_top + 46, text="L1 HIT: <80 CYCLES   |   DRAM MISS: >250 CYCLES", fill="#94a3b8", font=("Consolas", 9))
            wave_baseline = grid_bot - int(grid_h * 0.3)
            self.canvas.create_line(bus_x1 + 25, wave_baseline, bus_x2 - 25, wave_baseline, fill="#334155", width=2)

        # ==============================================================
        # MODEL 3: DDR4 PHYSICAL DRAM DIMM MODULE (VECTOR MODEL)
        # ==============================================================
        self.canvas.create_rectangle(ram_x1, ram_y1, ram_x2, ram_y2, fill="#042f2e", outline="#14b8a6", width=2)
        # Gold DIMM Edge Connector Pins
        for px in range(ram_x1 + 12, ram_x2 - 12, 14):
            self.canvas.create_rectangle(px, ram_y2, px + 6, ram_y2 + 6, fill="#eab308", outline="")

        self.canvas.create_text(ram_x1 + (ram_x2 - ram_x1) // 2, ram_y1 + 18, text="OFF-CHIP DDR4 DRAM (DIMM MODULE - BANK 0)", fill="#2dd4bf", font=("Consolas", 11, "bold"))

        # 20 Address Matrix Grid (4 rows x 5 cols)
        grid_x0 = ram_x1 + 16
        grid_y0 = ram_y1 + 38
        cell_w = max(45, int((ram_x2 - ram_x1 - 48) / 5))
        cell_h = max(32, int((ram_y2 - ram_y1 - 65) / 4))

        last_probed_addr = self.last_probe_info.get("addr")

        for i in range(20):
            c = i % 5
            r = i // 5
            cx = grid_x0 + c * cell_w
            cy = grid_y0 + r * cell_h
            is_cached = i in self.prep_counter
            is_just_probed = (last_probed_addr == i)

            if is_just_probed:
                cell_outline = "#facc15"
                border_w = 3
            elif is_cached:
                cell_outline = "#22c55e"
                border_w = 2
            else:
                cell_outline = "#334155"
                border_w = 1

            cell_fill = "#064e3b" if is_cached else "#090f1d"

            self.canvas.create_rectangle(cx, cy, cx + cell_w - 6, cy + cell_h - 6, fill=cell_fill, outline=cell_outline, width=border_w)
            
            # High-contrast, scalable text labels
            addr_text_color = "#ffffff" if is_cached else "#cbd5e1"
            self.canvas.create_text(cx + (cell_w - 6) // 2, cy + 12, text=f"0x{i:02x}", fill=addr_text_color, font=("Consolas", 10, "bold"))
            
            status_text = "L1 HIT" if is_cached else "DRAM"
            status_color = "#34d399" if is_cached else "#64748b"
            self.canvas.create_text(cx + (cell_w - 6) // 2, cy + cell_h - 14, text=status_text, fill=status_color, font=("Consolas", 8, "bold"))

        # ==============================================================
        # MODEL 4: HARDWARE EXECUTION THREAD TOKEN (VECTOR MODEL)
        # ==============================================================
        tx = int(W * self.token_norm_x)
        ty = int(H * self.token_norm_y)
        self._draw_thread_token(tx, ty)

    def _draw_thread_token(self, cx, cy):
        # Outer Glowing Diamond Processor Core Token
        r = 16
        self.canvas.create_polygon(cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill="#0284c7", outline="#38bdf8", width=2, tags="token")
        # Inner Core Indicator
        ir = 8
        self.canvas.create_polygon(cx, cy - ir, cx + ir, cy, cx, cy + ir, cx - ir, cy, fill="#ffffff", outline="", tags="token")
        self.canvas.create_text(cx, cy + r + 12, text="CORE THREAD", fill="#38bdf8", font=("Consolas", 8, "bold"), tags="token")

    # --- ATTACK STATE MACHINE METHODS ---

    def flush_cache(self):
        """Phase 1: Clear L1 SRAM lines via clflush."""
        self.prep_counter.clear()
        self.last_probe_info = {"addr": None, "hit": None, "cycles": None}
        self.token_norm_x = 0.16
        self._redraw_silicon_canvas()
        self.status_label.config(text="Cache Flushed: All lines evicted from L1 Data Cache to DRAM [V=0].")
        self.timer_label.config(text="Hardware RDTSC Latency: -- cycles")

    def trigger_victim(self):
        """Phase 2: Victim loads secrets into L1 Data Cache."""
        for item in self.secret_ingredients:
            if item not in self.prep_counter:
                self.prep_counter.append(item)

        # Animate Execution Thread traversing QPI bus to DRAM and back
        for step in range(25):
            self.token_norm_x = 0.16 + (0.80 - 0.16) * (step / 25)
            self._redraw_silicon_canvas()
            self.root.update()
            time.sleep(0.015)

        for step in range(25):
            self.token_norm_x = 0.80 - (0.80 - 0.16) * (step / 25)
            self._redraw_silicon_canvas()
            self.root.update()
            time.sleep(0.015)

        self.token_norm_x = 0.16
        self._redraw_silicon_canvas()
        self.status_label.config(text="Victim Executed: VIP memory lines loaded into L1 Data Cache [V=1].")

    def _update_budget_hud(self):
        rem = self.probes_remaining
        color = "#22c55e" if rem > 8 else "#f59e0b" if rem > 3 else "#ef4444"
        self.budget_label.config(text=f"Probe Budget Remaining: {rem} / {self.max_probes}", fg=color)

    def reset_round(self):
        self.secret_ingredients = random.sample(self.all_ingredients, 6)
        self.prep_counter = random.sample(self.all_ingredients, 6)
        self.probes_remaining = self.max_probes
        self.last_probe_info = {"addr": None, "hit": None, "cycles": None}
        self.token_norm_x = 0.16
        self._update_budget_hud()
        self._redraw_silicon_canvas()
        self.status_label.config(text="Round Reset! Flush cache (clflush) and trigger victim order to retry.", fg="#facc15")
        self.timer_label.config(text="Hardware RDTSC Latency: -- cycles")

    def probe_ingredient(self):
        """Phase 3: Measure hardware fetch latency via rdtsc."""
        if self.probes_remaining <= 0:
            self.status_label.config(text="Out of probes! Hardware security monitor flagged access threshold.", fg="#ef4444")
            messagebox.showwarning(
                "Probe Budget Depleted", 
                "You have used all 18 probes!\nThe CPU security monitor flagged high cache contention.\n\nThe round has been reset. Flush the cache to retry!"
            )
            self.reset_round()
            return

        try:
            ingredient_id = int(self.probe_spinbox.get())
        except ValueError:
            return

        if ingredient_id not in self.all_ingredients:
            return

        self.probes_remaining -= 1
        self._update_budget_hud()
        self._set_ui_state("disabled")
        start_time = time.time()
        is_hit = ingredient_id in self.prep_counter

        if is_hit:
            cycles = random.randint(52, 78)
            self.last_probe_info = {"addr": ingredient_id, "hit": True, "cycles": cycles}
            self.status_label.config(text=f"Probing 0x{ingredient_id:02x}... L1 SRAM HIT! ({cycles} cycles)")
            
            # Fast Core Hop Animation
            for i in range(4):
                self.token_norm_y = 0.50 - 0.06
                self._redraw_silicon_canvas()
                self.root.update()
                time.sleep(0.02)
                self.token_norm_y = 0.50
                self._redraw_silicon_canvas()
                self.root.update()
                time.sleep(0.02)

            elapsed = time.time() - start_time
            self.timer_label.config(text=f"RDTSC: {cycles} cycles (<0.05s) - FAST L1 CACHE HIT", fg="#22c55e")

        else:
            cycles = random.randint(260, 320)
            self.last_probe_info = {"addr": ingredient_id, "hit": False, "cycles": cycles}
            self.status_label.config(text=f"Probing 0x{ingredient_id:02x}... DRAM CACHE MISS! ({cycles} cycles)")

            # Bus Traversal Animation across to DRAM and back
            for step in range(25):
                self.token_norm_x = 0.16 + (0.80 - 0.16) * (step / 25)
                self._redraw_silicon_canvas()
                self.root.update()
                time.sleep(0.015)

            time.sleep(0.18) # Simulate DRAM line fetch delay

            for step in range(25):
                self.token_norm_x = 0.80 - (0.80 - 0.16) * (step / 25)
                self._redraw_silicon_canvas()
                self.root.update()
                time.sleep(0.015)

            self.token_norm_x = 0.16
            elapsed = time.time() - start_time
            self.timer_label.config(text=f"RDTSC: {cycles} cycles (>0.80s) - SLOW OFF-CHIP DRAM ACCESS", fg="#ef4444")
            self.prep_counter.append(ingredient_id)

        self._redraw_silicon_canvas()
        self._set_ui_state("normal")

    def verify_attack(self):
        """Phase 4: Verify the student's submission."""
        guess_str = self.guess_entry.get().strip()
        try:
            user_guess = sorted([int(x) for x in guess_str.replace(",", " ").split()])
        except ValueError:
            messagebox.showerror("Error", "Please enter 6 numbers separated by spaces.")
            return

        if len(user_guess) != 6:
            messagebox.showerror("Error", f"Please enter exactly 6 numbers separated by spaces (you entered {len(user_guess)}).")
            return

        secret = sorted(self.secret_ingredients)
        if user_guess == secret:
            self.status_label.config(text="ACCESS GRANTED! Secret extracted successfully.", fg="#22c55e")
            messagebox.showinfo(
                "Victory!", 
                f"Part 1 Cleared!\nYou successfully mapped the cache and extracted all 6 VIP addresses: {secret}\n\nClick OK to launch Part 2 (CPU Pipeline Simulation)!"
            )
            self.root.destroy()
            self.launch_part_2()
        else:
            self.status_label.config(text="ACCESS DENIED! Incorrect memory footprint.", fg="#ef4444")
            messagebox.showerror(
                "Failed", 
                "Access Denied.\nThe timing footprint does not match the VIP's secret addresses.\nRemember to FLUSH first, TRIGGER VICTIM, and record all latencies < 80 cycles!"
            )

    def launch_part_2(self):
        """Launches Part 2 (kitchen_espionage_part2.py) in full screen."""
        stop_bgm()
        part2_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Part 2"))
        part2_script = os.path.join(part2_dir, "kitchen_espionage_part2.py")
        if os.path.exists(part2_script):
            subprocess.run([sys.executable, part2_script], cwd=part2_dir)
        else:
            messagebox.showerror("Error", f"Could not find Part 2 script at:\n{part2_script}")

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

    def show_instructions(self):
        msg = (
            "🎯 MISSION OBJECTIVE:\n"
            "Extract the 6 secret VIP memory addresses (from physical space 0-19) using a Flush+Reload cache side-channel attack!\n\n"
            "⚙️ HARDWARE ARCHITECTURE:\n"
            "• CPU Core & L1 Cache = 32KB On-Die SRAM (Fast access, <80 cycles / <0.05s)\n"
            "• DDR4 DRAM = Off-Chip Main Memory (Slow access, >250 cycles / >0.80s)\n"
            "• System Bus = High-speed interconnect transferring 64-byte cache lines\n\n"
            "📋 4 ATTACK STEPS:\n"
            "1. Flush Cache: Execute clflush to invalidate all L1 SRAM lines out to DRAM [V=0].\n"
            "2. Trigger Victim: VIP accesses their 6 secret addresses, reloading them into L1 [V=1].\n"
            "3. Measure Latency: Test addresses (0 to 19). You have an 18-probe budget!\n"
            "   - FAST latency (< 80 cycles) -> CACHE HIT! Accessed by the victim!\n"
            "   - SLOW latency (> 250 cycles) -> CACHE MISS! Unrelated address (fetched from DRAM).\n"
            "4. Submit Attack: Enter all 6 identified addresses and click SUBMIT ATTACK!\n\n"
            "🔬 For in-depth x86 hardware implementation details (clflush, rdtsc, mfence), click 'Section B: Tech Deep Dive'!"
        )
        messagebox.showinfo("Part 1 - Mission Briefing & Instructions", msg)

    def show_tech_details(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🔬 Section B: Hardware Architecture & Flush+Reload Deep Dive")
        dialog.geometry("800x600")
        dialog.configure(bg="#070b14")
        dialog.transient(self.root)

        header = tk.Frame(dialog, bg="#0f172a", pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🔬 SECTION B: FLUSH+RELOAD HARDWARE IMPLEMENTATION", bg="#0f172a", fg="#facc15", font=("Consolas", 12, "bold")).pack()
        tk.Label(header, text="Real Silicon Microarchitecture: clflush, Shared Physical Frames, and rdtsc", bg="#0f172a", fg="#cbd5e1", font=("Arial", 9)).pack()

        text_box = tk.Text(dialog, bg="#0f172a", fg="#ecf0f1", font=("Consolas", 10), padx=16, pady=16, wrap="word", relief="flat")
        text_box.pack(fill="both", expand=True, padx=20, pady=12)

        tech_doc = (
            "========================================================================\n"
            " 1. HOW 'CLEARING THE COUNTER' (FLUSH) WORKS ON REAL HARDWARE\n"
            "========================================================================\n"
            "In real x86 systems, an unprivileged user process executes the instruction:\n\n"
            "      clflush [virtual_address]    (or clflushopt)\n\n"
            "• What clflush actually does:\n"
            "  1. It evicts the 64-byte cache line containing that memory address from ALL\n"
            "     cache levels (L1 Data, L2, and shared L3/LLC - Last Level Cache).\n"
            "  2. It writes back modified (dirty) data to DRAM and invalidates the cache tag.\n"
            "  3. Any subsequent memory access MUST fetch directly from high-latency DRAM.\n\n"
            "• Evict+Reload (When clflush is blocked or on ARMv7):\n"
            "  If the OS or architecture restricts clflush, the attacker allocates an\n"
            "  'Eviction Set' (memory buffers mapped to the exact same cache sets). By\n"
            "  accessing these lines in a loop, the CPU's hardware LRU (Least Recently Used)\n"
            "  replacement policy naturally evicts the victim's line out to DRAM.\n\n"
            "========================================================================\n"
            " 2. SHARED MEMORY: WHY CAN THE ATTACKER ACCESS THE VICTIM'S DATA?\n"
            "========================================================================\n"
            "Flush+Reload requires shared memory. This occurs legitimately via:\n"
            "  • Shared Dynamic Libraries (.so / .dll files, e.g. OpenSSL, libc).\n"
            "  • Kernel Samepage Merging (KSM) / memory deduplication in virtualization.\n"
            "Even though virtual addresses differ, the OS page tables map both processes\n"
            "to the EXACT SAME PHYSICAL DRAM FRAME. When the attacker flushes their\n"
            "virtual address, the shared physical line is evicted for the victim too!\n\n"
            "========================================================================\n"
            " 3. HIGH-RESOLUTION TIMING MEASUREMENT (rdtsc & FENCES)\n"
            "========================================================================\n"
            "In C/assembly, the attacker times memory fetches using the CPU cycle counter:\n\n"
            "      mfence; lfence;           // Serialization barrier: wait for prior instructions\n"
            "      uint64_t t1 = __rdtsc();  // Read Time-Stamp Counter\n"
            "      maccess(target_addr);     // Fetch target cache line\n"
            "      lfence;                   // Wait for memory fetch to finish\n"
            "      uint64_t delta = __rdtsc() - t1;\n\n"
            "• Hardware Decision Threshold:\n"
            "  - L1/L2/L3 Hit : ~40 - 80 cycles   -> VICTIM ACCESSED IT!\n"
            "  - DRAM Miss    : ~200 - 350 cycles -> VICTIM DID NOT ACCESS IT.\n"
        )
        text_box.insert("1.0", tech_doc)
        text_box.config(state="disabled")

        tk.Button(dialog, text="Close Deep Dive", command=dialog.destroy, bg="#1e293b", fg="white", font=("Arial", 10)).pack(pady=(0, 10))

    def _set_ui_state(self, state):
        self.btn_flush.config(state=state)
        self.btn_victim.config(state=state)
        self.btn_probe.config(state=state)
        self.btn_submit.config(state=state)

if __name__ == "__main__":
    root = tk.Tk()
    app = InteractiveKitchen(root)
    root.mainloop()
