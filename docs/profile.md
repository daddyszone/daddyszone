# Profile artwork

The root README is the GitHub profile for `daddyszone`. It embeds two self-contained SVGs: the original profile artwork with an ASCII intro and a terminal info card, and a decorative all-green calendar with real contribution totals. There are no external widget services or personal access tokens.

## Edit your details

Edit `data/profile/profile.json`, then run `python scripts/profile/generate.py`. Commit the configuration and generated SVGs. The detailed portrait uses your public GitHub avatar, saved in `data/profile/avatar-source.png`. Its 144 × 88 character grid is stored in `data/profile/portrait.json`. To rebuild, install `scripts/profile/requirements-portrait.txt` and run `python scripts/profile/make_portrait.py`, then `python scripts/profile/generate.py`. The portrait rebuild runs on configuration pushes and manual workflow runs; daily scheduled updates reuse the committed portrait. The original PNG is embedded unchanged in the SVG and becomes fully visible after the short ASCII introduction, preserving the face and glasses. The standalone `assets/profile/avatar.svg` provides a full-size view.

## Refresh the contribution calendar

Run `python scripts/profile/generate.py --fetch` with Python 3.10 or newer. There are no pip dependencies. This fetches GitHub's public contribution HTML, checks that all dates and counts are present, and regenerates the artwork. A fetch or parsing failure fails the workflow and leaves the last committed artwork available.

The **Update profile art** workflow runs daily at 06:17 UTC (11:47 AM India time), on relevant configuration changes, or manually from Actions. GitHub may delay scheduled runs. It uses the built-in workflow token with repository contents write permission to commit only the profile SVGs and calendar JSON. No secret setup is required. Repository policy must allow Actions and workflow writes.

The figures match the public GitHub contribution calendar, including any anonymized private contribution counts that you have chosen to display. No private repository names or activity are fetched.

The portrait transitions once from ASCII to the original artwork on image load. The decorative calendar assembles with a staggered entrance, followed by looping green color waves, a scanning beam, pulse rings on every box, and a moving border highlight. Every day is deliberately colored green regardless of activity, and the graphic clearly labels these colors as decorative. Contribution totals, active-day totals, best-day counts, and per-date tooltips still use real GitHub data. The density legend is removed because color no longer measures activity. Reduced-motion preferences disable all calendar animation and hide decorative moving overlays, leaving the complete static chart visible. Without animation support, the final artwork is visible. GitHub or browser image caching can delay a refresh.

Design approach inspired by [Avi Vashishta's animated README guide](https://www.avivashishta.com/blog/build-animated-github-profile-readme); the generator and artwork here are original implementations.

The existing Scope Starter site and its Pages workflow are independent of the profile artwork. The previous malformed README content is retained in `docs/previous-profile-readme.md` for reference.
