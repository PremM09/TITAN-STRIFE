# Titan Strife — design checkpoint

## Confirmed direction
Python first; Windows laptop; attempt mobile browser accessibility; original
retro pixel fighting game inspired by the feel of classic arcade fighters.
Five original characters playable and available as CPU opponents. One arena:
Roman-inspired colosseum architecture blended with a spiritual fortress,
ivory stone, muted gold, dusk sky, violet spirit lights. Simplified pixel art,
480x320 overall canvas including controls, with arena in upper 254 pixels.

## Roster
Zen — hard bot, calm strategist, swept dark hair, charcoal/violet jacket with
ivory panel. Kara — mid bot, mysterious operative, burgundy jacket, dark bob,
black trousers. Steve — easy bot, 22, jeans/tee/varsity jacket, taped fists.
Teresa — easy bot, adult law-enforcement detective, badge, practical navy/teal
clothing, tied hair. Jay — mid bot, adult professional wrestler, broad build,
teal/gold wrestling outfit and boots.

Specials and current tuning are documented in README.md. Values are initial
playtest values, not a declaration that the roster is fully balanced.

## Menus
Main: Play, View Characters, Settings.
Play: select fighter -> random non-mirror bot -> round introduction -> match.
Profiles: character description, default bot difficulty and named special.
Settings: music/SFX volume, controls reference, desktop fullscreen; session only.
Results: winner, score, victory pose; New Match, Character Selection, Main Menu.
No saving. Music/effects are original synthesis.

## Important implementation decisions
- Shared commands for player and CPU; difficulty is behavioural.
- Fixed 60 Hz simulation; rendering separated from combat.
- State machine prevents duplicate results/score awards.
- Ties preserve HP; simultaneous KO resets and replays without timer.
- Paused or unfocused gameplay freezes the simulation.
- Browser runtime compatibility and physical mobile performance remain unverified.
- Character art in 0.1 is deliberately provisional, not the final reference quality.

## Next pass after Aizen's playtest
Improve fighter proportions/animation, adjust response and spacing, tune bot
aggression, test special interactions on-device, lengthen music, verify mobile
browser runtime, and prepare hosting only after a reviewable working build.


## Approved visual/combat update (0.2)
Use approved arcade sprite roster for all character menus and combat. Preserve
Zen charcoal/ivory/violet, Kara burgundy tactical, Steve varsity/jeans, Teresa
tan/blue detective uniform, Jay teal/gold wrestling gear. Atlas generated from
approved lineup, 4 core poses each. Bot pacing and impact feedback upgraded;
original match and special rules retained. Full walk/jump/special animations
remain future work; this is not yet a final commercial release.

## Current refinement (0.3; supersedes earlier art notes)
Readable full-resolution UI text, star difficulty ratings and full-arena main menu.
One arena with random day/night lighting. Session-only adaptive opponent weights
from completed match results; no immediate repeat, no mirror match, no fixed order.
Jay now wears full-length teal trousers, a gold rune sash and bracers, with his
muscular torso exposed. Crouch and airborne basic-attack art is integrated.
Body spacing, height-based attack detection, buffered input and basic-only charge
feedback replace the earlier behavior. Blocking successfully preserves own streak.
Original once-per-round special and best-of-three/timeout rules remain unchanged.

## Approval checkpoint: 200 HP revision
Both fighters 200 HP; normal rounds 120 seconds. Kara binds 3 seconds above
100 HP, otherwise 2 seconds, with one damaging hit allowed before the next
breaks the rope. Teresa Field Aid replaces Lockdown: 20 HP at completion of
2-second interruptible self-treatment, capped at200. Jay's wave travels and
deals 35% of remaining HP once on contact; chant interruptible before release, launched wave
persists. Jay now has pixel-matched charge and release poses. 10% shorter CPU
decision pauses, unchanged tier structure. Moderate arcade typography and
WELCOME TO THE ARENA tagline. Jay artwork approved. Final build authorized.

Final correction: Jay deals 35% of remaining target HP at impact, not maximum HP. The tagline is larger, unboxed and below the title. 12 seconds is only the demonstration video length; his animation lasts 1.25 seconds.

## Current 0.5 balance revision (supersedes earlier timer/medkit notes)
Keep 200 HP but restore 60-second rounds. Teresa heals20 immediately at valid
activation, capped200, once per round. Medkit flash is cosmetic with no channel
or recovery lock. CPU decision timers run during recovery; active spacing,
shorter pauses, strike-aware blocks, basic-hit chains and timely earned specials
replace the previous passive behavior. No free special charges or hidden buffs.
Keep Checkmate avoidance, and punish nearby Jay chants before release.

## Approved v5 final moderation
Reduce decision speed and block accuracy for every tier, including Zen. Add occasional CPU-only recovery gaps and enforce burst breathers regardless of streak. Preserve earned specials, Checkmate avoidance, player stats, 60 seconds, 200 HP, instant Teresa heal and Jay 1.25 seconds / 35% remaining HP.

Latest polish review supersedes prior statements that ordinary hits cancel Jay chants. Kara/Jay now resist ordinary cast interruption, still take damage, and remain vulnerable to special interruption/KO. Checkmate recognition is rolled once per activation rather than repeatedly. Four original victory poses integrated.

## Approved 0.6
Restore final-v5 victory art/renderer; discard proposed new victory poses. Checkmate recognition reduced to 15/25/35 percent easy/mid/hard with one decision per activation. Keep tested full-arena Kara/Jay targeting and resistance to ordinary cast interruption; special interrupts and KO remain. General bot difficulty unchanged.
