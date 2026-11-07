# stimtype

A dependency-free Linux terminal typing game with college-style vocabulary,
accuracy, elapsed time, cumulative points, and saved best scores. Requires Python 3.8 or newer.

## Install on Linux

Install Python 3 and Git first. On CachyOS/Arch:

```sh
sudo pacman -Syu --needed python git
```

This also performs a full system update. Then clone and install (works in Fish
and Bash):

```sh
git clone https://github.com/Tatersman/stimtype.git &&
cd stimtype &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

After installation, type `stimtype` from any directory. If you already cloned
the repository, use the update commands below instead. To try it without
installing, run `python3 stimtype` from the cloned folder.

For a user-only installation in Fish, run these commands from the cloned folder:

```fish
mkdir -p ~/.local/bin &&
install -m 755 stimtype ~/.local/bin/stimtype &&
fish_add_path ~/.local/bin &&
stimtype
```

## Play

Choose a mode at startup with **↑/↓**, then press **Enter**. Navigation wraps
at the ends; `q` quits. Number keys move the highlight to that option.
The replay menu uses the same controls. Piped input and `TERM=dumb` use the
numbered, line-based menu instead.

The startup options are:

```text
stimtype
1. 15-second test  best: 0
2. 30-second test  best: 0
3. 60-second test  best: 0
4. Free play  best: 0
q. Quit
Select:
```

Each round follows this format:

```text
hypothesis
> hypothesis
accuracy 100.0% time: 1.12s points: 179 score 179 best: 179
```

- Submit with **Space or Enter** in timed tests and free play. The submitting
  space is not part of the answer. Backspace works normally. Type `:q` to end a session and
  open the play-again menu. Ctrl+C or EOF (Ctrl+D on an empty line) exits the game.
- In timed modes, a live countdown appears next to the word, for example
  `hypothesis  14.9s`. It shows the session's remaining time, updates every tenth
  of a second while you type, and turns red for the final five seconds.
  Free play has no countdown. `--no-color` keeps the live timer active.
  Piped output and `TERM=dumb` show remaining time once per word instead.
- Timed tests end automatically, even without pressing Enter. The clock starts
  at the first word's prompt, after vocabulary loading. Answers submitted at or
  after the deadline are not scored; unfinished input is discarded.
- After each test or free-play session, choose **Same mode**, **Change mode**, or
  **Quit**. Replaying resets the timer and points and loads a fresh word list.
- Each answer adds **`200 × (1/3 + (2/3 × accuracy)) / time`** to your score.
  Accuracy is a fraction from 0 to 1; time is elapsed seconds. A perfect answer
  in 2 seconds earns 100 points; 50% accuracy in 2 seconds earns about 67.
  Faster, more accurate answers earn more. Following this formula, even a 0%
  answer earns the base `200 / (3 × time)`. Points accumulate at full precision
  and display rounded to whole numbers. Nonpositive elapsed time earns zero.
- A live **best** counter tracks the highest total for the current mode. Best
  scores are separate for 15 seconds, 30 seconds, 60 seconds, and free play.
  A new record is saved at session end, including when you exit with Ctrl+C.
  Existing saved bests are automatically displayed at the new 200× scale.
  Records remain stored in original units to preserve compatibility.
- `points` shows the gain for the word just submitted; `score` is the cumulative
  session total and `best` is the highest total for the mode.
- Time includes reading/reaction time and the submitting Space or Enter. Accuracy
  compares your final submitted text, including case, using
  `100 × (1 − edit_distance / max(word_length, typed_length))`. Missing, extra,
  and substituted characters count as edits. Empty answers score 0%; corrections
  made before submitting do not count against you.

The final summary uses this format (a previous score of 3.71 now displays as 742):

```text
words: 7 score: 742 best: 742
```

`words` counts submitted attempts, including incorrect answers. Quit commands
and unfinished answers at the deadline do not count.

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
and leaves redirected output free of escape sequences. `--no-color` keeps
arrow navigation active, using a plain `>` marker for the selected option.

## Update or uninstall

Update your existing installation (Fish and Bash):

```sh
cd ~/stimtype &&
git pull --ff-only &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

Uninstall with `sudo rm /usr/local/bin/stimtype`. For a user-only installation,
update by copying to `~/.local/bin/stimtype` instead, or uninstall by removing
that file.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

Tests cover scoring, cumulative points, all menu choices, deadline enforcement,
actual terminal expiry without Enter, clean exits, shuffled word selection,
online response validation, offline fallback, replay and mode switching, best-score
persistence, corrupt score files, save failures, color controls, real arrow-key
navigation, terminal restoration on interruption, scaled scores, live countdown expiry, typing and Backspace during timer
updates, terminal restoration after countdown interruption, and Space/Enter
submission in timed, free-play, and plain-terminal modes.
