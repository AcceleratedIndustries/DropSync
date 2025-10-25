Questions (please number your answers)

Repo & metadata
1.1. GitHub username/org to create the repo under?
1.2. Preferred repo name (e.g., sync-inbox)?
1.3. License (MIT, Apache-2.0, GPL-3.0, proprietary)?
1.4. Author name/email for git and copyright?

Target platforms
2.1. Primary target OS: Arch Linux (you)? Any others to support in docs (Debian/Ubuntu, macOS)?
2.2. CPU/arch assumptions (x86_64 ok)?

Tech choices
3.1. Keep the collector in Python 3 with a simple built-in HTTP server, or prefer FastAPI/Flask?
3.2. Package as: (a) bare Python + systemd user service (default), (b) pipx app, or (c) Docker/Podman container too?
3.3. Config format: TOML (default), YAML, or .env?

Syncthing paths & structure
4.1. Root synced dir path (default ~/Sync/Collect)?
4.2. Keep subfolders links/ notes/ code/ media/ files/ as proposed? Any additions/renames?

Capture & processing features
5.1. Enable these helpers by default: yt-dlp, gallery-dl, readability-cli, monolith (single-file HTML snapshot)?
5.2. Any extra helpers (e.g., trafilatura for article parsing, OCR via tesseract for images/PDFs)?
5.3. File-naming convention ok as YYYYMMDD-HHMMSS--Title.ext?
5.4. Include optional front matter (YAML/TOML) in saved Markdown for later tooling (title, url, tags, domain, timestamp)?

Security & networking
6.1. Bind only to 127.0.0.1:8765 (default) or allow LAN?
6.2. If LAN: require a secret token header? (I recommend yes.)
6.3. Any CORS allowances (e.g., for a local web capture page)?

Browser & UX
7.1. Support bookmarklet + clipboard hotkeys (Niri/Hyprland examples) + file manager context menu?
7.2. Also ship a minimal web UI page (/capture) for pasting/sending links & notes?

Automation
8.1. Include a nightly systemd timer to auto-organize processed items (e.g., move items after .readable.md exists, tag by domain)? If yes, define basic rules or keep as examples?
8.2. Include sample rules for “video → media/ by site,” “images via gallery-dl → dated subfolders”?

Quality & CI
9.1. Python version pin (e.g., >=3.11)?
9.2. Linters/formatters: ruff + black + mypy?
9.3. Add GitHub Actions for lint/test on PRs and releases?
9.4. Include unit tests for the HTTP handlers and file writers (pytest)?

Docs & packaging
10.1. Provide INSTALL.md with Arch (pacman + yay) and Debian instructions?
10.2. Include systemd user units, example Hyprland/Niri bindings, and file-manager actions (Nautilus/Thunar/Dolphin)?
10.3. Provide a quickstart that completes in <5 minutes on Arch.
10.4. Include an Uninstall guide.

Releases & versioning
11.1. Semantic versioning starting at v0.1.0 okay?
11.2. Include a CHANGELOG.md (Keep a Changelog format)?
11.3. GitHub Release notes template?

Publishing to GitHub
12.1. I’ll script git init, initial commit, and a push step—but you’ll need to provide a GitHub PAT locally. Should the script:
- Prompt for GH_TOKEN env var or read from ~/.config/gh/hosts.yml (if GitHub CLI is present)?
- Create the repo via gh repo create (preferred) or raw API?

Extras (optional)
13.1. Provide a minimal Tray icon (Linux) to show “collector running” and “last capture OK”?
13.2. Sample monolith and readability tuning presets (max length, sanitize, etc.)?
13.3. A simple domain-rules.toml so users can add per-site behaviors without code edits.

Once you reply, I’ll generate a single, very complete Codex prompt that will:

scaffold the project;

implement the collector + helpers + systemd units;

include docs, CI, tests, and installer scripts;

and perform an initial GitHub push from your machine.

--------------------------------------------------------------------

Open questions 1: BSD-2-Clause license
2: pin to 3.11
3: yes default to loopback and network token disabled
4: we should discuss number 4 after I finish the current round.
5: include 'on' with sane defaults.
6: enabled by default - but easy to change.  phase 2 of the project might be to create user interfaces for checking/setting of defaults and monitoring operations etc. maybe part of web ui/
7: web ui please and we'll include the /capture page in the v0.1.0
8: we will discuss further regarding github actions (I haven't used them, I've been a Jenkins guy for the last 12 years or so at my former employer)
9: we can put them on the repo page, I'm not sure about readme.  I need more context. :)
10: I've created the repo as DropSync (camel case). See attached image.
11: yes
12: oops.  I've created the repo.  github cli is installed. but the Makefile can use gh cli in the Publish target (or whatever we call the push to github makefile target)
