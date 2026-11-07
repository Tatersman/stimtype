"""Behavior checks for scoring, repeated rounds, timing, and clean exits."""

import os
import tempfile
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "stimtype"
LOADER = importlib.machinery.SourceFileLoader("stimtype_game", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
game = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(game)


class AccuracyTests(unittest.TestCase):
    def test_exact_empty_and_completely_wrong_answers(self):
        for expected, typed, score in (
            ("garden", "garden", 100.0),
            ("garden", "", 0.0),
            ("", "garden", 0.0),
            ("", "", 100.0),
            ("cat", "dog", 0.0),
        ):
            with self.subTest(expected=expected, typed=typed):
                self.assertAlmostEqual(game.accuracy(expected, typed), score)

    def test_missing_extra_and_substituted_characters(self):
        for expected, typed, score in (
            ("forest", "forst", 100 * 5 / 6),
            ("garden", "gardens", 100 * 6 / 7),
            ("garden", "garken", 100 * 5 / 6),
            ("garden", "Garden", 100 * 5 / 6),
            ("garden", " garden", 100 * 6 / 7),
            ("cat", "act", 100 / 3),
        ):
            with self.subTest(expected=expected, typed=typed):
                self.assertAlmostEqual(game.accuracy(expected, typed), score)


class GameTests(unittest.TestCase):
    def play(self, answers, times, duration=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), \
                patch.object(game, "read_answer", side_effect=answers), \
                patch.object(game, "shuffled_words", return_value=iter(["analysis", "analysis", "analysis"])), \
                patch.object(game.time, "perf_counter", side_effect=times):
            self.assertIsInstance(game.play(["analysis"], duration), tuple)
        return output.getvalue()

    def test_points_accumulate_inverse_time_formula(self):
        output = self.play(["analysis", "analysis", ":q"], [0, 1.12, 2, 4, 5, 6])
        self.assertIn("accuracy 100.0% time: 1.12s points: 0.89", output)
        self.assertIn("accuracy 100.0% time: 2.00s points: 1.39", output)
        self.assertIn("rounds: 2 points: 1.39", output)

    def test_incorrect_answer_gets_proportional_points(self):
        output = self.play(["analysi", ":q"], [0, 2, 3, 4])
        self.assertIn("accuracy 87.5% time: 2.00s points: 0.46", output)

    def test_expired_answer_is_not_scored(self):
        output = self.play(["analysis"], [0, 16], 15)
        self.assertIn("Time's up!", output)
        self.assertIn("rounds: 0 points: 0", output)

    def test_idle_timeout_ends_test(self):
        output = self.play([game.TimeUp], [0], 15)
        self.assertIn("Time's up!", output)
        self.assertIn("rounds: 0 points: 0", output)

    def test_quit_eof_and_interrupt(self):
        for answer in [":q", EOFError, KeyboardInterrupt]:
            output = self.play([answer], [0, 1])
            self.assertIn("rounds: 0 points: 0", output)

    def test_shuffle_exhausts_pool_without_boundary_repeat(self):
        words = ("analysis", "inference", "hypothesis")
        stream = game.shuffled_words(words)
        values = [next(stream) for _ in range(30)]
        for i in range(0, 30, 3):
            self.assertEqual(set(values[i:i+3]), set(words))
        self.assertTrue(all(a != b for a, b in zip(values, values[1:])))

    def test_menu_modes_and_invalid_choice(self):
        for choice, duration in [("1", 15), ("2", 30), ("3", 60), ("4", None)]:
            with patch("builtins.input", side_effect=["wrong", choice]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(game.MODES[game.menu()], duration)

    def test_deadline_wait_is_bounded(self):
        with patch.object(game.time, "perf_counter", return_value=10), \
                patch.object(game.select, "select", return_value=([], [], [])) as wait:
            with self.assertRaises(game.TimeUp):
                game.read_answer(15)
            wait.assert_called_once_with([sys.stdin], [], [], 5)


class ReplayAndRecordsTests(unittest.TestCase):
    def test_formula_normalizes_accuracy_and_rewards_speed(self):
        self.assertAlmostEqual(game.earned_points(100, 2), 0.5)
        self.assertAlmostEqual(game.earned_points(50, 2), 1 / 3)
        self.assertAlmostEqual(game.earned_points(0, 2), 1 / 6)
        self.assertGreater(game.earned_points(100, 1), game.earned_points(100, 2))
        self.assertEqual(game.earned_points(100, 0), 0)

    def test_best_scores_persist_per_mode_and_never_decrease(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(game, "score_path", return_value=Path(directory) / "scores.json"):
            bests = game.load_bests()
            game.save_best(bests, "1", 12.5)
            game.save_best(bests, "1", 3)
            game.save_best(bests, "4", 8)
            self.assertEqual(game.load_bests(), {"1": 12.5, "4": 8})
            self.assertEqual(list(Path(directory).iterdir()), [Path(directory) / "scores.json"])

    def test_corrupt_and_invalid_records_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(game, "score_path", return_value=Path(directory) / "scores.json"):
            path = game.score_path()
            for data in ['bad json', '[]', '{"1": -1, "2": true, "3": NaN, "4": "bad"}']:
                path.write_text(data)
                self.assertEqual(game.load_bests(), {})

    def test_save_failure_keeps_in_memory_record(self):
        with patch.object(game.Path, "mkdir", side_effect=OSError), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            bests = {}
            game.save_best(bests, "1", 2.5)
            self.assertEqual(bests["1"], 2.5)
            self.assertIn("could not save", output.getvalue())

    def test_replay_same_mode_change_mode_and_quit(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, str(SCRIPT), "--offline", "--no-color"],
                input="4\n:q\nwrong\n1\n:q\n2\n1\n:q\nq\n", text=True,
                capture_output=True, timeout=5, env=dict(os.environ, XDG_DATA_HOME=directory))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stdout.count("Play again?"), 3)
        self.assertEqual(process.stdout.count("15-second test"), 2)
        self.assertNotIn("\x1b[", process.stdout)

    def test_colors_respect_terminal_and_no_color(self):
        with patch.object(game.sys.stdout, "isatty", return_value=True), \
                patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            self.assertIn("\x1b[", game.color("word", "36"))
            with patch.dict(os.environ, {"NO_COLOR": ""}):
                self.assertEqual(game.color("word", "36"), "word")
            with patch.object(game, "COLOR_ENABLED", False):
                self.assertEqual(game.color("word", "36"), "word")


class WordTests(unittest.TestCase):
    def test_offline_avoids_network(self):
        with patch.object(game.urllib.request, "urlopen") as fetch:
            self.assertEqual(game.load_words(True), game.WORDS)
            fetch.assert_not_called()
        self.assertEqual(len(game.WORDS), len(set(game.WORDS)))
        self.assertTrue(all(6 <= len(w) <= 14 for w in game.WORDS))

    def test_network_failure_and_invalid_data_fall_back(self):
        from unittest.mock import MagicMock
        for payload in [b"not json", b"{}", b"[]", b'[{}, {"word": 123}]']:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = payload
            with patch.object(game.urllib.request, "urlopen", return_value=response):
                self.assertEqual(game.load_words(), game.WORDS)
        with patch.object(game.urllib.request, "urlopen", side_effect=OSError):
            self.assertEqual(game.load_words(), game.WORDS)

    def test_online_words_are_filtered_and_deduplicated(self):
        import json
        from unittest.mock import MagicMock
        expected = tuple(w for w in game.WORDS if len(w) >= 7)[:15]
        data = [{"word": w} for w in expected + expected]
        data.extend([{"word": w} for w in ["two words", "abc", "UPPERCASE", "hello\x1bworld"]])
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(data).encode()
        with patch.object(game.urllib.request, "urlopen", return_value=response):
            self.assertEqual(game.load_words(), expected)


class CommandTests(unittest.TestCase):
    def test_actual_free_play_and_quit(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, str(SCRIPT), "--offline"],
                                     input="4\n\n:q\nq\n", text=True, capture_output=True, timeout=5,
                                     env=dict(os.environ, XDG_DATA_HOME=directory))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("15-second test", process.stdout)
        self.assertIn("30-second test", process.stdout)
        self.assertIn("60-second test", process.stdout)
        self.assertIn("Free play", process.stdout)
        self.assertIn("accuracy 0.0%", process.stdout)
        self.assertIn("rounds: 1 points:", process.stdout)

    def test_timed_session_expires_in_real_terminal_without_enter(self):
        import os
        import pty
        import select
        import time
        master, slave = pty.openpty()
        # Exercise the same deadline path with a short duration for a fast check.
        code = "import runpy; g=runpy.run_path(%r); g['play'](['analysis'], 0.2)" % str(SCRIPT)
        process = subprocess.Popen([sys.executable, "-c", code], stdin=slave,
                                   stdout=slave, stderr=slave)
        os.close(slave)
        output = b""
        end = time.monotonic() + 5
        try:
            os.write(master, b"unfinished")
            while time.monotonic() < end:
                if select.select([master], [], [], 0.1)[0]:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    output += chunk
            process.wait(timeout=1)
            self.assertEqual(process.returncode, 0, output)
            self.assertIn(b"Time's up!", output)
            self.assertIn(b"rounds: 0 points: 0", output)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)


if __name__ == "__main__":
    unittest.main()
