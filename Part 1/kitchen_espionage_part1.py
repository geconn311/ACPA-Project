import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
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
        self.root.title("Kitchen Espionage - Flush+Reload Attack")
        self.root.geometry("650x550")
        self.root.configure(bg="#2c3e50")

        # Core Game State
        self.all_ingredients = list(range(10))
        self.secret_ingredients = random.sample(self.all_ingredients, 4)
        
        # The cache state (what is currently on the prep counter)
        # We start it with random garbage to force the student to "Flush" it first
        self.prep_counter = random.sample(self.all_ingredients, 6)

        # --- 1. VISUAL CANVAS ---
        self.canvas = tk.Canvas(root, width=600, height=200, bg="#ecf0f1", highlightthickness=0)
        self.canvas.pack(pady=10)

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Draw Freezer (Main Memory) - Right
        self.freezer = PhotoImage(file=os.path.join(script_dir, "freezer.png"))
        self.canvas.create_image(450, 100, image=self.freezer, tags="freezer")

        # Draw Prep Counter (L1 Cache) - Left
        self.counter = PhotoImage(file=os.path.join(script_dir, "counter.png"))
        self.canvas.create_image(130, 150, image=self.counter, tags="counter")

        # Draw the Chef
        self.chef = PhotoImage(file=os.path.join(script_dir, "chef.png"))
        self.chef = self.chef.subsample(2, 2)
        self.canvas.create_image(85, 50, image=self.chef, tags="chef")

        # Audio Setup
        self.music_on = True
        self.music_path = os.path.join(script_dir, "restaurant_music.mp3")
        if os.path.exists(self.music_path):
            start_bgm(self.music_path)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- 2. STATUS HUD ---
        self.status_label = tk.Label(root, text="System Ready. Waiting for attacker action...", bg="#2c3e50", fg="#f1c40f", font=("Arial", 11, "bold"))
        self.status_label.pack(pady=5)
        
        self.timer_label = tk.Label(root, text="Last Fetch Latency: -- s", bg="#2c3e50", fg="white", font=("Arial", 12))
        self.timer_label.pack()

        # --- 3. INTERACTIVE CONTROL PANEL ---
        control_frame = tk.Frame(root, bg="#34495e", bd=2, relief="groove", padx=10, pady=10)
        control_frame.pack(pady=10, fill="x", padx=20)
        
        header_frame = tk.Frame(control_frame, bg="#34495e")
        header_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="ew")
        tk.Label(header_frame, text="ATTACKER CONTROL PANEL", bg="#34495e", fg="white", font=("Arial", 12, "bold")).pack(side="left")
        self.btn_help = tk.Button(header_frame, text="📋 Instructions", command=self.show_instructions, bg="#16a085", fg="white", font=("Arial", 9, "bold"))
        self.btn_help.pack(side="right")
        self.btn_audio = tk.Button(header_frame, text="🔊 Music: ON", command=self.toggle_music, bg="#2980b9", fg="white", font=("Arial", 9, "bold"))
        self.btn_audio.pack(side="right", padx=(0, 6))

        # Phase 1: Flush
        self.btn_flush = tk.Button(control_frame, text="1. Flush Cache (Clear Counter)", command=self.flush_cache, bg="#e67e22", fg="white", width=30)
        self.btn_flush.grid(row=1, column=0, pady=5, padx=5, sticky="w")
        tk.Label(control_frame, text="Evicts all data from L1 to Main Memory.", bg="#34495e", fg="#bdc3c7").grid(row=1, column=1, sticky="w")

        # Phase 2: Victim Execution
        self.btn_victim = tk.Button(control_frame, text="2. Trigger Victim (Prep VIP Order)", command=self.trigger_victim, bg="#9b59b6", fg="white", width=30)
        self.btn_victim.grid(row=2, column=0, pady=5, padx=5, sticky="w")
        tk.Label(control_frame, text="Victim loads the 4 secret items into L1.", bg="#34495e", fg="#bdc3c7").grid(row=2, column=1, sticky="w")

        # Phase 3: Probe/Reload
        probe_frame = tk.Frame(control_frame, bg="#34495e")
        probe_frame.grid(row=3, column=0, pady=5, padx=5, sticky="w")
        tk.Label(probe_frame, text="3. Probe Ingredient (0-9):", bg="#34495e", fg="white").pack(side="left")
        
        self.probe_spinbox = tk.Spinbox(probe_frame, from_=0, to=9, width=5, font=("Arial", 10))
        self.probe_spinbox.pack(side="left", padx=5)
        
        self.btn_probe = tk.Button(probe_frame, text="Measure Latency", command=self.probe_ingredient, bg="#3498db", fg="white")
        self.btn_probe.pack(side="left")
        tk.Label(control_frame, text="Time the fetch to map the cache state.", bg="#34495e", fg="#bdc3c7").grid(row=3, column=1, sticky="w")

        # Phase 4: Submit Attack
        submit_frame = tk.Frame(root, bg="#2c3e50")
        submit_frame.pack(pady=10)
        tk.Label(submit_frame, text="Enter 4 VIP Ingredients (e.g., 0 3 5 8):", bg="#2c3e50", fg="white", font=("Arial", 11)).pack(side="left")
        self.guess_entry = tk.Entry(submit_frame, width=15, font=("Arial", 12))
        self.guess_entry.pack(side="left", padx=10)
        self.btn_submit = tk.Button(submit_frame, text="SUBMIT ATTACK", command=self.verify_attack, bg="#2ecc71", fg="white", font=("Arial", 10, "bold"))
        self.btn_submit.pack(side="left")


    # --- ATTACK STATE MACHINE METHODS ---

    def flush_cache(self):
        """Phase 1: Clear the prep counter."""
        self.prep_counter.clear()
        self.status_label.config(text="Cache Flushed: Prep counter is now empty.")
        self.timer_label.config(text="Last Fetch Latency: -- s")

    def trigger_victim(self):
        """Phase 2: Victim loads their secrets into the cache."""
        # The victim puts their specific ingredients on the counter
        for item in self.secret_ingredients:
            if item not in self.prep_counter:
                self.prep_counter.append(item)
        for _ in range(40):
            self.canvas.move("chef", 10, 0)
            self.root.update()
            time.sleep(0.02)
        for _ in range(40):
            self.canvas.move("chef", -10, 0)
            self.root.update()
            time.sleep(0.02)
        self.status_label.config(text="Victim Executed: VIP order placed on prep counter.")

    def probe_ingredient(self):
        """Phase 3: The attacker measures the time it takes to fetch an ingredient."""
        try:
            ingredient_id = int(self.probe_spinbox.get())
        except ValueError:
            return

        if ingredient_id not in self.all_ingredients:
            return

        self._set_ui_state("disabled")
        start_time = time.time()

        if ingredient_id in self.prep_counter:
            self.status_label.config(text=f"Probing {ingredient_id}... Found on Prep Counter (Hit)!")
            # Cache Hit Animation (Short vertical hop)
            for _ in range(5):
                self.canvas.move("chef", 0, -5)
                self.root.update()
                time.sleep(0.03)
            for _ in range(5):
                self.canvas.move("chef", 0, 5)
                self.root.update()
                time.sleep(0.03)
                
            elapsed = time.time() - start_time
            self.timer_label.config(text=f"Last Fetch Latency: {elapsed:.3f} s (FAST)")

        else:
            self.status_label.config(text=f"Probing {ingredient_id}... Fetching from Freezer (Miss)!")
            # Cache Miss Animation (Long horizontal walk)
            for _ in range(40):
                self.canvas.move("chef", 10, 0)
                self.root.update()
                time.sleep(0.02)
                
            time.sleep(0.3) # Simulate grabbing the item
            
            for _ in range(40):
                self.canvas.move("chef", -10, 0)
                self.root.update()
                time.sleep(0.02)
                
            elapsed = time.time() - start_time
            self.timer_label.config(text=f"Last Fetch Latency: {elapsed:.3f} s (SLOW)")
            
            # The item is now cached because the attacker fetched it
            self.prep_counter.append(ingredient_id)

        self._set_ui_state("normal")

    def verify_attack(self):
        """Phase 4: Verify the student's submission."""
        guess_str = self.guess_entry.get().strip()
        try:
            # Parse the user's string into a list of integers
            user_guess = sorted([int(x) for x in guess_str.replace(",", " ").split()])
        except ValueError:
            messagebox.showerror("Error", "Please enter 4 numbers separated by spaces.")
            return

        secret = sorted(self.secret_ingredients)
        
        if user_guess == secret:
            self.status_label.config(text="ACCESS GRANTED! Secret extracted successfully.", fg="#2ecc71")
            messagebox.showinfo(
                "Victory!", 
                f"Part 1 Cleared!\nYou successfully mapped the cache and extracted the VIP order: {secret}\n\nClick OK to start Part 2 (CPU Pipeline Simulation)!"
            )
            self.root.destroy()
            self.launch_part_2()
        else:
            self.status_label.config(text="ACCESS DENIED! Wrong recipe.", fg="#e74c3c")
            messagebox.showerror("Failed", "Access Denied.\nThe timing footprint does not match the VIP's order. Try flushing the cache and measuring again.")

    def launch_part_2(self):
        """Launches Part 2 (kitchen_espionage_part2.py) once Part 1 is successfully completed."""
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
            self.btn_audio.config(text="🔇 Music: OFF", bg="#7f8c8d")
        else:
            if os.path.exists(self.music_path):
                start_bgm(self.music_path)
            self.music_on = True
            self.btn_audio.config(text="🔊 Music: ON", bg="#2980b9")

    def _on_close(self):
        stop_bgm()
        self.root.destroy()

    def show_instructions(self):
        """Displays interactive mission instructions in a dialog."""
        msg = (
            "🎯 MISSION OBJECTIVE:\n"
            "Extract the 4 secret VIP ingredients (chosen from 0-9) using a Flush+Reload cache attack!\n\n"
            "⚙️ HARDWARE ANALOGY:\n"
            "• Prep Counter = L1 Cache (Fast, low-latency access)\n"
            "• Walk-In Freezer = Main Memory (Slow DRAM, high-latency access)\n"
            "• Chef = CPU executing memory fetch operations\n\n"
            "📋 4 ATTACK STEPS:\n"
            "1. Flush Cache: Clear the prep counter so no stale data is cached.\n"
            "2. Trigger Victim: VIP loads their 4 secret ingredients onto the prep counter.\n"
            "3. Measure Latency: Test ingredients 0 through 9 one by one:\n"
            "   - FAST latency (< 0.1s) -> CACHE HIT! This is a secret VIP ingredient!\n"
            "   - SLOW latency (> 1.0s) -> CACHE MISS! Not ordered by VIP (fetched from freezer).\n"
            "4. Submit Attack: Enter the 4 FAST numbers (e.g. '1 3 5 8') and click SUBMIT ATTACK!"
        )
        messagebox.showinfo("Part 1 - Mission Briefing & Instructions", msg)

    def _set_ui_state(self, state):
        self.btn_flush.config(state=state)
        self.btn_victim.config(state=state)
        self.btn_probe.config(state=state)
        self.btn_submit.config(state=state)


if __name__ == "__main__":
    root = tk.Tk()
    app = InteractiveKitchen(root)
    root.mainloop()