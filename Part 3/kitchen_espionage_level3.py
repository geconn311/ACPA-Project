import tkinter as tk
from tkinter import messagebox
from tkinter import PhotoImage
import os
import random
import time

class RowhammerKitchenGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kitchen Espionage - Part 3 (Rowhammer Attack)")
        self.root.geometry("700x660")
        self.root.configure(bg="#2c3e50")

        self.pantry_pool = [
            "Box of pasta", "Bottle of olive oil", "Canned tomatoes", "Garlic cloves",
            "Bag of rice", "Black pepper shaker", "A jar of honey", "Bag of flour",
            "Box of salt", "Salt shaker", "Soy sauce bottle", "Vinegar bottle",
            "Dried oregano", "Butter block", "Milk carton", "Cheddar wedge", "Bag of sugar"
        ]

        self._init_game_state()

        script_dir = os.path.dirname(os.path.abspath(__file__))

        # --- 1. VISUAL CANVAS ---
        self.canvas = tk.Canvas(root, width=660, height=200, bg="#ecf0f1", highlightthickness=0)
        self.canvas.pack(pady=10)

        # Draw Walk-In Freezer / Shelf Rack - Right
        self.freezer = PhotoImage(file=os.path.join(script_dir, "freezer.png"))
        self.canvas.create_image(520, 100, image=self.freezer, tags="freezer")

        # Draw Prep Counter - Left
        self.counter = PhotoImage(file=os.path.join(script_dir, "counter.png"))
        self.canvas.create_image(120, 150, image=self.counter, tags="counter")

        # Draw Chef Sprite
        self.chef = PhotoImage(file=os.path.join(script_dir, "chef.png"))
        self.chef = self.chef.subsample(2, 2)
        self.canvas.create_image(250, 70, image=self.chef, tags="chef")

        # --- 2. STATUS HUD ---
        self.actions_label = tk.Label(
            root, 
            text="Actions Remaining: 35 / 35", 
            bg="#2c3e50", 
            fg="#2ecc71", 
            font=("Arial", 13, "bold")
        )
        self.actions_label.pack(pady=3)

        self.status_label = tk.Label(
            root, 
            text="System Ready. Select an accessible even row (2-18) to hammer.", 
            bg="#2c3e50", 
            fg="#f1c40f", 
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(pady=2)

        self.feedback_label = tk.Label(
            root, 
            text="The secret security access list is sitting on an odd shelf...", 
            bg="#2c3e50", 
            fg="#ecf0f1", 
            font=("Arial", 10, "italic")
        )
        self.feedback_label.pack(pady=2)

        # --- 3. ATTACKER CONTROL PANEL ---
        ctrl_frame = tk.Frame(root, bg="#34495e", bd=2, relief="groove", padx=15, pady=12)
        ctrl_frame.pack(pady=10, fill="x", padx=20)

        header_frame = tk.Frame(ctrl_frame, bg="#34495e")
        header_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            header_frame, 
            text="ROWHAMMER CONTROL PANEL", 
            bg="#34495e", 
            fg="white", 
            font=("Arial", 12, "bold")
        ).pack(side="left")

        self.btn_help = tk.Button(
            header_frame, 
            text="📋 Instructions", 
            command=self.show_instructions, 
            bg="#16a085", 
            fg="white", 
            font=("Arial", 9, "bold")
        )
        self.btn_help.pack(side="right")

        # Row Selection & Hammer Action
        hammer_frame = tk.Frame(ctrl_frame, bg="#34495e")
        hammer_frame.pack(fill="x", pady=6)

        tk.Label(
            hammer_frame, 
            text="Target Even Row (2-18):", 
            bg="#34495e", 
            fg="white", 
            font=("Arial", 10)
        ).pack(side="left")

        self.row_var = tk.StringVar(value="2")
        self.row_spinbox = tk.Spinbox(
            hammer_frame, 
            values=self.accessible_rows, 
            textvariable=self.row_var, 
            width=6, 
            font=("Arial", 10, "bold"),
            state="readonly"
        )
        self.row_spinbox.pack(side="left", padx=10)

        self.btn_hammer = tk.Button(
            hammer_frame, 
            text="🔨 Hammer Selected Row", 
            command=self.hammer_row, 
            bg="#e67e22", 
            fg="white", 
            font=("Arial", 10, "bold")
        )
        self.btn_hammer.pack(side="left", padx=10)

        tk.Label(
            hammer_frame, 
            text="(-1 Action)", 
            bg="#34495e", 
            fg="#bdc3c7", 
            font=("Arial", 9)
        ).pack(side="left")

        # Verify Action
        verify_frame = tk.Frame(ctrl_frame, bg="#34495e")
        verify_frame.pack(fill="x", pady=8)

        self.btn_check = tk.Button(
            verify_frame, 
            text="👨‍🍳 Ask Head Chef to Verify Access", 
            command=self.check_chef, 
            bg="#3498db", 
            fg="white", 
            font=("Arial", 10, "bold")
        )
        self.btn_check.pack(side="left")

        tk.Label(
            verify_frame, 
            text="Check if the access list fell. (-3 Actions penalty if wrong)", 
            bg="#34495e", 
            fg="#bdc3c7", 
            font=("Arial", 9)
        ).pack(side="left", padx=10)

        # Reset button
        self.btn_reset = tk.Button(
            ctrl_frame, 
            text="🔄 Restart Level", 
            command=self.reset_level, 
            bg="#7f8c8d", 
            fg="white", 
            font=("Arial", 9)
        )
        self.btn_reset.pack(anchor="w", pady=(8, 0))

        # --- 4. ROW ACCESS VISUAL INDICATOR ---
        shelf_frame = tk.LabelFrame(
            root, 
            text="FREEZER RACK ACCESS MAP", 
            bg="#34495e", 
            fg="#bdc3c7", 
            font=("Arial", 9, "bold"), 
            padx=10, 
            pady=8
        )
        shelf_frame.pack(pady=8, fill="x", padx=20)

        self.shelf_indicators = {}
        for r in range(1, 21):
            is_accessible = (r % 2 == 0)
            color = "#27ae60" if is_accessible else "#7f8c8d"
            text = f"R{r}" if is_accessible else f"R{r}🔒"
            lbl = tk.Label(
                shelf_frame, 
                text=text, 
                bg=color, 
                fg="white", 
                font=("Arial", 8, "bold"), 
                width=4, 
                padx=2, 
                pady=2
            )
            lbl.grid(row=0 if r <= 10 else 1, column=(r - 1) % 10, padx=3, pady=2)
            self.shelf_indicators[r] = lbl

    def _init_game_state(self):
        self.shelves = {}
        for i in range(1, 21):
            self.shelves[i] = random.sample(self.pantry_pool, k=random.randint(2, 4))

        valid_targets = [i for i in range(1, 20, 2)]
        self.target_row = random.choice(valid_targets)
        self.shelves[self.target_row].append("The Security Access List")

        self.accessible_rows = [i for i in range(2, 20, 2)]
        self.actions_remaining = 35
        self.access_list_fallen = False
        self.game_over = False

    def reset_level(self):
        self._init_game_state()
        self.actions_label.config(text="Actions Remaining: 35 / 35", fg="#2ecc71")
        self.status_label.config(text="Level restarted. Select an even row to hammer.", fg="#f1c40f")
        self.feedback_label.config(text="The secret security access list is sitting on an odd shelf...", fg="#ecf0f1")
        self.btn_hammer.config(state="normal")
        self.btn_check.config(state="normal")
        self.canvas.coords("chef", 250, 70)

    def hammer_row(self):
        if self.game_over or self.actions_remaining <= 0:
            return

        try:
            row_chosen = int(self.row_var.get())
        except ValueError:
            return

        if row_chosen not in self.accessible_rows:
            self.status_label.config(text=f"Access Denied! You cannot reach Row {row_chosen}.", fg="#e74c3c")
            return

        self.actions_remaining -= 1
        self._update_actions_hud()

        # Animate chef hammering the freezer shelf
        self._animate_hammer()

        self.status_label.config(
            text=f"Aggressively pulling and restocking items from Row {row_chosen}...", 
            fg="#f39c12"
        )

        # Check adjacency to target row
        if abs(row_chosen - self.target_row) == 1:
            target_items = self.shelves[self.target_row]
            fallen_this_turn = []

            for item in target_items[:]:
                if random.random() < 0.10:
                    target_items.remove(item)
                    fallen_this_turn.append(item)

            if fallen_this_turn:
                dropped_names = []
                for item in fallen_this_turn:
                    if "Access List" in item:
                        self.access_list_fallen = True
                        dropped_names.append("THE SECURITY ACCESS LIST 📄")
                    else:
                        dropped_names.append(item)

                if self.access_list_fallen:
                    self.feedback_label.config(
                        text=f"💥 RACK DISTURBANCE! Papers rustled... {', '.join(dropped_names)} fell to the floor!", 
                        fg="#2ecc71"
                    )
                else:
                    self.feedback_label.config(
                        text=f"💥 *CLATTER* {', '.join(dropped_names)} slipped off an adjacent shelf!", 
                        fg="#e67e22"
                    )
            else:
                self.feedback_label.config(
                    text="⚡ Strong vibrations sent to neighboring shelf, but nothing broke loose this turn.", 
                    fg="#f1c40f"
                )
        else:
            self.feedback_label.config(
                text=f"A dull thud echoes from Row {row_chosen}. Too far away to disturb sensitive shelves.", 
                fg="#bdc3c7"
            )

        self._check_failure()

    def check_chef(self):
        if self.game_over:
            return

        self.actions_remaining -= 3
        self._update_actions_hud()

        # Animate chef walking to the left to talk to Head Chef
        self._animate_chef_check()

        if self.access_list_fallen:
            self.game_over = True
            self.status_label.config(text="ACCESS GRANTED! You win!", fg="#2ecc71")
            self.feedback_label.config(
                text="The Chef notices the access list on the floor and unlocks the pantry!", 
                fg="#2ecc71"
            )
            messagebox.showinfo(
                "VICTORY!", 
                "🎉 Mission Accomplished!\n\n"
                "The Head Chef opens the ledger and gasps:\n"
                "'Wait... the access list is missing from the shelf! It must have fallen off.'\n\n"
                "The Chef unlocks the pantry door. You have successfully cleared Level 3 and mastered Rowhammer!"
            )
            self.btn_hammer.config(state="disabled")
            self.btn_check.config(state="disabled")
        else:
            self.status_label.config(text="Verification Failed!", fg="#e74c3c")
            self.feedback_label.config(
                text="The Chef checks: 'The access list is right here where it belongs! Get back to work!' (-3 Actions)", 
                fg="#e74c3c"
            )
            self._check_failure()

    def _animate_hammer(self):
        # Move towards freezer and shake
        self.canvas.coords("chef", 420, 70)
        self.root.update()
        for _ in range(3):
            self.canvas.move("chef", 4, 0)
            self.root.update()
            time.sleep(0.03)
            self.canvas.move("chef", -4, 0)
            self.root.update()
            time.sleep(0.03)

    def _animate_chef_check(self):
        # Move towards prep counter
        self.canvas.coords("chef", 160, 70)
        self.root.update()
        time.sleep(0.15)

    def _update_actions_hud(self):
        rem = max(0, self.actions_remaining)
        color = "#2ecc71" if rem > 15 else "#f39c12" if rem > 5 else "#e74c3c"
        self.actions_label.config(text=f"Actions Remaining: {rem} / 35", fg=color)

    def _check_failure(self):
        if self.actions_remaining <= 0 and not self.game_over:
            self.game_over = True
            self.status_label.config(text="--- INVENTORY RESET ---", fg="#e74c3c")
            self.feedback_label.config(
                text="The Prep Cook walked in and restocked the shelves! Progress wiped.", 
                fg="#e74c3c"
            )
            messagebox.showerror(
                "Game Over", 
                "Out of Actions!\n\n"
                "The Prep Cook walks in, sees the disturbed shelves, and resets everything.\n"
                "Your progress has been wiped out. Click 'Restart Level' to try again!"
            )
            self.btn_hammer.config(state="disabled")
            self.btn_check.config(state="disabled")

    def show_instructions(self):
        msg = (
            "🎯 MISSION OBJECTIVE (ROWHAMMER ATTACK):\n"
            "Gain access to the locked pantry by knocking the Security Access List off an odd shelf.\n\n"
            "⚙️ HARDWARE ANALOGY:\n"
            "• Freezer Rack = DRAM Bank rows.\n"
            "• Accessible Rows = Memory rows you have permission to access (Even rows 2, 4, 6... 18).\n"
            "• Target Row = An adjacent protected DRAM row containing sensitive data (Odd rows 1, 3, 5... 19).\n"
            "• Hammering = Repeated rapid activations of an adjacent row induce electrical disturbance (vibrations) causing bit-flips (falling items)!\n\n"
            "📋 HOW TO PLAY:\n"
            "1. Select an even row (2-18) from the dropdown/spinbox.\n"
            "2. Click '🔨 Hammer Selected Row'. If it is adjacent to the target row (±1 distance), vibrations shake items off the neighboring shelf.\n"
            "3. Watch the feedback label for clatters or fluttering papers.\n"
            "4. When you believe the Security Access List has fallen, click '👨‍🍳 Ask Head Chef to Verify Access'.\n"
            "5. BEWARE: You have 35 actions total. Failed checks cost 3 actions penalty. If actions reach 0, the Prep Cook resets the shelves!"
        )
        messagebox.showinfo("Part 3 - Mission Briefing & Instructions", msg)


def run_rowhammer_level():
    root = tk.Tk()
    app = RowhammerKitchenGUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_rowhammer_level()
