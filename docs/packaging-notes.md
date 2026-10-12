# Packaging notes

Technical notes on how this Flatpak is built: how the payload reaches the
machine, how it is unpacked, the layout the launcher needs, and the permissions
the app requests.

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

## The `.deb` source and how it is unpacked

Upstream's Linux releases carry both `anich-linux-<version>.deb` and
`anich-linux-<version>.zip`. The two hold the same tree - the `anich` launcher,
`lib/` with the Flutter engine and plugins, and `data/` with the Flutter assets
and `icudtl.dat` - and the launcher binary is byte-identical between them. The
`.deb` is declared as the extra-data source.

A `.deb` is an `ar` archive holding `data.tar.zst`, and the install-time sandbox
has no `ar` and no `dpkg-deb`, so `apply_extra` calls `extract-deb.py`:

* it walks the 60-byte ar headers itself and picks the `data.tar.*` member;
* it decompresses it with Python's `compression.zstd`;
* it extracts the tar under `/app/extra`, then `apply_extra` moves
  `opt/anich/` to `/app/extra/anich` and drops the deb's own `.desktop` and
  icons, which this package does not use.

Both prerequisites come from the GNOME 51 runtime (Python 3.14, `libzstd`).
Pointing the manifest at the `.zip` instead and unzipping it would remove the
helper script, since a zip needs nothing beyond Python's standard library.

## Layout the launcher expects

The launcher is a Flutter GTK application with `RUNPATH = $ORIGIN/lib`, and the
Flutter embedder locates `data/` relative to `/proc/self/exe`. The tree has to
keep `anich`, `lib/` and `data/` together:

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

## App ID, window class and icons

The App ID is `org.eu.emmmm.anich`. The launcher's window class is `anich`, which
is what `StartupWMClass` in the desktop file carries.

Icons are the 128 / 256 / 512 PNGs under `icons/`; AppStream wants at least the
128 and 256 alongside the 512.

## Permissions

The app is a network media player: it needs `--share=network`, audio, GPU access
(`--device=dri`) for VA-API and Skia, and the screen-saver inhibition call it
makes through `org.freedesktop.ScreenSaver` while a video plays. It requests no
host filesystem access. Everything it writes - downloads, cache, the Anime4K
shaders copied to `$XDG_DATA_HOME/anich/shaders` on first run, and the config
Hive databases - lands under `~/.var/app/org.eu.emmmm.anich/`, which the sandbox
always provides. A user who wants the app to save into a real folder grants it
explicitly (see the README).
