# Profile artwork

The root README is the GitHub profile for `daddyszone`. It embeds two self-contained SVGs: an animated ASCII avatar with a terminal info card, and a live contribution calendar. There are no external widget services or personal access tokens.

## Edit your details

Edit `data/profile/profile.json`, then run `python scripts/profile/generate.py`. Commit the configuration and generated SVGs. The portrait uses your public GitHub avatar as captured on October 15, 2026; its character rows are stored in `data/profile/portrait.json`. It stays fixed until you replace those rows.

## Refresh the contribution calendar

Run `python scripts/profile/generate.py --fetch` with Python 3.10 or newer. There are no pip dependencies. This fetches GitHub's public contribution HTML, checks that all dates and counts are present, and regenerates the artwork. A fetch or parsing failure fails the workflow and leaves the last committed artwork available.

The **Update profile art** workflow runs daily at 06:17 UTC (11:47 AM India time), on relevant configuration changes, or manually from Actions. GitHub may delay scheduled runs. It uses the built-in workflow token with repository contents write permission to commit only the profile SVGs and calendar JSON. No secret setup is required. Repository policy must allow Actions and workflow writes.

The figures match the public GitHub contribution calendar, including any anonymized private contribution counts that you have chosen to display. No private repository names or activity are fetched.

Animations play once on image load and respect reduced-motion preferences. Without animation support, the final artwork is visible. GitHub or browser image caching can delay a refresh.

Design approach inspired by [Avi Vashishta's animated README guide](https://www.avivashishta.com/blog/build-animated-github-profile-readme); the generator and artwork here are original implementations.

The existing Scope Starter site and its Pages workflow are independent of the profile artwork. The previous malformed README content is retained in `docs/previous-profile-readme.md` for reference.
