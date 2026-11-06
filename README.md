# stimtype

A tiny terminal typing game with extremely long, difficult words (20–45 letters).
See a random word, type it, press Enter, and get your accuracy and elapsed time.
The next word appears automatically. Runs offline with Python 3.8 or newer;
no packages required.

## Install on Linux

Check that `python3 --version` works. This repository is private, so authenticate
with GitHub before cloning. On CachyOS/Arch, if GitHub CLI is not installed,
`sudo pacman -Syu --needed github-cli` installs it along with a full system update.
Then run:

```sh
gh auth login --hostname github.com --git-protocol https --web
gh repo clone Tatersman/stimtype &&
cd stimtype &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

After installation, type `stimtype` from any directory to play. The script is
copied into `/usr/local/bin`, which is on PATH on most Linux systems. You can
delete the cloned folder after installation.

If you prefer an installation without sudo, use these commands from the cloned
folder instead (Bash):

```sh
mkdir -p "$HOME/.local/bin"
install -m 755 stimtype "$HOME/.local/bin/stimtype"
case ":$PATH:" in
  *":$HOME/.local/bin:"*) ;;
  *) printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$HOME/.bashrc" ;;
esac
export PATH="$HOME/.local/bin:$PATH"
stimtype
```

For other shells, add `~/.local/bin` to PATH in that shell's configuration.
You can also play without installing: `python3 stimtype`.

## Play

```text
electroencephalography
> electroencephalography
accuracy 100.0% time: 4.12s

antidisestablishmentarianism
> antidisestablishmentarianism
accuracy 100.0% time: 5.31s
```

- Press Enter to submit each word. Backspace works normally in your terminal.
- Type `:q`, press Ctrl+C, or send EOF (Ctrl+D on an empty line on Linux) to quit.
- Timing starts when the input prompt is displayed and ends when you press Enter.
  This includes reading/reaction time and the final Enter.
- Accuracy compares your submitted text with the word, including case and spaces.
  It uses `100 × (1 − edit_distance / max(word_length, typed_length))`.
  Missing, extra, and substituted characters count as edits. An empty answer
  scores 0%; an exact match scores 100%. Corrections made before submitting do
  not count against you.
- The screen contains just the word, input prompt, and result for each round.
  Nothing is saved or sent anywhere.

## Update or uninstall

To update an existing installation (works in Fish and Bash):

```sh
cd ~/stimtype &&
git pull --ff-only &&
sudo install -m 755 stimtype /usr/local/bin/stimtype &&
stimtype
```

To uninstall a system installation:

```sh
sudo rm /usr/local/bin/stimtype
```

For a user installation, remove `~/.local/bin/stimtype` instead.

## Tests

```sh
python3 -m unittest discover -s tests -v
```
