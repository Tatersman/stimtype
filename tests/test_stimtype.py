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
        responses = iter(answers)

        def terminal_input():
            response = next(responses)
            if isinstance(response, type) and issubclass(response, BaseException):
                raise response
            # Real terminals echo submitted text, including the final newline.
            print(response)
            return response

        with contextlib.redirect_stdout(output), \
                patch("builtins.input", side_effect=terminal_input), \
                patch.object(game.random, "choice", side_effect=words or ["garden"]), \
                patch.object(game.time, "perf_counter", side_effect=times or [10.0]):
            result = game.play()
        self.assertEqual(result, 0)
        return output.getvalue()

    def test_exact_requested_template_with_a_mocked_word(self):
        output = self.run_game(
            answers=["nest", ":q"],
            words=["nest", "garden"],
            times=[10.0, 11.12, 20.0, 21.0],
        )
        self.assertEqual(output, "nest\n> nest\naccuracy 100.0% time: 1.12s\n\ngarden\n> :q\n")

    def test_multiple_rounds_report_elapsed_time_and_accuracy(self):
        output = self.run_game(
            answers=["garden", "forst", ":q"],
            words=["garden", "forest", "apple"],
            times=[10.0, 11.25, 20.0, 22.75, 30.0, 35.0],
        )
        self.assertEqual(
            output,
            "garden\n> garden\naccuracy 100.0% time: 1.25s\n\n"
            "forest\n> forst\naccuracy 83.3% time: 2.75s\n\n"
            "apple\n> :q\n",
        )

    def test_empty_answer_is_a_scored_round(self):
        output = self.run_game(
            answers=["", ":q"],
            words=["garden", "forest"],
            times=[10.0, 11.0, 20.0, 21.0],
        )
        self.assertEqual(output, "garden\n> \naccuracy 0.0% time: 1.00s\n\nforest\n> :q\n")

    def test_quit_does_not_count_as_an_attempt(self):
        output = self.run_game([":q"], times=[10.0, 12.0])
        self.assertEqual(output, "garden\n> :q\n")

    def test_eof_and_keyboard_interrupt_before_first_round_exit_cleanly(self):
        for exit_signal in (EOFError, KeyboardInterrupt):
            with self.subTest(exit_signal=exit_signal):
                output = self.run_game([exit_signal])
                self.assertEqual(output, "garden\n> \n")

    def test_eof_and_keyboard_interrupt_preserve_completed_results(self):
        for exit_signal in (EOFError, KeyboardInterrupt):
            with self.subTest(exit_signal=exit_signal):
                output = self.run_game(
                    ["garden", exit_signal],
                    words=["garden", "forest"],
                    times=[10.0, 11.0, 20.0],
                )
                self.assertEqual(
                    output,
                    "garden\n> garden\naccuracy 100.0% time: 1.00s\n\nforest\n> \n",
                )

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


class WordListTests(unittest.TestCase):
    def test_words_are_unique_lowercase_letters_and_at_least_twenty_characters(self):
        self.assertGreater(len(game.WORDS), 1)
        self.assertEqual(len(game.WORDS), len(set(game.WORDS)))
        for word in game.WORDS:
            with self.subTest(word=word):
                self.assertGreaterEqual(len(word), 20)
                self.assertTrue(word.isalpha())
                self.assertTrue(word.isascii())
                self.assertEqual(word, word.lower())


class CommandTests(unittest.TestCase):
    def test_help_and_version_do_not_start_a_round(self):
        for option, expected in (("--help", "usage:"), ("--version", "stimtype 1.1.0")):
            with self.subTest(option=option):
                process = subprocess.run(
                    [sys.executable, str(SCRIPT), option],
                    input="", capture_output=True, text=True, timeout=5,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assertIn(expected, process.stdout)
                self.assertNotIn("> ", process.stdout)

    def test_actual_process_accepts_input_then_quits(self):
        process = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input="\n:q\n", capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertRegex(
            process.stdout,
            r"\A[a-z]{20,}\n> accuracy 0\.0% time: \d+\.\d{2}s\n\n[a-z]{20,}\n> \Z",
        )
        self.assertEqual(process.stderr, "")


if __name__ == "__main__":
    unittest.main()
