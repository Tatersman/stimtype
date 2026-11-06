"""Behavior checks for scoring, repeated rounds, timing, and clean exits."""

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
    def run_game(self, answers, words=None, times=None):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), \
                patch("builtins.input", side_effect=answers), \
                patch.object(game.random, "choice", side_effect=words or ["garden"]), \
                patch.object(game.time, "perf_counter", side_effect=times or [10.0]):
            result = game.play()
        self.assertEqual(result, 0)
        return output.getvalue()

    def test_multiple_rounds_report_elapsed_time_accuracy_and_averages(self):
        output = self.run_game(
            answers=["garden", "forst", ":q"],
            words=["garden", "forest", "apple"],
            times=[10.0, 11.25, 20.0, 22.75, 30.0, 35.0],
        )
        self.assertIn("Accuracy: 100.0% | Time: 1.25s", output)
        self.assertIn("Accuracy: 83.3% | Time: 2.75s", output)
        self.assertIn("2 rounds | Average accuracy: 91.7% | Average time: 2.00s", output)
        self.assertEqual(output.count("Word: "), 3)
        self.assertTrue(output.rstrip().endswith("Thanks for playing!"))

    def test_empty_answer_is_a_scored_round(self):
        output = self.run_game(
            answers=["", ":q"],
            words=["garden", "forest"],
            times=[10.0, 11.0, 20.0, 21.0],
        )
        self.assertIn("Accuracy: 0.0% | Time: 1.00s", output)
        self.assertIn("1 round | Average accuracy: 0.0%", output)

    def test_quit_does_not_count_as_an_attempt(self):
        output = self.run_game([":q"], times=[10.0, 12.0])
        self.assertNotIn("Accuracy:", output)
        self.assertNotIn("Average accuracy:", output)
        self.assertIn("Thanks for playing!", output)

    def test_eof_and_keyboard_interrupt_before_first_round_exit_cleanly(self):
        for exit_signal in (EOFError, KeyboardInterrupt):
            with self.subTest(exit_signal=exit_signal):
                output = self.run_game([exit_signal])
                self.assertNotIn("Accuracy:", output)
                self.assertIn("Thanks for playing!", output)

    def test_eof_and_keyboard_interrupt_preserve_completed_results(self):
        for exit_signal in (EOFError, KeyboardInterrupt):
            with self.subTest(exit_signal=exit_signal):
                output = self.run_game(
                    ["garden", exit_signal],
                    words=["garden", "forest"],
                    times=[10.0, 11.0, 20.0],
                )
                self.assertIn("1 round | Average accuracy: 100.0% | Average time: 1.00s", output)

    def test_previous_word_is_excluded_from_the_next_selection(self):
        choices = []

        def choose(words):
            choices.append(tuple(words))
            return words[0]

        with contextlib.redirect_stdout(io.StringIO()), \
                patch("builtins.input", side_effect=["anchor", ":q"]), \
                patch.object(game.random, "choice", side_effect=choose):
            game.play()
        self.assertGreater(len(choices[0]), 1)
        self.assertNotIn(choices[0][0], choices[1])


class CommandTests(unittest.TestCase):
    def test_help_and_version_do_not_start_a_round(self):
        for option, expected in (("--help", "usage:"), ("--version", "stimtype 1.0.0")):
            with self.subTest(option=option):
                process = subprocess.run(
                    [sys.executable, str(SCRIPT), option],
                    input="", capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertIn(expected, process.stdout)
                self.assertNotIn("Word:", process.stdout)

    def test_actual_process_accepts_input_then_quits(self):
        process = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="\n:q\n", capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Accuracy: 0.0% | Time:", process.stdout)
        self.assertIn("1 round | Average accuracy: 0.0%", process.stdout)
        self.assertEqual(process.stderr, "")


if __name__ == "__main__":
    unittest.main()
