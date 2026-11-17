import tkinter as tk
from tkinter import messagebox
import random
import time
import os
import sys
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

class RowhammerKitchenGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kitchen Espionage - Part 3 (Double-Sided Rowhammer DRAM Attack)")
        self.root.configure(bg="#070b14")

        # Fullscreen on launch
        self.is_fullscreen = False
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1400x900")
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

        self.pantry_pool = [
            "Bag of rice", "Black pepper shaker", "A jar of honey", "Bag of flour",
            "Box of salt", "Salt shaker", "Soy sauce bottle", "Vinegar bottle",
            "Dried oregano", "Butter block", "Milk carton", "Cheddar wedge", "Bag of sugar"
        ]

        self._init_game_state()

        # Dynamic Canvas Dimensions
        self.canvas_width = 1200
        self.canvas_height = 420
        self.active_hammered_row = None
        self.show_sparks = False
        self.token_norm_x = 0.08
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

        self.actions_label = tk.Label(hud_frame, text="Actions Remaining: 20 / 20", bg="#070b14", fg="#22c55e", font=("Consolas", 13, "bold"))
        self.actions_label.pack(side="left")

        self.voltage_label = tk.Label(hud_frame, text="Victim Cell Voltage: 1.20V (100% Charge)", bg="#070b14", fg="#38bdf8", font=("Consolas", 12, "bold"))
        self.voltage_label.pack(side="right")

        self.status_label = tk.Label(root, text="System Ready. Select an accessible even row (2-18) to hammer.", bg="#070b14", fg="#facc15", font=("Arial", 11, "bold"))
        self.status_label.pack(pady=2)

        self.feedback_label = tk.Label(root, text="The secret Page Table Entry (PTE) is mapped to an odd physical DRAM row...", bg="#070b14", fg="#94a3b8", font=("Consolas", 10, "italic"))
        self.feedback_label.pack(pady=2)

        # --- 3. ATTACKER CONTROL PANEL ---
        ctrl_frame = tk.Frame(root, bg="#0f172a", bd=1, relief="solid", padx=16, pady=8)
        ctrl_frame.pack(fill="x", padx=16, pady=6)

        header_frame = tk.Frame(ctrl_frame, bg="#0f172a")
        header_frame.pack(fill="x", pady=(0, 6))

        tk.Label(header_frame, text="⚡ ROWHAMMER ATTACK CONSOLE (DRAM DISTURBANCE ENGINE)", bg="#0f172a", fg="#38bdf8", font=("Consolas", 11, "bold")).pack(side="left")

        self.btn_audio = tk.Button(header_frame, text="🔊 Music: ON", command=self.toggle_music, bg="#1e293b", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_audio.pack(side="right", padx=(4, 0))
        self.btn_help = tk.Button(header_frame, text="📋 Briefing", command=self.show_instructions, bg="#0284c7", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_help.pack(side="right", padx=(4, 0))
        self.btn_tech = tk.Button(header_frame, text="🔬 Section B: Tech Deep Dive", command=self.show_tech_details, bg="#9333ea", fg="white", font=("Arial", 9, "bold"), bd=1)
        self.btn_tech.pack(side="right", padx=(4, 0))

        # Hammer controls row
        hammer_frame = tk.Frame(ctrl_frame, bg="#0f172a")
        hammer_frame.pack(fill="x", pady=4)

        tk.Label(hammer_frame, text="Target Aggressor Row (Even Only):", bg="#0f172a", fg="white", font=("Consolas", 10)).pack(side="left")
        self.row_var = tk.StringVar(value="2")
        self.row_dropdown = tk.OptionMenu(hammer_frame, self.row_var, *[str(x) for x in self.accessible_rows])
        self.row_dropdown.config(bg="#1e293b", fg="white", font=("Consolas", 10, "bold"), width=4)
        self.row_dropdown.pack(side="left", padx=8)

        self.btn_hammer = tk.Button(hammer_frame, text="⚡ Activate Wordline (Hammer)", command=self.hammer_row, bg="#d97706", fg="white", font=("Arial", 10, "bold"), padx=10)
        self.btn_hammer.pack(side="left", padx=5)

        tk.Label(hammer_frame, text="Alternate between flanking even rows to induce electromagnetic crosstalk.", bg="#0f172a", fg="#94a3b8", font=("Consolas", 9)).pack(side="left", padx=10)

        # Verification controls row
        verify_frame = tk.Frame(ctrl_frame, bg="#0f172a")
        verify_frame.pack(fill="x", pady=4)

        self.btn_check = tk.Button(verify_frame, text="🔍 Check If Bit Flipped (Inspect Access List)", command=self.check_chef, bg="#059669", fg="white", font=("Arial", 10, "bold"), padx=10)
        self.btn_check.pack(side="left", padx=5)

        tk.Label(verify_frame, text="Checks if PTE bit flipped to supervisor root mode. (-3 Actions penalty if checked prematurely)", bg="#0f172a", fg="#94a3b8", font=("Consolas", 9)).pack(side="left", padx=10)

        self.btn_reset = tk.Button(verify_frame, text="🔄 Restart Level", command=self.reset_level, bg="#475569", fg="white", font=("Arial", 9, "bold"), padx=8)
        self.btn_reset.pack(side="right", padx=5)

        # --- 4. DRAM ROW MATRIX ACCESS INDICATOR ---
        shelf_frame = tk.LabelFrame(root, text="DRAM PHYSICAL BANK ROW ACCESS MAP", bg="#0f172a", fg="#38bdf8", font=("Consolas", 9, "bold"), padx=10, pady=4)
        shelf_frame.pack(fill="x", padx=16, pady=(2, 8))

        self.shelf_indicators = {}
        for r in range(1, 21):
            is_accessible = (r % 2 == 0)
            color = "#059669" if is_accessible else "#334155"
            text = f"Row {r}" if is_accessible else f"Row {r} 🔒"
            lbl = tk.Label(shelf_frame, text=text, bg=color, fg="white", font=("Consolas", 8, "bold"), width=7, pady=2)
            lbl.grid(row=0 if r <= 10 else 1, column=(r - 1) % 10, padx=2, pady=2, sticky="nsew")
            shelf_frame.grid_columnconfigure((r - 1) % 10, weight=1)
            self.shelf_indicators[r] = lbl

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
            self._redraw_dram_canvas(hammered_row=self.active_hammered_row, show_sparks=self.show_sparks)

    def _init_game_state(self):
        self.shelves = {}
        for i in range(1, 21):
            self.shelves[i] = random.sample(self.pantry_pool, k=random.randint(2, 4))

        valid_targets = [3, 5, 7, 9, 11, 13, 15, 17]
        self.target_row = random.choice(valid_targets)
        self.sandwich_a = self.target_row - 1
        self.sandwich_b = self.target_row + 1
        self.recent_hammers = []
        self.cell_voltage = 1.20

        self.shelves[self.target_row].append("The Security Access List")
        self.accessible_rows = [i for i in range(2, 20, 2)]
        self.max_actions = 20
        self.actions_remaining = 20
        self.access_list_fallen = False
        self.game_over = False

    # --- PROCEDURAL VECTOR DRAM SILICON MATRIX RENDERER ---

    def _redraw_dram_canvas(self, hammered_row=None, show_sparks=False):
        self.canvas.delete("all")
        W = self.canvas_width
        H = self.canvas_height
        self.active_hammered_row = hammered_row
        self.show_sparks = show_sparks

        # 1. Silicon Substrate Background Grid
        grid_step = 40
        for x in range(0, W, grid_step):
            self.canvas.create_line(x, 0, x, H, fill="#0d1527", width=1)
        for y in range(0, H, grid_step):
            self.canvas.create_line(0, y, W, y, fill="#0d1527", width=1)

        # Header Title
        self.canvas.create_text(W // 2, 16, text="DRAM SILICON SUBSTRATE (<20nm Technology) • BANK 0 ROW MATRIX", fill="#38bdf8", font=("Consolas", 10, "bold"))

        # Geometry Coordinates
        margin_x = 30
        content_w = W - 2 * margin_x
        row_y1 = max(45, int(H * 0.18))
        row_y2 = max(115, int(H * 0.45))
        row_y3 = max(185, int(H * 0.72))
        pte_y = max(245, int(H * 0.85))

        # ==============================================================
        # AGGRESSOR WORDLINE 1 (ROW A)
        # ==============================================================
        is_agg1 = (hammered_row == self.sandwich_a)
        w1_col = "#ef4444" if is_agg1 else "#475569"
        w1_width = 4 if is_agg1 else 2
        self.canvas.create_line(margin_x, row_y1, margin_x + content_w, row_y1, fill=w1_col, width=w1_width)
        w1_label = f"Aggressor Wordline 1: Row {self.sandwich_a} (Even) {'⚡ HIGH-VOLTAGE ACTIVATION (V_PP = 2.5V)' if is_agg1 else '[Precharged 0V]'}"
        self.canvas.create_text(margin_x + 10, row_y1 - 12, text=w1_label, fill="#f87171" if is_agg1 else "#94a3b8", font=("Consolas", 9, "bold"), anchor="w")

        # ==============================================================
        # VICTIM WORDLINE (ROW T - SENSITIVE PTE PAGE TABLE ENTRY)
        # ==============================================================
        v_col = "#ef4444" if self.access_list_fallen else "#22c55e"
        self.canvas.create_line(margin_x, row_y2, margin_x + content_w, row_y2, fill=v_col, width=3)
        v_status = "⚡ BIT-FLIP BREACHED! [PAGE TABLE ENTRY ROOT EXPLOIT]" if self.access_list_fallen else "PROTECTED [Capacitor Charged]"
        v_label = f"VICTIM WORDLINE: Row {self.target_row} [THE SECURITY ACCESS LIST / PTE] &bull; {v_status}"
        self.canvas.create_text(margin_x + 10, row_y2 - 28, text=v_label, fill="#f87171" if self.access_list_fallen else "#4ade80", font=("Consolas", 10, "bold"), anchor="w")

        # 6 Trench Storage Capacitor Models along the Victim Row
        cap_count = 6
        cap_w = max(70, int((content_w - 60) / cap_count))
        cap_h = 44
        cap_y = row_y2 - 18

        for c in range(cap_count):
            cx = margin_x + 30 + c * cap_w
            is_target_cell = (c == 2)
            cell_v = self.cell_voltage if is_target_cell else 1.18
            charge_pct = min(1.0, max(0.05, cell_v / 1.20))
            is_flipped = is_target_cell and self.access_list_fallen

            # Trench Capacitor Outline
            self.canvas.create_rectangle(cx, cap_y, cx + cap_w - 14, cap_y + cap_h, fill="#090e1a", outline="#ef4444" if is_flipped else "#38bdf8", width=1.5 if is_target_cell else 1)
            self.canvas.create_text(cx + (cap_w - 14) // 2, cap_y + 9, text=f"Cap C{c}", fill="#94a3b8", font=("Consolas", 7, "bold"))

            # Charge Level Bar (Trench Capacitor Dielectric Storage)
            bar_col = "#ef4444" if is_flipped else "#22c55e" if charge_pct > 0.6 else "#f59e0b"
            bar_max_w = cap_w - 22
            self.canvas.create_rectangle(cx + 4, cap_y + 18, cx + 4 + int(bar_max_w * charge_pct), cap_y + 28, fill=bar_col, outline="")

            # Digital Voltage Readout
            v_text = "BIT: 0!" if is_flipped else f"{cell_v:.2f}V"
            self.canvas.create_text(cx + (cap_w - 14) // 2, cap_y + 36, text=v_text, fill=bar_col, font=("Consolas", 8, "bold"))

        # ==============================================================
        # AGGRESSOR WORDLINE 2 (ROW B)
        # ==============================================================
        is_agg2 = (hammered_row == self.sandwich_b)
        w2_col = "#ef4444" if is_agg2 else "#475569"
        w2_width = 4 if is_agg2 else 2
        self.canvas.create_line(margin_x, row_y3, margin_x + content_w, row_y3, fill=w2_col, width=w2_width)
        w2_label = f"Aggressor Wordline 2: Row {self.sandwich_b} (Even) {'⚡ HIGH-VOLTAGE ACTIVATION (V_PP = 2.5V)' if is_agg2 else '[Precharged 0V]'}"
        self.canvas.create_text(margin_x + 10, row_y3 + 12, text=w2_label, fill="#f87171" if is_agg2 else "#94a3b8", font=("Consolas", 9, "bold"), anchor="w")

        # ==============================================================
        # ELECTROMAGNETIC CROSSTALK SPARK ARCS
        # ==============================================================
        if show_sparks:
            spark_points = [margin_x + 60 + i * (content_w // 7) for i in range(6)]
            for sx in spark_points:
                # Top wordline to victim spark
                self.canvas.create_line(sx, row_y1, sx + 8, (row_y1 + row_y2) // 2, sx - 4, row_y2, fill="#facc15", width=2)
                # Bottom wordline to victim spark
                self.canvas.create_line(sx + 15, row_y3, sx + 22, (row_y2 + row_y3) // 2, sx + 10, row_y2, fill="#facc15", width=2)

        # ==============================================================
        # 64-BIT PAGE TABLE ENTRY (PTE) HARDWARE ARCHITECTURE REGISTER
        # ==============================================================
        if pte_y + 36 <= H:
            self.canvas.create_rectangle(margin_x, pte_y, margin_x + content_w, pte_y + 36, fill="#040914", outline="#ef4444" if self.access_list_fallen else "#0284c7", width=1.5)
            self.canvas.create_text(margin_x + 15, pte_y + 11, text="64-BIT PAGE TABLE ENTRY (PTE): [PFN: 0x00000001B400] &bull; P=1 | PCD=0 | A=1 | D=0", fill="#38bdf8", font=("Consolas", 9, "bold"), anchor="w")

            us_text = "0 (SUPERVISOR / KERNEL ROOT PRIVILEGE GRANTED!)" if self.access_list_fallen else "1 (User Mode - Unprivileged)"
            rw_text = "1 (Read / Write Access)" if self.access_list_fallen else "0 (Read-Only Protected)"
            p_color = "#ef4444" if self.access_list_fallen else "#22c55e"
            self.canvas.create_text(margin_x + 15, pte_y + 25, text=f"[BIT 2] U/S Flag: {us_text}   |   [BIT 1] R/W Flag: {rw_text}", fill=p_color, font=("Consolas", 9, "bold"), anchor="w")

        # ==============================================================
        # HARDWARE EXECUTION THREAD TOKEN
        # ==============================================================
        tok_y = row_y1 if is_agg1 else row_y3 if is_agg2 else row_y2
        self._draw_thread_token(margin_x + 12, tok_y)

    def _draw_thread_token(self, cx, cy):
        r = 12
        self.canvas.create_polygon(cx, cy - r, cx + r, cy, cx, cy + r, cx - r, cy, fill="#d97706", outline="#f59e0b", width=2, tags="token")
        ir = 6
        self.canvas.create_polygon(cx, cy - ir, cx + ir, cy, cx, cy + ir, cx - ir, cy, fill="#ffffff", outline="", tags="token")

    # --- ROWHAMMER ATTACK LOGIC ---

    def reset_level(self):
        self._init_game_state()
        self.actions_label.config(text=f"Actions Remaining: {self.max_actions} / {self.max_actions}", fg="#22c55e")
        self.voltage_label.config(text="Victim Cell Voltage: 1.20V (100% Charge)", fg="#38bdf8")
        self.status_label.config(text="Level restarted. Select an accessible even row to hammer.", fg="#facc15")
        self.feedback_label.config(text="The secret Page Table Entry (PTE) is mapped to an odd physical DRAM row...", fg="#94a3b8")
        self.btn_hammer.config(state="normal")
        self.btn_check.config(state="normal")
        self._redraw_dram_canvas()

    def hammer_row(self):
        if self.game_over or self.actions_remaining <= 0:
            return

        try:
            row_chosen = int(self.row_var.get())
        except ValueError:
            return

        if row_chosen not in self.accessible_rows:
            self.status_label.config(text=f"Access Denied! You cannot reach Row {row_chosen}.", fg="#ef4444")
            return

        self.actions_remaining -= 1
        self.recent_hammers.append(row_chosen)
        if len(self.recent_hammers) > 8:
            self.recent_hammers.pop(0)

        self._update_actions_hud()
        self.status_label.config(text=f"Executing tight read/activation loop on Row {row_chosen}...", fg="#f59e0b")

        # Double-sided check
        is_double_sided = False
        if row_chosen in (self.sandwich_a, self.sandwich_b):
            other_side = self.sandwich_b if row_chosen == self.sandwich_a else self.sandwich_a
            is_double_sided = other_side in self.recent_hammers[-4:]

            # Accelerated charge leakage due to capacitive cross-coupling
            if is_double_sided:
                self.cell_voltage = max(0.35, self.cell_voltage - 0.22)
            else:
                self.cell_voltage = max(0.68, self.cell_voltage - 0.08)

            target_items = self.shelves[self.target_row]
            fallen_this_turn = []
            drop_prob = 0.28 if is_double_sided else 0.04

            for item in target_items[:]:
                if random.random() < drop_prob:
                    target_items.remove(item)
                    fallen_this_turn.append(item)

            if fallen_this_turn:
                dropped_names = []
                for item in fallen_this_turn:
                    if "Access List" in item:
                        self.access_list_fallen = True
                        self.cell_voltage = 0.22
                        dropped_names.append("THE SECURITY ACCESS LIST (PTE)")
                    else:
                        dropped_names.append(item)

                if self.access_list_fallen:
                    self.feedback_label.config(
                        text=f"💥 DIE DISTURBANCE! Charge breached threshold... {', '.join(dropped_names)} flipped to supervisor root mode!", 
                        fg="#22c55e"
                    )
                else:
                    self.feedback_label.config(
                        text=f"💥 Charge leakage detected! {', '.join(dropped_names)} suffered partial disturbance!", 
                        fg="#f59e0b"
                    )
            else:
                if is_double_sided:
                    self.feedback_label.config(
                        text=f"⚡⚡ DOUBLE-SIDED ROWHAMMER ACTIVE! Rapidly toggling Rows {self.sandwich_a} & {self.sandwich_b} induces intense parasitic cross-talk!", 
                        fg="#f59e0b"
                    )
                else:
                    self.feedback_label.config(
                        text=f"⚡ Single-sided vibration near Row {row_chosen}! Double-sided hammering from BOTH flanking rows is required to flip bits!", 
                        fg="#facc15"
                    )
        else:
            self.cell_voltage = min(1.20, self.cell_voltage + 0.04)
            self.feedback_label.config(
                text=f"Wordline activation on Row {row_chosen} is too distant to induce capacitive coupling on protected rows.", 
                fg="#64748b"
            )

        pct = int((self.cell_voltage / 1.20) * 100)
        self.voltage_label.config(text=f"Victim Cell Voltage: {self.cell_voltage:.2f}V ({pct}% Charge)", fg="#ef4444" if self.cell_voltage < 0.4 else "#22c55e")
        self._redraw_dram_canvas(hammered_row=row_chosen, show_sparks=is_double_sided)
        self._check_failure()

    def check_chef(self):
        if self.game_over:
            return

        self.actions_remaining -= 3
        self._update_actions_hud()

        if self.access_list_fallen:
            self.game_over = True
            self.status_label.config(text="ACCESS GRANTED! Root Privilege Escalation Complete!", fg="#22c55e")
            self.feedback_label.config(
                text="The bit-flip corrupted the PTE! Virtual memory now maps directly to Kernel Page Tables (Ring 0 Access Granted)!", 
                fg="#22c55e"
            )
            self.btn_hammer.config(state="disabled")
            self.btn_check.config(state="disabled")
            self._redraw_dram_canvas()
            self.root.after(300, self.show_grand_victory_popup)
        else:
            self.status_label.config(text="Verification Failed! Cell charge intact.", fg="#ef4444")
            self.feedback_label.config(
                text="The victim capacitor voltage remains above the sense amplifier threshold. Bit has NOT flipped! (-3 Actions penalty)", 
                fg="#ef4444"
            )
            self._redraw_dram_canvas()
            self._check_failure()

    def _update_actions_hud(self):
        rem = max(0, self.actions_remaining)
        color = "#22c55e" if rem > 12 else "#f59e0b" if rem > 5 else "#ef4444"
        self.actions_label.config(text=f"Actions Remaining: {rem} / {self.max_actions}", fg=color)

    def _check_failure(self):
        if self.actions_remaining <= 0 and not self.game_over:
            self.game_over = True
            self.status_label.config(text="--- MEMORY REFRESH CYCLE EXPIRED ---", fg="#ef4444")
            self.feedback_label.config(
                text="The DRAM memory controller executed an auto-refresh cycle (tREFI) and restored capacitor charges! Progress wiped.", 
                fg="#ef4444"
            )
            messagebox.showerror(
                "Game Over", 
                "Out of Actions!\n\n"
                "The memory controller triggered an auto-refresh command (tREFI = 64ms) and recharged all victim capacitors before a bit-flip occurred.\n\n"
                "Tip: Identify adjacent even rows (Row N-1 and Row N+1) and alternate between them to maximize double-sided charge leakage!"
            )
            self.reset_level()

    def show_instructions(self):
        msg = (
            "🎯 PART 3 MISSION OBJECTIVE:\n"
            "Induce a hardware bit-flip in an inaccessible victim DRAM row containing the sensitive security access list (Page Table Entry)!\n\n"
            "⚙️ ROWHAMMER PHYSICS:\n"
            "• You can ONLY access EVEN rows (2, 4, 6, ... 18).\n"
            "• The victim's sensitive PTE is located on an unmapped ODD row (3, 5, 7, ... 17).\n"
            "• Rapidly activating adjacent aggressor wordlines induces parasitic capacitive cross-talk, bleeding charge from neighboring storage capacitors.\n\n"
            "⚡ DOUBLE-SIDED ROWHAMMERING:\n"
            "Hammering from ONE side causes weak leakage; alternating rapidly between BOTH flanking rows (Row N-1 and Row N+1) accelerates charge leakage tenfold!\n\n"
            "⚠️ ACTION BUDGET:\n"
            "You have 20 actions. Checking if the bit flipped costs 3 actions! Plan your flanking search strategically."
        )
        messagebox.showinfo("Part 3 - Mission Briefing", msg)

    def show_tech_details(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("🔬 Section B: Rowhammer Physics & Exploitation Deep Dive")
        dialog.geometry("800x600")
        dialog.configure(bg="#070b14")
        dialog.transient(self.root)

        header = tk.Frame(dialog, bg="#0f172a", pady=12)
        header.pack(fill="x")
        tk.Label(header, text="🔬 SECTION B: DRAM CAPACITOR PHYSICS & ROWHAMMER ROOT EXPLOITS", bg="#0f172a", fg="#facc15", font=("Consolas", 12, "bold")).pack()
        tk.Label(header, text="Semiconductor Charge Leakage, Double-Sided Disturbance, and Page Table Takeover", bg="#0f172a", fg="#cbd5e1", font=("Arial", 9)).pack()

        text_box = tk.Text(dialog, bg="#0f172a", fg="#ecf0f1", font=("Consolas", 10), padx=16, pady=16, wrap="word", relief="flat")
        text_box.pack(fill="both", expand=True, padx=20, pady=12)

        tech_doc = (
            "========================================================================\n"
            " 1. DRAM PHYSICS: WHY DO CELL CAPACITORS LOSE CHARGE?\n"
            "========================================================================\n"
            "Each DRAM bit cell consists of 1 Access Transistor and 1 Storage Capacitor (1T-1C).\n"
            "In modern memory (<20nm feature size), cell capacitors are microscopic trenches\n"
            "holding just ~20-30 femtofarads of charge. When an aggressor row is activated:\n\n"
            "  1. Parasitic Capacitive Coupling: Rapid voltage swings induce electromagnetic\n"
            "     cross-talk on adjacent wordlines.\n"
            "  2. Accelerated Charge Leakage: The neighboring unaccessed VICTIM row's\n"
            "     capacitors bleed charge before the scheduled DRAM refresh command arrives.\n"
            "  3. Bit-Flip: The voltage level drops below the sense amplifier threshold,\n"
            "     spontaneously flipping a 1 -> 0 or 0 -> 1!\n\n"
            "========================================================================\n"
            " 2. CRITICAL CLARIFICATION: WHERE DO BITS FLIP?\n"
            "========================================================================\n"
            "  • Aggressor Row (Attacker's row) : Reads normally; bits DO NOT flip here.\n"
            "  • Victim Row (Neighboring row)   : BITS FLIP HERE without being accessed!\n"
            "  • Double-Sided Hammering         : Squeezing the victim row between TWO\n"
            "    aggressor rows (Row N-1 and Row N+1) causes cumulative electrical leakage,\n"
            "    dramatically accelerating bit-flips compared to single-sided attacks.\n\n"
            "========================================================================\n"
            " 3. HOW THE ATTACKER EXPLOITS A BIT-FLIP (PRIVILEGE ESCALATION)\n"
            "========================================================================\n"
            "A bit-flip causes random data corruption—how does an attacker gain root/admin?\n\n"
            "• The Google Project Zero Page Table Entry (PTE) Exploit:\n"
            "  1. Memory Spraying: The attacker process allocates millions of Page Table\n"
            "     Entries (PTEs) across physical memory until one lands in the victim row.\n"
            "  2. Rowhammer Trigger: The attacker hammers adjacent rows until a bit flips\n"
            "     inside the Physical Page Number (PPN) field or U/S permission bit.\n"
            "  3. Kernel Takeover: The flipped bit causes the attacker's virtual page to\n"
            "     point directly to a physical page table itself! The unprivileged user\n"
            "     can now write directly to page tables, granting arbitrary read/write access\n"
            "     to ALL physical RAM, completely bypassing OS kernel protection (Ring 0)!\n"
        )
        text_box.insert("1.0", tech_doc)
        text_box.config(state="disabled")

        tk.Button(dialog, text="Close Deep Dive", command=dialog.destroy, bg="#1e293b", fg="white", font=("Arial", 10)).pack(pady=(0, 10))

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

    def show_grand_victory_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("🏆 MISSION ACCOMPLISHED - Kitchen Espionage Cleared!")
        popup.geometry("640x520")
        popup.configure(bg="#070b14")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        header = tk.Frame(popup, bg="#0f172a", pady=15)
        header.pack(fill="x")

        tk.Label(header, text="🎉 CONGRATULATIONS, AGENT! 🎉", bg="#0f172a", fg="#facc15", font=("Consolas", 15, "bold")).pack()
        tk.Label(header, text="You have mastered Microarchitectural Exploits & Computer Architecture!", bg="#0f172a", fg="#cbd5e1", font=("Arial", 9)).pack()

        body = tk.Frame(popup, bg="#070b14", padx=25, pady=15)
        body.pack(fill="both", expand=True)

        summary_text = (
            "🏆 ALL 3 MISSION LEVELS SUCCESSFULLY COMPLETED:\n\n"
            "✔ PART 1: FLUSH+RELOAD CACHE SIDE-CHANNEL ATTACK\n"
            "   You evicted cache lines with clflush, calibrated rdtsc cycle thresholds,\n"
            "   and successfully extracted shared secret memory through timing footprints.\n\n"
            "✔ PART 2: 5-STAGE CPU PIPELINING & THE MEMORY WALL\n"
            "   You analyzed the RISC datapath (IF, DE, EX, ME, WB), observed multi-tier\n"
            "   memory latencies (L1, L2, DRAM), and calculated the 9.0s pipeline delay.\n\n"
            "✔ PART 3: DOUBLE-SIDED ROWHAMMER DRAM ATTACK\n"
            "   You bypassed OS kernel memory isolation by hammering flanking wordlines,\n"
            "   inducing capacitive crosstalk, and triggering a Page Table Entry bit-flip!\n\n"
            "You are now ready to analyze, exploit, and defend real-world computer systems."
        )
        tk.Label(body, text=summary_text, bg="#070b14", fg="#ecf0f1", font=("Consolas", 9), justify="left").pack(anchor="w")

        btn_exit = tk.Button(popup, text="Exit Kitchen Espionage", command=lambda: [stop_bgm(), self.root.destroy()], bg="#ef4444", fg="white", font=("Arial", 11, "bold"), pady=6, padx=15)
        btn_exit.pack(pady=(0, 15))

if __name__ == "__main__":
    root = tk.Tk()
    app = RowhammerKitchenGUI(root)
    root.mainloop()
