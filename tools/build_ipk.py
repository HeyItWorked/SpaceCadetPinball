#!/usr/bin/env python3
"""Build a webOS IPK from an app folder. No ares, no platform ar quirks.

Vendored so CI and a laptop produce the same bytes-shaped package: LG's dev
installer expects an ar archive of debian-binary, control.tar.gz, data.tar.gz
with the app under usr/palm/applications/<id>/.

    python3 build_ipk.py <app-dir> [out-dir]

Format LG's dev installer expects:
    ar archive: debian-binary, control.tar.gz, data.tar.gz
    data tree : usr/palm/applications/<id>/...
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


def add_tree(tar: tarfile.TarFile, src: Path, arcname: str) -> None:
    for root, dirs, files in os.walk(src):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE)
        rel = Path(root).relative_to(src)
        for name in sorted(files):
            if name.endswith('.ipk') or name == '.DS_Store':
                continue
            path = Path(root) / name
            info = tar.gettarinfo(str(path), arcname=str(Path(arcname) / rel / name))
            info.uid = info.gid = 0
            info.uname = info.gname = 'root'
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
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        payload_root = tmp / 'data' / 'usr' / 'palm' / 'applications' / app_id
        payload_root.mkdir(parents=True)
        add_tree_dir = shutil.copytree(app_dir, payload_root, dirs_exist_ok=True,
                                       ignore=shutil.ignore_patterns(*EXCLUDE, '*.ipk'))

        data_buf = io.BytesIO()
        with tarfile.open(fileobj=data_buf, mode='w:gz', format=tarfile.GNU_FORMAT) as tar:
            add_tree(tar, payload_root, 'usr/palm/applications/' + app_id)
        data_bytes = data_buf.getvalue()

        control = (
            f"Package: {app_id}\n"
            f"Version: {version}\n"
            "Section: misc\n"
            "Priority: optional\n"
            "Architecture: all\n"
            f"Installed-Size: {sum(f.stat().st_size for f in payload_root.rglob('*') if f.is_file())}\n"
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

        ipk = out_dir / f"{app_id}_{version}_all.ipk"
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
