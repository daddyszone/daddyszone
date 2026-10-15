# Profile artwork

The root README is the GitHub profile for `daddyszone`. It embeds two self-contained SVGs: a detailed text-only ASCII portrait with a terminal info card, and a decorative all-green calendar with real contribution totals. There are no external widget services or personal access tokens.

## Edit your details

Edit `data/profile/profile.json`, then run `python scripts/profile/generate.py`. Commit the configuration and generated SVGs.

The portrait is a 224-column by 136-row character grid generated from the supplied high-resolution reference, with a tighter head-and-shoulders crop and 16 levels of grayscale text shading. The character and tone rows are stored in `data/profile/portrait.json`. The displayed SVG contains only text and vector framing: no embedded photo, raster image, or photo-reveal animation.

To convert a new high-resolution reference, install `scripts/profile/requirements-portrait.txt`, run `python scripts/profile/make_portrait.py --source path/to/reference.png`, then run `python scripts/profile/generate.py`. Without `--source`, the converter uses the previously saved public GitHub avatar. Source image files are input to the conversion only; they are never embedded by the SVG generator. The standalone `assets/profile/avatar.svg` provides a full-size ASCII view.

All workflow runs reuse the committed character grid. This prevents a daily refresh or unrelated edit from replacing the approved high-detail portrait with a lower-resolution conversion.

## Refresh the contribution calendar

Run `python scripts/profile/generate.py --fetch` with Python 3.10 or newer. There are no pip dependencies. This fetches GitHub's public contribution HTML, checks that all dates and counts are present, and regenerates the artwork. A fetch or parsing failure fails the workflow and leaves the last committed artwork available.

The **Update profile art** workflow runs daily at 06:17 UTC (11:47 AM India time), on relevant configuration changes, or manually from Actions. GitHub may delay scheduled runs. It uses the built-in workflow token with repository contents write permission to commit only the profile SVGs and calendar JSON. No secret setup is required. Repository policy must allow Actions and workflow writes.

The figures match the public GitHub contribution calendar, including any anonymized private contribution counts that you have chosen to display. No private repository names or activity are fetched.

The ASCII portrait reveals its rows once on image load and remains ASCII afterward. The decorative calendar assembles with a staggered entrance, followed by looping green color waves, a scanning beam, pulse rings on every box, and a moving border highlight. Every day is deliberately colored green regardless of activity, and the graphic clearly labels these colors as decorative. Contribution totals, active-day totals, best-day counts, and per-date tooltips still use real GitHub data. The density legend is removed because color no longer measures activity. Reduced-motion preferences disable all calendar animation and hide decorative moving overlays, leaving the complete static chart visible. Without animation support, the final artwork is visible. GitHub or browser image caching can delay a refresh.

Design approach inspired by [Avi Vashishta's animated README guide](https://www.avivashishta.com/blog/build-animated-github-profile-readme); the generator and artwork here are original implementations.

The existing Scope Starter site and its Pages workflow are independent of the profile artwork. The previous malformed README content is retained in `docs/previous-profile-readme.md` for reference.
