# stimtype

A dependency-free Linux terminal typing game with college-style vocabulary,
accuracy, elapsed time, cumulative points, and saved best scores. Requires Python 3.8 or newer.

## Install

This repository is private. Authenticate with GitHub CLI, then install:

```sh
gh auth login --hostname github.com --git-protocol https --web
gh repo clone Tatersman/stimtype &&
cd stimtype &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

On CachyOS/Arch, `sudo pacman -Syu --needed github-cli python` installs the
prerequisites along with a full system update. After installation, run
`stimtype` from any directory. To try it without installing, run `python3 stimtype`.

## Play

Choose a mode at startup:

```text
stimtype
1. 15-second test  best: 0.00
2. 30-second test  best: 0.00
3. 60-second test  best: 0.00
4. Free play  best: 0.00
q. Quit
Select:
```

Each round follows this format:

```text
hypothesis
> hypothesis
accuracy 100.0% time: 1.12s points: 0.89 best: 0.89
```

- Submit with Enter; Backspace works normally. Type `:q` to end a session and
  open the play-again menu. Ctrl+C or EOF (Ctrl+D on an empty line) exits the game.
- Timed tests end automatically, even without pressing Enter. The clock starts
  at the first word's prompt, after vocabulary loading. Answers submitted at or
  after the deadline are not scored; unfinished input is discarded.
- After each test or free-play session, choose **Same mode**, **Change mode**, or
  **Quit**. Replaying resets the timer and points and loads a fresh word list.
- Each answer adds **`(1/3 + (2/3 × accuracy)) / time`** to your points.
  Accuracy is a fraction from 0 to 1; time is elapsed seconds. A perfect answer
  in 2 seconds earns 0.50 points; 50% accuracy in 2 seconds earns about 0.33.
  Faster, more accurate answers earn more. Following this formula, even a 0%
  answer earns the base `1 / (3 × time)`. Points accumulate at full precision
  and display with two decimal places. Nonpositive elapsed time earns zero.
- A live **best** counter tracks the highest total for the current mode. Best
  scores are separate for 15 seconds, 30 seconds, 60 seconds, and free play.
  A new record is saved at session end, including when you exit with Ctrl+C.
- Time includes reading/reaction time and the final Enter. Accuracy compares
  your final submitted text, including case and spaces, using
  `100 × (1 − edit_distance / max(word_length, typed_length))`. Missing, extra,
  and substituted characters count as edits. Empty answers score 0%; corrections
  made before submitting do not count against you.

## Vocabulary

At each session start, stimtype fetches words related to a randomly selected
academic subject (such as philosophy, economics, or psychology) from the
[Datamuse API](https://www.datamuse.com/api/). It accepts only lowercase words
of 7–14 letters. These are academically themed words, not a formally graded
college vocabulary list. The list is shuffled and exhausted before reshuffling,
with no consecutive repeated words.

If fetching times out, fails, or produces too few valid words, the game uses a
built-in academic vocabulary list, including words such as *inference*,
*paradigm*, *empirical*, and *synthesis*. To skip the network entirely:

```sh
stimtype --offline
```

Loading happens before the timer starts. Only the selected topic is sent to
Datamuse; your answers stay local and are not saved. Best scores are stored in
`~/.local/share/stimtype/best-scores-inverse-time-v1.json` (or under
`$XDG_DATA_HOME/stimtype` when configured). Remove that file to reset records.
If saving is unavailable, records remain available for the current run.

## Colors

Words and headings are cyan, prompts are purple, perfect answers are green,
and imperfect answers and records are yellow. Use `stimtype --no-color` for
plain text. The game also respects `NO_COLOR`, disables color for `TERM=dumb`,
and leaves redirected output free of color escape sequences.

## Update or uninstall

Update your existing installation (Fish and Bash):

```sh
cd ~/stimtype &&
git pull --ff-only &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

Uninstall with `sudo rm /usr/local/bin/stimtype`.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests cover scoring, cumulative points, all menu choices, deadline enforcement,
actual terminal expiry without Enter, clean exits, shuffled word selection,
online response validation, offline fallback, replay and mode switching, best-score
persistence, corrupt score files, save failures, and color controls.
