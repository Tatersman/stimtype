# stimtype

A dependency-free Linux terminal typing game with college-style vocabulary,
accuracy, elapsed time, and cumulative points. Requires Python 3.8 or newer.

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
1. 15-second test
2. 30-second test
3. 60-second test
4. Free play
q. Quit
Select:
```

Each round follows this format:

```text
hypothesis
> hypothesis
accuracy 100.0% time: 1.12s points: 112
```

- Submit with Enter; Backspace works normally. Type `:q`, press Ctrl+C, or send
  EOF (Ctrl+D on an empty line) to end the session.
- Timed tests end automatically, even without pressing Enter. The clock starts
  at the first word's prompt, after vocabulary loading. Answers submitted at or
  after the deadline are not scored; unfinished input is discarded.
- Free play continues until you quit. Each session ends with completed rounds
  and total points; launch `stimtype` again to select another mode.
- Each answer adds **accuracy percentage × elapsed seconds** to your points.
  For example, 100% × 1.12 seconds adds 112 points; 80% × 2 seconds adds 160.
  As requested, this formula rewards slower answers with more points. Points
  reset each session, accumulate at full precision, and display rounded to a
  whole number.
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
Datamuse; your answers and scores stay local and are not saved.

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
online response validation, and offline fallback.
