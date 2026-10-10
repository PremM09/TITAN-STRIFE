# Titan Strife

A retro-inspired 2D fighting game built with Python and Pygame by Prem Mehta.

**[Play in your browser](https://aizenxpm.itch.io/titanstrife)**

## Features
- Five original fighters: Zen, Kara, Steve, Teresa and Jay.
- Unique special abilities unlocked by five consecutive successful basic hits.
- Bot opponents with three difficulty levels and adaptive opponent selection.
- Best-of-three matches with 200 HP, 60-second rounds and sudden-death ties.
- Day/night arenas, arcade artwork and synthesized music and sound effects.
- Keyboard and touchscreen controls.

## Run locally
Python 3.10+ is required.

On Windows, run `SETUP_WINDOWS.bat` once, then `RUN_GAME.bat`.

Alternatively, from the project folder:
```sh
python -m pip install -r requirements.txt
python main.py
```

## Controls
| Action | Keyboard | Touch |
| --- | --- | --- |
| Move | A/D or Left/Right | Joystick |
| Jump | W, Up or Space | Joystick up |
| Crouch | S or Down | Joystick down |
| Punch | J | X |
| Kick | K | A |
| Combo | L | Y |
| Special | I | B |
| Block | Hold away or Shift | Hold joystick away |
| Pause | Escape | PAUSE |

Five consecutive successful punch/kick hits unlock a special once per round.
The combo has a five-second cooldown. Misses, blocked basic attacks and taking
damage reset the hit streak; a charged special remains ready until used.

## Browser and mobile
The published version uses Pygbag to run Python/Pygame in a browser.
On mobile, use landscape and fullscreen without zooming. The release has been
playtested on Windows and Android. Mobile screen fit remains a known polish item.

To rebuild the web package:
```sh
python -m pip install pygbag==0.9.3
python build_web.py
```
Upload `build/Titan-Strife-Web.zip` to itch.io as an HTML browser game.
Initial browser loading needs internet access for the Pygbag runtime.

## Project structure
- `main.py`: menus, keyboard/touch input, rendering and game loop.
- `combat.py`: combat, bot decisions, special abilities and round rules.
- `sprites.py`: sprite loading and poses.
- `arena.py` / `effects.py`: arenas and special effects.
- `make_audio.py`: synthesized audio generation.
- `assets/`: artwork, audio and fonts.
- `tests/`: automated checks.
- `web/index.html`: browser loader and mobile display support.

## Tests
```sh
python -m unittest discover -s tests -v
```

## Development and credits
Created with AI assistance for programming, artwork and iteration, with manual
playtesting and feedback guiding the final balance and presentation.
Artwork uses original designs rather than ripped franchise sprites.
Bundled DejaVu fonts retain their licence in `assets/FONT-LICENSE.txt`.
Pygame and Pygbag are third-party dependencies with their own licences.
No open-source licence has been granted for the project code or original assets.
