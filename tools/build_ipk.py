#!/usr/bin/env python3
"""Build a webOS IPK from an app folder, without LG's ares-package.

    python3 build_ipk.py <app-dir> [out-dir]

The package mirrors what ares-package produces for this app in CI, which is
the layout known to install:
    ar archive: debian-binary, control.tar.gz, data.tar.gz
    data tree : usr/palm/applications/<id>/...            the app folder
                usr/palm/packages/<id>/packageinfo.json   id, version, app
    control   : Architecture is "arm" for a native ARM app, "all" otherwise
"""
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

EXCLUDE = {'.git', 'node_modules', 'test', 'build', '__pycache__'}

EM_ARM = 40


def package_arch(app_dir: Path, meta: dict) -> str:
    """ares-package labels a native app with the architecture of its executable.

    Only 32-bit ARM, the one webOS TV target, has been observed; anything else stays "all".
    """
    if meta.get('type') != 'native':
        return 'all'
    with open(app_dir / meta['main'], 'rb') as fh:
        header = fh.read(20)
    if len(header) < 20 or header[:4] != b'\x7fELF':
        return 'all'
    machine = int.from_bytes(header[18:20], 'little' if header[5] == 1 else 'big')
    return 'arm' if machine == EM_ARM else 'all'


def add_tree(tar: tarfile.TarFile, src: Path) -> None:
    """Add everything below src, directories included, under paths relative to src."""
    for root, dirs, files in os.walk(src):
        dirs.sort()
        rel = Path(root).relative_to(src)
        for name in dirs + sorted(files):
            path = Path(root) / name
            info = tar.gettarinfo(str(path), arcname=str(rel / name))
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
            if info.isdir():
                tar.addfile(info)
            else:
                with open(path, 'rb') as fh:
                    tar.addfile(info, fh)


def ar_member(name: str, payload: bytes) -> bytes:
    # match LG's own packs: bare name, mode 100644, no trailing slash
    header = (
        f"{name:<16}"
        f"{0:<12}{0:<6}{0:<6}{'100644':<8}{len(payload):<10}"
        "`\n"
    ).encode()
    body = payload + (b'\n' if len(payload) % 2 else b'')
    return header + body


def build(app_dir: Path, out_dir: Path) -> Path:
    meta = json.loads((app_dir / 'appinfo.json').read_text())
    app_id = meta['id']
    version = str(meta.get('version', '1.0.0'))
    title = meta.get('title', app_id)
    arch = package_arch(app_dir, meta)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        data_root = Path(tmp) / 'data'
        payload_root = data_root / 'usr' / 'palm' / 'applications' / app_id
        payload_root.mkdir(parents=True)
        # Symlinks are followed: the package carries plain files, as ares-package's does
        shutil.copytree(app_dir, payload_root, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns(*EXCLUDE, '*.ipk', '.DS_Store'))

        package_root = data_root / 'usr' / 'palm' / 'packages' / app_id
        package_root.mkdir(parents=True)
        (package_root / 'packageinfo.json').write_text(
            json.dumps({'id': app_id, 'version': version, 'app': app_id}, indent=2) + '\n')

        data_buf = io.BytesIO()
        with tarfile.open(fileobj=data_buf, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
            add_tree(tar, data_root)
        data_bytes = data_buf.getvalue()

        control = (
            f"Package: {app_id}\n"
            f"Version: {version}\n"
            "Section: misc\n"
            "Priority: optional\n"
            f"Architecture: {arch}\n"
            f"Installed-Size: {sum(f.stat().st_size for f in data_root.rglob('*') if f.is_file())}\n"
            "Maintainer: heyitworked <noreply@github.com>\n"
            f"Description: {title}\n"
            "webOS-Package-Format-Version: 2\n"
            "webOS-Packager-Version: x.y.x\n"
        ).encode()

        ctrl_buf = io.BytesIO()
        with tarfile.open(fileobj=ctrl_buf, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
            info = tarfile.TarInfo('control')
            info.size = len(control)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(control))
        ctrl_bytes = ctrl_buf.getvalue()

        ipk = out_dir / f"{app_id}_{version}_{arch}.ipk"
        with open(ipk, 'wb') as fh:
            fh.write(b'!<arch>\n')
            fh.write(ar_member('debian-binary', b'2.0\n'))
            fh.write(ar_member('control.tar.gz', ctrl_bytes))
            fh.write(ar_member('data.tar.gz', data_bytes))
        return ipk


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    app = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path('/tmp/ipk-out')
    ipk = build(app, out)
    print(ipk)
    print(f"  {ipk.stat().st_size} bytes")
