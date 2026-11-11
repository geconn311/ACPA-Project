# ACPA-Project: Kitchen Espionage

An interactive, visual educational suite designed to teach undergraduate computer architecture and microarchitectural security vulnerabilities using an intuitive kitchen hardware analogy.

The project translates complex hardware concepts—cache side-channel attacks, CPU pipelining with multi-level cache latency, and DRAM disturbance errors—into a multi-level graphical game.

---

## 🚀 Quickstart & How to Run

The entire 3-part sequence runs seamlessly from the workspace root using Python's standard library:

```bash
python main.py
```

*Each level automatically transitions to the next upon completion. Individual parts can also be run directly if desired.*

---

## 🛠️ Technologies & Tools Used

- **Language:** Python 3.6+
- **GUI Framework:** **Tkinter** (`Canvas`, `PhotoImage`, `messagebox`, `Spinbox`, `Frame`, etc.) — chosen to provide a lightweight, cross-platform graphical interface with zero external dependencies (no Pygame or third-party packages required).
- **Process Orchestration:** Python's built-in **`subprocess`**, **`os`**, and **`sys`** modules to coordinate seamless level-to-level transitions and robust relative asset path resolution.
- **Microarchitectural Simulators:**
  - Discrete timing measurement and cache state mapping (`time`).
  - Instruction decoding and 5-stage CPU cycle advancement (`IF`, `DE`, `EX`, `ME`, `WB`).
  - Stochastic bit-flip disturbance modeling (`random`).
- **Audio System:** Native Windows MCI multimedia playback (`ctypes.windll.winmm`) playing the classic Club Penguin Pizza Parlor restaurant music across all levels, with in-game `🔊 Music: ON` / `🔇 Music: OFF` controls and zero external audio package dependencies.
- **Visual Assets:** Custom sprites (`chef.png`, `counter.png`, `freezer.png`) integrated into dynamic Tkinter canvas animations.

---

## 📋 Summary of Levels

### 🔪 Part 1: Flush+Reload Cache Side-Channel Attack
- **File:** [`Part 1/kitchen_espionage_part1.py`](Part%201/kitchen_espionage_part1.py)
- **Concept:** Timing-based microarchitectural side-channel attack (Flush+Reload).
- **The Hardware Analogy:**
  - **Prep Counter** = **L1 Cache (SRAM):** Fast, low-latency access (~0.06s).
  - **Walk-In Freezer** = **Main Memory (DRAM):** Slow, high-latency access (~1.8s).
  - **Chef** = **CPU** executing memory fetch instructions.
  - **VIP Order** = **Victim's Secret Data:** 6 secret ingredients selected from 20 memory addresses (0–19).
- **Attack Flow:**
  1. **Flush:** Clear the prep counter so no stale data remains cached.
  2. **Trigger Victim:** The victim loads their 6 secret ingredients into the L1 cache.
  3. **Probe / Reload:** Measure fetch latencies across addresses 0 through 19 within an **18-probe budget**. A fast access (<0.1s) indicates a **Cache Hit** (the victim used it); a slow access (>1.0s) indicates a **Cache Miss**.
  4. **Submit Attack:** Submit the 6 identified secret numbers to steal the recipe and advance to Part 2.

---

### ⏱️ Part 2: 5-Stage CPU Pipeline & Cache Latency Simulation
- **File:** [`Part 2/kitchen_espionage_part2.py`](Part%202/kitchen_espionage_part2.py)
- **Concept:** Classical RISC 5-stage instruction pipelining and memory hierarchy bottlenecks.
- **The Hardware Analogy:**
  - **Prep Counter** = **L1 Cache:** 1.0s latency (addresses 5, 11, 14).
  - **Kitchen Pantry** = **L2 Cache:** 3.0s latency (addresses 2, 6, 8, 12, 13, 16, 19).
  - **Walk-In Freezer** = **Main Memory (DRAM):** 5.0s latency (all other addresses).
  - **Chef** = Moves to the active storage tier during memory access (`ME`) stages.
- **Pipeline Mechanics:**
  - Reads assembly instructions (`lw`, `add`, `sub`, `or`) from [`Part 2/ACPAtext.txt`](Part%202/ACPAtext.txt).
  - Simulates the 5 pipeline stages concurrently:
    - **IF** (Instruction Fetch) ➜ **DE** (Instruction Decode) ➜ **EX** (Execute / ALU) ➜ **ME** (Memory Access) ➜ **WB** (Register Writeback).
  - Features real-time register monitoring (`PC`, `r1`, `r2`, `r3`), cycle-by-cycle manual stepping, and automatic run modes.
  - Completing all instructions through writeback automatically triggers Part 3.

---

### 🔨 Part 3: Rowhammer DRAM Disturbance Attack
- **File:** [`Part 3/kitchen_espionage_level3.py`](Part%203/kitchen_espionage_level3.py)
- **Concept:** Physical DRAM electrical disturbance and unauthorized bit-flips via Double-Sided Rowhammering.
- **The Hardware Analogy:**
  - **Freezer Shelves** = **DRAM Bank Rows.**
  - **Accessible Rows** = Even rows (2, 4, 6... 18) that the attacker has permission to access.
  - **Target Row** = An inaccessible odd row (3, 5, 7... 17) containing protected data ("The Security Access List").
  - **Double-Sided Hammering** = Rapid, alternating activations of **both** even rows flanking the target odd row (`T - 1` and `T + 1`) induce intense electrical disturbance (25% bit-flip drop rate). Single-sided hammering produces only mild vibrations.
- **Gameplay:**
  - Probe even rows (2–18) until single-sided vibrations reveal an adjacent row.
  - Deduce the second flanking row and execute double-sided hammering to dislodge the Security Access List.
  - Verify with the Head Chef once the list drops.
  - Must succeed before the **26-action budget** expires.
  - Upon clearing Level 3, a **Grand Victory Celebration Popup** summarizes all achievements across the 3 parts and provides options to replay Part 3, restart the full mission from Part 1, or exit cleanly.
