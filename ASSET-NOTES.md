# Original asset production — 0.3

Generated using the built-in image-generation tool. Assets are included locally,
not loaded from remote URLs. Sprite atlases are alpha-isolated and scaled at runtime.

- assets/jay.png: four right-facing full-body poses (guard, straight punch, side
  kick, hurt) of Jay. Prompt direction: preserve muscular bare chest, dark hair,
  beard and teal/gold palette; replace wrestling shorts with loose full-length
  teal martial trousers, ceremonial rune sash, gold bracers and dark boots.
  Transparent background, original detailed arcade sprite aesthetic.
- assets/movement.png: five character rows, five columns: crouch guard, crouch
  punch, low sweep, airborne punch, airborne kick. Same original outfits for Zen,
  Kara, Steve and Teresa; Jay uses the new spellfighter design. Transparent.
  Corrective prompt preserved layout while fixing Steve's sweep outfit and
  covering Jay's knees with full-length trousers.
- assets/arena-day.png: original full Roman colosseum / spiritual Japanese
  fortress stage, ivory limestone arcades, teal roofs, gold/violet banners,
  mountains, bright daylight, empty side-view stone combat terrace. No text/UI.
- assets/arena-night.png: lighting edit of the same architecture and camera,
  midnight sky, moon, blue/violet stone lighting and amber braziers.

Rendering fits the arena floor to combat coordinates. New character art is
used in menus and matches. Left-facing sprites mirror right-facing artwork.
The background art and character atlas were generated, not taken from another game.

Sound: make_audio.py synthesizes every sound and the music loop. The punch crack
and bass kick impact are distinct waveforms; no sampled franchise recordings.
Font: bundled DejaVu Sans, license included in assets/FONT-LICENSE.txt.

## Revised arena art direction
The painterly arena was replaced with built-in image-generation edits.
Day prompt: authentic 1992 16-bit arcade stage; coarse consistent pixel grid,
square clusters, jagged contours, restrained palette, three flat shade bands,
Roman arches and spiritual Japanese fortress, ivory pillars, teal roofs, violet
banners, clear empty stone terrace. No realistic texture, bloom or smooth shading.
Night prompt: preserve the exact pixel-art architecture and floor; use an indigo
sky, small square stars, pixel crescent moon, slate/lavender stone and amber
torches, retaining flat shade ramps without glow.
The runtime uses nearest-neighbor sampling to preserve the pixel-art edges.

## Jay approval candidate
assets/jay-review.png: built-in image-generation tool, prompt direction:
match original roster's coarse 1992 arcade pixels, dark contours, angular
3-tone shading and visible clusters. Preserve muscular bare torso, full teal
trousers, rune sash/bracers and boots. Twelve separate right-facing poses:
guard/punch/kick/hurt; crouch guard/punch/kick/air punch; air kick/charge/open-
palm release/victory. Transparent background; no baked-in magic effects.
Runtime nearest-neighbor sprite sampling now matches the original roster.
Spell rings/projectile/impact, ropegun/tether and medkit are native game effects.
