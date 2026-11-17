import sys
import os
import unittest
import tkinter as tk
from unittest.mock import patch, MagicMock

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(base_dir, "Part 1"))
sys.path.insert(0, os.path.join(base_dir, "Part 2"))
sys.path.insert(0, os.path.join(base_dir, "Part 3"))

# Mock messagebox and time.sleep to avoid blocking modals and sleep delays
patcher_msg = patch("tkinter.messagebox.showerror")
patcher_info = patch("tkinter.messagebox.showinfo")
patcher_sleep = patch("time.sleep", return_value=None)

patcher_msg.start()
patcher_info.start()
patcher_sleep.start()

import kitchen_espionage_part1 as p1
import kitchen_espionage_part2 as p2
import kitchen_espionage_level3 as p3

class TestPart1(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = p1.InteractiveKitchen(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_part1_initial_state(self):
        self.assertEqual(len(self.game.secret_ingredients), 6)
        self.assertEqual(self.game.probes_remaining, 18)

    def test_part1_flush_cache(self):
        self.game.prep_counter = [1, 5, 8]
        self.game.flush_cache()
        self.assertEqual(len(self.game.prep_counter), 0)

    def test_part1_trigger_victim(self):
        self.game.flush_cache()
        self.assertEqual(len(self.game.prep_counter), 0)
        self.game.trigger_victim()
        self.assertEqual(len(self.game.prep_counter), 6)
        self.assertEqual(sorted(self.game.prep_counter), sorted(self.game.secret_ingredients))

    def test_part1_probe_timing(self):
        self.game.flush_cache()
        self.game.trigger_victim()
        cached_item = self.game.secret_ingredients[0]
        uncached_item = next(i for i in range(20) if i not in self.game.secret_ingredients)

        # Probe hit
        self.game.probe_spinbox.delete(0, tk.END)
        self.game.probe_spinbox.insert(0, str(cached_item))
        self.game.probe_ingredient()
        self.assertTrue(self.game.last_probe_info["hit"])
        self.assertLess(self.game.last_probe_info["cycles"], 80)

        # Probe miss
        self.game.probe_spinbox.delete(0, tk.END)
        self.game.probe_spinbox.insert(0, str(uncached_item))
        self.game.probe_ingredient()
        self.assertFalse(self.game.last_probe_info["hit"])
        self.assertGreater(self.game.last_probe_info["cycles"], 250)

    def test_part1_canvas_resizing(self):
        for w, h in [(800, 600), (1280, 720), (1920, 1080), (2560, 1440)]:
            self.game.canvas_width = w
            self.game.canvas_height = h
            self.game._redraw_silicon_canvas()

    def test_part1_submission_validation(self):
        # Empty string
        self.game.guess_entry.delete(0, tk.END)
        self.game.guess_entry.insert(0, "")
        self.game.verify_attack()

        # Incomplete count (e.g. only 3)
        self.game.guess_entry.delete(0, tk.END)
        self.game.guess_entry.insert(0, "1 2 3")
        self.game.verify_attack()

        # Correct submission
        correct_str = " ".join(str(x) for x in self.game.secret_ingredients)
        self.game.guess_entry.delete(0, tk.END)
        self.game.guess_entry.insert(0, correct_str)
        with patch.object(self.game, 'launch_part_2') as mock_p2:
            self.game.verify_attack()
            mock_p2.assert_called_once()

class TestPart2(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = p2.KitchenPipelineGUI(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_part2_pipeline_step(self):
        initial_cycle = self.game.cycle
        self.game.step_cycle()
        self.assertEqual(self.game.cycle, initial_cycle + 1)
        self.assertIsNotNone(self.game.fetch)

    def test_part2_canvas_resizing(self):
        for w, h in [(800, 600), (1280, 720), (1920, 1080), (2560, 1440)]:
            self.game.canvas_width = w
            self.game.canvas_height = h
            self.game._redraw_pipeline_canvas()

class TestPart3(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.game = p3.RowhammerKitchenGUI(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_part3_hammer(self):
        initial_actions = self.game.actions_remaining
        self.game.row_var.set("2")
        self.game.hammer_row()
        self.assertEqual(self.game.actions_remaining, initial_actions - 1)
        self.assertIn(2, self.game.recent_hammers)

    def test_part3_canvas_resizing(self):
        for w, h in [(800, 600), (1280, 720), (1920, 1080), (2560, 1440)]:
            self.game.canvas_width = w
            self.game.canvas_height = h
            self.game._redraw_dram_canvas()

if __name__ == '__main__':
    unittest.main()
