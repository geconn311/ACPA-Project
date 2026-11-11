# Kitchen Espionage: A Visual Flush+Reload Simulator

An interactive, GUI-based educational module designed to teach undergraduate cybersecurity students the microarchitectural mechanics of **Cache Side-Channel Attacks** (specifically Flush+Reload) without requiring low-level assembly programming. 

## 🎯 Educational Objective
This simulator translates abstract computer architecture vulnerabilities into a tangible, visual state machine. By measuring the physical time it takes a Chef to fetch ingredients, students map out hidden data using the exact same logic an attacker uses to map an L1 cache.

### The Hardware Analogy
* **The Walk-In Freezer** = Main Memory (DRAM). Slow, high-latency access (simulated as ~3.3 seconds).
* **The Prep Counter** = L1 Cache (SRAM). Fast, low-latency access (simulated as ~0.6 seconds).
* **The Sous-Chef** = The CPU executing load instructions.
* **The VIP Order** = The Victim's secret cryptographic key or sensitive data.

---

## ⚙️ Prerequisites & Installation
This simulator runs entirely on Python's built-in libraries. No external packages (like Pygame) are required.
* **Python 3.6+** must be installed.
* **Tkinter** (Python's standard GUI framework) is included by default on Windows and macOS.
  * *Note for Linux users: You may need to install it manually via your package manager (e.g., `sudo apt-get install python3-tk`).*

**To run the simulator:**
1. Download `kitchen_espionage.py` to your local machine.
2. Open your terminal or command prompt.
3. Run the following command:
   ```bash
   python kitchen_espionage.py
   ```
