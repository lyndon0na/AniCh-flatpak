# Packaging notes

Why this Flatpak is built the way it is. The interesting constraints are all
about how AniCh ships for Linux and what is available inside the sandbox at
install time.

## Why extra-data

Upstream publishes a single self-contained Linux artifact, so the Flatpak does
not build anything. Declaring that artifact as an [extra-data][] source means:

* flatpak-builder records the URL, sha256 and size in the app metadata and never
  downloads the file;
* flatpak downloads it on the machine where the app is installed, at install and
  at every update, and verifies the sha256 before running `apply_extra`;
* this repository ships only the desktop metadata, the entry point and two small
  helper scripts.

The consequence worth knowing is that a `.flatpak` bundle is not an install
path: `flatpak build-bundle` does not copy the detached metadata that holds the
extra-data record, so installing a bundle fails with `Extra data missing in
detached metadata`. The OSTree repository published over GitHub Pages, reached
through the `.flatpakref`, is the only way to install this.

[extra-data]: https://docs.flatpak.org/en/latest/module-sources.html#extra-data

## Why the `.deb`, and not the `.zip`

Upstream's Linux releases carry both `anich-linux-<version>.deb` and
`anich-linux-<version>.zip`. The two hold the exact same tree - the `anich`
launcher, `lib/` with the Flutter engine and plugins, and `data/` with the
Flutter assets and `icudtl.dat` - and the launcher binary is byte-identical
between them.

The `.deb` is used here for continuity with the previous packaging, which also
extracted the `.deb`. It costs one extra step: a `.deb` is an `ar` archive
holding `data.tar.zst`, and the install-time sandbox has no `ar` and no
`dpkg-deb`. Hence `extract-deb.py`: it walks the 60-byte ar headers itself and
decompresses the member with Python's `compression.zstd`, both of which the
GNOME 51 runtime provides (Python 3.14). If the extra step is ever unwanted,
pointing the manifest at the `.zip` and unzipping it would remove the script
entirely.

## Layout the launcher expects

The launcher is a Flutter GTK application with `RUNPATH = $ORIGIN/lib`, and the
Flutter embedder locates `data/` relative to `/proc/self/exe`. So the tree has
to keep `anich`, `lib/` and `data/` together:

```
/app/extra/anich/
├── anich          # launcher, RUNPATH=$ORIGIN/lib
├── data/          # flutter_assets/, icudtl.dat
└── lib/           # libapp.so, libflutter_linux_gtk.so, libmpv.so.2, plugins
```

`anich-wrapper` (`/app/bin/anich`) `exec`s the launcher directly rather than
through a shell, so `/proc/self/exe` resolves to the real path inside
`/app/extra/anich`. That is what makes both the RUNPATH and the `data/` lookup
work without touching `LD_LIBRARY_PATH`.

## The old manifest, and why "it would not open"

The previous manifest pinned AniCh 1.5.18 and extracted `usr/share/anich/`.
Upstream moved the payload to `/opt/anich/` in a later release, so the extract
paths no longer match any current release - the manifest was both old and
pointed at a layout that no longer exists. On top of that, 1.5.18 predates
several upstream changes and its service endpoints are gone, so the app had
nothing to connect to. Repackaging the current release through extra-data fixes
both: the payload is fetched fresh at install time, and `apply_extra` extracts
whatever layout upstream ships instead of hard-coding one.

## App ID and metadata

The App ID stays `org.eu.emmmm.anich`, matching the previous packaging, so
existing installs update in place rather than needing the remote re-added. The
launcher's window class is `anich`, which is what `StartupWMClass` in the
desktop file uses (verified by running the binary under an X11 backend and
reading `WM_CLASS`).

Icons are generated from the single 512×512 PNG that the previous packaging
shipped; AppStream wants at least 128 and 256 alongside it.

## Permissions

The app is a network media player: it needs `--share=network`, audio, GPU access
(`--device=dri`) for VA-API and Skia, and the screen-saver inhibition call it
makes through `org.freedesktop.ScreenSaver` while a video plays. It requests no
host filesystem access. Everything it writes - downloads, cache, the Anime4K
shaders copied to `~/.local/share/anich/shaders` on first run, and the database -
lands under `~/.var/app/org.eu.emmmm.anich/`, which the sandbox always provides.
A user who wants the app to save into a real folder grants it explicitly (see
the README).
