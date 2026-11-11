# ACPA-Project: Kitchen Espionage

An interactive, GUI-based educational module designed to teach cybersecurity concepts through simulated cache side-channel attacks (Flush+Reload).

## Running the Project

You can start the game with a single command from the project root:

```bash
python main.py
```

### Flow:
1. **Part 1 (Kitchen Espionage - Flush+Reload GUI):** The student flushes the cache, observes the victim, measures access latency (hits vs. misses), and submits the VIP ingredients in the Tkinter GUI.
2. **Part 2 (Kitchen Espionage Part 2 - Pipeline & Cache Latency GUI):** Automatically launches upon Part 1 victory. Displays an interactive GUI simulation of the 5-stage CPU pipeline (IF, DE, EX, ME, WB) and visualizes the Chef fetching data across the Prep Counter (L1 Cache - 1s), Kitchen Pantry (L2 Cache - 3s), and Walk-In Freezer (Main Memory - 5s).
3. **Part 3 (Kitchen Espionage Part 3 - Rowhammer Attack GUI):** Automatically launches upon Part 2 completion. Interactive GUI simulation demonstrating Rowhammer disturbance errors across DRAM shelves with physical shelf animations and adjacent-row bit-flip mechanics.
4. You can start the entire sequence from root with `python main.py`, or launch any part individually.
