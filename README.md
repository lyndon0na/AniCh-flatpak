# AniCh Flatpak Packaging

Build configuration that repackages the official Linux `.deb` as a Flatpak.

**English** | [简体中文](README.zh-CN.md) | [Packaging notes](docs/packaging-notes.md)

## App info

| | |
|---|---|
| Name | AniCh |
| Version | 1.5.27 |
| App ID | `org.eu.emmmm.anich` |
| Runtime | `org.gnome.Platform` 51 |
| Architecture | x86_64 |
| Upstream source | https://github.com/Sle2p/AniCh |
| Homepage | https://anich.emmmm.eu.org |
| App payload | the upstream `anich-linux-1.5.27.deb`, declared as an [extra-data](https://docs.flatpak.org/en/latest/module-sources.html#extra-data) source: flatpak downloads it on the machine where the app is installed, verifies its sha256, and `apply_extra` unpacks it there |

## Installation

### From the repository

```sh
flatpak install --user https://<user>.github.io/AniCh-flatpak/org.eu.emmmm.anich.flatpakref
```

This adds the remote as well, so later versions arrive through `flatpak update`
(or through the desktop's software centre). Installing downloads the ~22 MB
`.deb` from GitHub, which is where the application itself comes from.

### Build locally

```sh
# dependencies
sudo dnf install flatpak flatpak-builder      # Fedora
sudo apt install flatpak flatpak-builder      # Debian / Ubuntu

# Flathub, plus the GNOME runtime and SDK
flatpak remote-add --if-not-exists --user flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install --user flathub org.gnome.Platform//51 org.gnome.Sdk//51

# clone and build
git clone https://github.com/lyndon0na/AniCh-flatpak.git
cd AniCh-flatpak
flatpak-builder --user --install --force-clean --repo=repo build org.eu.emmmm.anich.yml
```

Building needs no `.deb`: it is an extra-data source, so the build only uses
the runtime and the SDK. The `.deb` is pulled on the machine where the app is
installed, from the upstream release URL, checked against the sha256 recorded in
the manifest.

### Why there is no bundle

A bundle cannot carry the extra-data record: it lives in the commit's detached
metadata, which `flatpak build-bundle` does not include, so installing one fails
with `Extra data missing in detached metadata`. The repository published over
GitHub Pages is therefore the only install path.

## Run

```sh
flatpak run org.eu.emmmm.anich
```

## Uninstall

```sh
flatpak uninstall --user org.eu.emmmm.anich
```

Flatpak will ask whether to delete the app data in
`~/.var/app/org.eu.emmmm.anich/` as well.

## Permissions

| Permission | Purpose |
|---|---|
| `--share=network` | Online anime sources, danmaku APIs and DoH resolution |
| `--share=ipc` | X11 shared memory for the fallback X11 path |
| `--socket=wayland` | Wayland support |
| `--socket=fallback-x11` | X11 fallback |
| `--socket=pulseaudio` | Audio playback |
| `--device=dri` | GPU rendering and VA-API hardware decoding |
| `--talk-name=org.freedesktop.ScreenSaver` | Inhibit the screen saver and sleep while a video plays |
| `--talk-name=org.freedesktop.Notifications` | Download and playback notifications |

No host filesystem access is requested. Everything the app stores by default -
the downloaded media, the cache, the Anime4K shaders it copies at first run and
the database - lives in `~/.var/app/org.eu.emmmm.anich/`, which the sandbox
always provides. Pointing the app at a real path therefore needs a grant too:
the folder picker will happily show you `~/Videos`, but the app cannot read or
write it until you allow it.

```sh
flatpak override --user --filesystem=xdg-download org.eu.emmmm.anich
```

Use `--filesystem=home` for the whole home directory, or do the same per app in
Flatseal.

## Files

| File | Purpose |
|---|---|
| `org.eu.emmmm.anich.yml` | Flatpak manifest (GNOME runtime 51) |
| `apply_extra` | runs at install and update time: unpacks the `.deb` |
| `extract-deb.py` | parses the `.deb` ar container and extracts `data.tar.zst`; executed by `apply_extra` |
| `anich-wrapper` | `/app/bin/anich` entry point |
| `org.eu.emmmm.anich.desktop` | launcher entry |
| `org.eu.emmmm.anich.metainfo.xml` | AppStream metadata |
| `icons/org.eu.emmmm.anich-*.png` | installed icons (128 / 256 / 512) |
| `org.eu.emmmm.anich.flatpakref.in` | template for the one-line install, filled in and published by CI |
| `org.eu.emmmm.anich.flatpakrepo.in` | same, for adding the remote by hand |
| `.github/workflows/build.yml` | CI: builds, verifies, publishes the repository and the release |
| `.github/workflows/upstream.yml` | daily upstream check, opens a bump pull request |
| `docs/` | [Packaging notes](docs/packaging-notes.md) |
| `LICENSE` | CC0-1.0 (packaging only; the app is proprietary) |

## CI

`.github/workflows/build.yml`:

* a push to `main` or a manual dispatch builds, installs and verifies the
  deployed tree;
* a `v*` tag additionally signs the build, updates the published repository and
  creates a GitHub release;
* `.github/workflows/upstream.yml` runs daily: when Sle2p/AniCh publishes a newer
  release it opens a pull request that points the manifest at it. Merging that
  pull request does not publish anything - the tag does.

The runner is headless, so the GUI smoke test runs under Xvfb as a best-effort
step that reports without failing the build. The structural checks are gating.

```sh
git tag v1.5.27
git push origin v1.5.27
```

## Publishing

A tag publishes the repository, and that needs a few things set up once:

1. **`GPG_PRIVATE_KEY`** as a repository secret: the ASCII-armoured private key
   of the signing key. CI derives the key id and the public key from it, signs
   the commit and the repository summary, and writes the public key into the
   descriptors.
2. **GitHub Pages** serving the `gh-pages` branch (Settings → Pages → Source).
   Every tag pushes the OSTree repository, `org.eu.emmmm.anich.flatpakref`,
   `org.eu.emmmm.anich.flatpakrepo` and an icon to that branch.
3. **Pull requests from Actions** allowed (Settings → Actions → General →
   Workflow permissions), otherwise the daily upstream check cannot open its
   bump pull request.

To release a new version, edit `url`, `sha256` and `size` in the manifest (and
the `<release>` entry in the metainfo), commit, and tag.

Unlike a JVM or CEF app, this payload is only ~22 MB, so a new published commit
is cheap. flatpak still re-downloads and re-applies extra data whenever the
commit changes, even when the extra-data record did not, so batch unrelated
changes into one tag anyway.

The descriptors committed here are templates: `@PAGES_URL@` and `@GPGKEY@` are
substituted at publish time, so no key material is in the repository.

## Notes

* This is **unofficial** packaging. Upstream does not support it; please file
  issues against this repository.
* The app is downloaded from GitHub when you install or update, not shipped by
  this repository. If upstream ever deletes a release asset, new installs break
  until the sha256 in the manifest is pointed at a new one.
* App state lives in `~/.var/app/org.eu.emmmm.anich/`, fully separate from a
  system-installed AniCh.

## License

The application and the icon artwork come from [Sle2p/AniCh](https://github.com/Sle2p/AniCh)
and are proprietary. This repository only provides the packaging configuration,
which is released under [CC0-1.0](LICENSE).

## Links

* [AniCh homepage](https://anich.emmmm.eu.org)
* [AniCh source](https://github.com/Sle2p/AniCh)
* [Packaging notes](docs/packaging-notes.md)
* [Releases](../../releases)
