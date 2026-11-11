"""
ACPA Project - Main Runner
Runs Part 1 (kitchen_espionage_part1.py).
Upon completing Part 1, Part 2 (kitchen_espionage_part2.py) starts automatically.
Upon completing Part 2, Part 3 (kitchen_espionage_level3.py) starts automatically!
"""
import os
import sys
import subprocess

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    part1_dir = os.path.join(base_dir, "Part 1")
    
    # Locate Part 1 script (kitchen_espionage_part1.py or fallback)
    part1_script = os.path.join(part1_dir, "kitchen_espionage_part1.py")
    if not os.path.exists(part1_script):
        part1_script = os.path.join(part1_dir, "kitchen_espionage.py")

    if not os.path.exists(part1_script):
        print(f"Error: Could not find Part 1 script in: {part1_dir}")
        sys.exit(1)

    # Launch Part 1; upon victory, it automatically starts Part 2, which then starts Part 3
    subprocess.run([sys.executable, part1_script], cwd=part1_dir)

if __name__ == "__main__":
    main()
