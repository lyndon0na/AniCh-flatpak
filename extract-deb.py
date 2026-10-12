#!/usr/bin/env python3
"""Unpack a Debian .deb into a directory tree.

flatpak runs the caller (apply_extra) at install and update time inside a
sandbox that has no network, no host access and only a handful of tools. The
GNOME runtime ships python3, tar and zstd, but not `ar` or `dpkg-deb`, and a
.deb is an ar archive - so the ar container is parsed here rather than shelled
out to a tool that may not exist.

Only the data member is extracted. The control member (maintainer scripts,
conffiles, md5sums) is Debian packaging metadata with no meaning inside a
Flatpak, and the caller does not need it.
"""

import gzip
import io
import lzma
import os
import sys
import tarfile

try:
    # Python 3.14+; the GNOME 51 runtime ships 3.14.
    from compression import zstd
except ImportError:  # pragma: no cover - only on older interpreters
    zstd = None


def ar_members(path):
    """Yield (name, data) for every member of a POSIX/GNU ar archive."""
    with open(path, "rb") as archive:
        if archive.read(8) != b"!<arch>\n":
            raise SystemExit(f"{path}: not an ar archive")
        while True:
            header = archive.read(60)
            if len(header) < 60:  # end of archive
                return
            if header[58:60] != b"`\n":
                raise SystemExit(f"{path}: corrupt ar header")
            name = header[:16].decode("ascii", "replace").strip()
            size = int(header[48:58].decode("ascii").strip())
            data = archive.read(size)
            if size % 2:  # members are padded to an even offset
                archive.read(1)
            yield name.rstrip("/"), data


def data_tar_bytes(members):
    """Return the decompressed bytes of the deb's data.tar.* member."""
    for name, data in members:
        if not name.startswith("data.tar"):
            continue
        if name.endswith(".zst"):
            if zstd is None:
                raise SystemExit("data.tar.zst needs python3.14+ (compression.zstd)")
            return zstd.decompress(data)
        if name.endswith(".xz"):
            return lzma.decompress(data)
        if name.endswith(".gz"):
            return gzip.decompress(data)
        return data
    raise SystemExit("no data.tar member in the .deb")


def main(argv):
    if len(argv) != 3:
        raise SystemExit(f"usage: {argv[0]} DEB DEST")
    deb, dest = argv[1], argv[2]
    blob = data_tar_bytes(ar_members(deb))
    os.makedirs(dest, exist_ok=True)
    # The `data` filter sanitises paths and mode bits (no absolute paths, no
    # "..", no setuid/setgid), which is what a member of an untrusted archive
    # needs; it keeps the owner execute bit, so the launcher stays executable.
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        tar.extractall(dest, filter="data")


if __name__ == "__main__":
    main(sys.argv)
