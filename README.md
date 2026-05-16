# Little Guardian of the Ocean

Little Guardian of the Ocean is a small 2D pygame game inspired by the classic Gold Miner gameplay loop. The player controls a hook from a boat, collects ocean trash, avoids or interacts with moving sea creatures, and tries to earn as much guardian value as possible before time runs out.

## Project Structure

```text
Little Guardian of the Ocean.py
art_resources/
requirements.txt
```

- `Little Guardian of the Ocean.py`: Main game source file.
- `art_resources/`: Image assets used by the game interface and game objects.
- `requirements.txt`: Python package dependencies.

## Requirements

Python 3.9 or newer is recommended.

Install dependencies with:

```bash
pip install -r requirements.txt
```

## How to Run

From this folder, run:

```bash
python "Little Guardian of the Ocean.py"
```

## Controls

- Mouse click: select menu buttons, continue through introduction screens, pause, and launch the hook during gameplay.

## Generated Files

The game may create local runtime files such as:

```text
gamecache.sav
highscore.sav
save_load.log
__pycache__/
```

These files are intentionally excluded from version control because they are local saves, logs, or Python cache files.

## Notes for GitHub

This prepared version removes runtime cache/log/archive files and keeps only the source code, image assets, README, dependency list, and ignore rules needed for a clean repository upload.
