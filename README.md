# ACPA-Project: Kitchen Espionage

An interactive, visual educational suite designed to teach undergraduate computer architecture and microarchitectural security vulnerabilities using an intuitive kitchen hardware analogy paired with in-depth technical hardware deep dives.

The project translates complex hardware concepts—cache side-channel attacks, CPU pipelining with multi-level cache latency, and DRAM disturbance errors—into a multi-level graphical game available both as a **live web app on GitHub Pages** and as a **native Python desktop suite**.

---

## 🌐 Play Live on GitHub Pages (Zero Install)

The entire educational suite is ready to run directly in any web browser with **zero installation or downloads**:

👉 **[Launch Kitchen Espionage on GitHub Pages](https://geconn311.github.io/ACPA-Project/)**

*(To enable on your own repository: Go to `Settings` &rarr; `Pages` &rarr; Source: `Deploy from a branch` &rarr; Select `main` and `/ (root)` &rarr; Save).*

---

## 🚀 Desktop Quickstart & How to Run (Python)

The entire 3-part sequence also runs natively from the workspace root using Python's standard library:

```bash
python main.py
```

*Each level automatically transitions to the next upon completion. Individual parts can also be run directly if desired.*

---

## 🧩 Two-Section Structure: Intuition & Deep Technical Rigor

Every part of Kitchen Espionage is split into two complementary sections:
- **Section A (Kitchen Espionage Analogy):** Visual, gamified simulation where students interact with kitchen storage tiers (Prep Counter, Pantry, Walk-In Freezer) to build intuitive understanding.
- **Section B (Hardware Architecture Deep Dive):** Rigorous technical explanations, assembly/C snippets (`clflush`, `rdtsc`, `mfence`), semiconductor physics (DRAM capacitive coupling), real-world exploit pathways (Page Table Entry overwriting), and interactive critical thinking checkpoints that students must solve.

---

## 🛠️ Technologies & Tools Used

- **Web Deployment:** Pure HTML5 Canvas, modern responsive CSS, and native JavaScript single-page application (`index.html`), optimized for GitHub Pages with zero external dependencies.
- **Desktop GUI:** **Tkinter** (`Canvas`, `PhotoImage`, `messagebox`, `Spinbox`, `Frame`, etc.) using Python 3 standard libraries.
- **Audio Engine:** Background looping playback of the classic Club Penguin Pizza Parlor music (`restaurant_music.mp3`) at 10% volume, with in-game mute and volume controls. Implemented natively in Python via Windows MCI (`ctypes.windll.winmm`) and in the browser via the HTML5 Audio API.
- **Visual Assets:** Custom sprites (`chef.png`, `counter.png`, `freezer.png`) integrated into dynamic canvas animations across all pipeline stages.

---

## 📋 Detailed Summary of Levels

### 🔪 Part 1: Flush+Reload Cache Side-Channel Attack
- **Desktop File:** [`Part 1/kitchen_espionage_part1.py`](Part%201/kitchen_espionage_part1.py) | **Web Tab:** Part 1
- **Concept:** Timing-based microarchitectural side-channel attack (Flush+Reload).
- **The Hardware Analogy (Section A):**
  - **Prep Counter** = **L1 Cache (SRAM):** Fast, low-latency access (~0.06s).
  - **Walk-In Freezer** = **Main Memory (DRAM):** Slow, high-latency access (~1.8s).
  - **Chef** = **CPU** executing memory fetch instructions.
  - **VIP Order** = **Victim's Secret Data:** 6 secret ingredients selected from 20 memory addresses (0–19).
- **Hardware Deep Dive (Section B):**
  - **How 'Clearing the Counter' Works:** In x86, user processes execute `clflush [address]` to evict the 64-byte line across L1, L2, and shared L3/LLC back to DRAM. On architectures without unprivileged flush, attackers use **Evict+Reload** via memory eviction sets that force lines out via hardware LRU replacement.
  - **Shared Memory:** Explains how OS page deduplication (KSM) and shared libraries (`libcrypto.so`) map both victim and attacker to the exact same physical DRAM frame.
  - **Timing Measurement:** Explains `rdtsc` timestamp counters and serialization barriers (`mfence`, `lfence`).
- **Gameplay:** Flush the counter, trigger the VIP order, probe addresses within an **18-probe budget**, identify the 6 fast cache hits (<0.1s), and submit the recipe.

---

### ⏱️ Part 2: 5-Stage CPU Pipeline & Cache Latency Simulation
- **Desktop File:** [`Part 2/kitchen_espionage_part2.py`](Part%202/kitchen_espionage_part2.py) | **Web Tab:** Part 2
- **Concept:** Classical RISC 5-stage instruction pipelining and the Von Neumann Memory Wall.
- **The Hardware Analogy (Section A):**
  - **Prep Counter** = **L1 Cache:** 1.0s latency (addresses 5, 11, 14).
  - **Kitchen Pantry** = **L2 Cache:** 3.0s latency (addresses 2, 6, 8, 12, 13, 16, 19).
  - **Walk-In Freezer** = **Main Memory (DRAM):** 5.0s latency (all other addresses).
  - **Stage Highlights:** Real-time visual box glowing for `IF` (Fetch), `DE` (Decode), `EX` (Execute), `ME` (Memory), and `WB` (Writeback), with the chef walking to the corresponding storage station during memory phases.
- **Hardware Deep Dive & Anti-Bypass Checkpoint (Section B):**
  - **No Autoplay Skip:** Students **cannot simply press Auto Run to bypass Part 2**!
  - **Mandatory Calculation Checkpoint:** To advance to Part 3, students must calculate the cumulative storage latency ($1.0\text{s} + 3.0\text{s} + 5.0\text{s} = 9.0\text{s}$) and identify why the `ME` stage causes pipeline bubbles due to the **Memory Wall** (CPU logic at GHz speeds vs off-chip DRAM taking hundreds of cycles).

---

### 🔨 Part 3: DRAM Double-Sided Rowhammer Disturbance Attack
- **Desktop File:** [`Part 3/kitchen_espionage_level3.py`](Part%203/kitchen_espionage_level3.py) | **Web Tab:** Part 3
- **Concept:** Physical DRAM electrical disturbance, bit-flips, and privilege escalation.
- **The Hardware Analogy (Section A):**
  - **Freezer Shelves** = **DRAM Bank Rows.**
  - **Aggressor Rows** = Even rows (2, 4, 6... 18) that the attacker has permission to rapidly activate.
  - **Victim Row** = The protected odd row (3, 5, 7... 17) holding "The Security Access List".
  - **Double-Sided Hammering:** Alternating rapid activations of **both** sandwich rows ($T-1$ and $T+1$) induces 25% disturbance bit-flips. Single-sided hammering produces only mild warning vibrations.
- **Hardware Deep Dive (Section B):**
  - **Critical Concept: Where do bits flip?** Explains that bits flip in the **unaccessed VICTIM row**, NOT the aggressor row, due to parasitic capacitive coupling leaking charge from microscopic capacitors before the DRAM refresh interval (64ms).
  - **The Page Table Entry (PTE) Exploit:** Explains how real-world attackers (Google Project Zero) spray memory with page tables and use a single bit-flip in a Physical Page Number (PPN) field to redirect user memory to a page table itself, gaining root/kernel privilege escalation (Ring 0).
- **Gameplay:** Use a strategic skip search across even rows within a **tightened 20-action budget** to isolate the sandwich pair, double-hammer both rows to dislodge the access list, and verify with the Head Chef!

---

### 🏆 Mission Accomplished & Grand Victory Debrief
Upon clearing Level 3, a celebratory debrief screen celebrates the student's mastery across all three microarchitectural domains, providing options to replay individual levels or restart the entire suite.
