"""Dependency-free, source-bound PvZ2 resource patch installer (Python 3.11+)."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

PACKAGE = 'com.ea.game.pvz2_row'
NAMES = {'obb': 'main.1055.com.ea.game.pvz2_row.obb', 'cdn': 'LawnStrings-en-us.rton'}
REMOTE = {'obb': '/sdcard/Android/obb/' + PACKAGE + '/' + NAMES['obb'],
          'cdn': '/sdcard/Android/data/' + PACKAGE + '/files/No_Backup/CDN.13.4/' + NAMES['cdn']}

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def apply(source, delta, output, entry):
    source, delta, output = map(Path, (source, delta, output))
    require(not output.exists() and output.resolve() != source.resolve(), 'Output already exists or aliases input')
    require(sha(delta) == entry['patch_sha256'], 'Patch damaged')
    require(sha(source) == entry['source_sha256'], 'Unsupported original resource; version/hash must match')
    with zipfile.ZipFile(delta) as z:
        require(set(z.namelist()) == {'ops.json', 'literal.bin'}, 'Unexpected patch members')
        require(z.getinfo('ops.json').file_size < 32 * 1024 * 1024, 'Oversized patch metadata')
        ops = json.loads(z.read('ops.json'))
        total = 0
        literals = 0
        for kind, offset, size in ops:
            require(type(offset) is int and type(size) is int and offset >= 0 and size > 0, 'Invalid patch range')
            require(kind in ('copy', 'literal'), 'Invalid patch operation')
            limit = source.stat().st_size if kind == 'copy' else z.getinfo('literal.bin').file_size
            require(offset + size <= limit, 'Patch range exceeds source')
            if kind == 'literal':
                require(offset == literals, 'Nonsequential literal data')
                literals += size
            total += size
        require(total == entry['target_bytes'] and literals == z.getinfo('literal.bin').file_size, 'Patch size mismatch')
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.patch-', delete=False) as target:
                temp = Path(target.name)
                with source.open('rb') as original, z.open('literal.bin') as literal:
                    for kind, offset, size in ops:
                        reader = original if kind == 'copy' else literal
                        if kind == 'copy':
                            reader.seek(offset)
                        while size:
                            block = reader.read(min(size, 1024 * 1024))
                            require(bool(block), 'Truncated patch/input')
                            target.write(block)
                            size -= len(block)
            require(sha(temp) == entry['target_sha256'], 'Generated output hash mismatch')
            require(not output.exists(), 'Output appeared during patching')
            # link is exclusive: never replace an existing destination.
            import os
            os.link(temp, output)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)

class Device:
    def __init__(self, adb, serial):
        self.adb, self.serial = adb, serial

    def call(self, *args):
        p = subprocess.run([self.adb, '-s', self.serial, *map(str, args)], capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=900)
        require(p.returncode == 0, 'ADB failed: ' + p.stderr[-700:])
        return p.stdout.strip()

    def preflight(self):
        require(self.call('get-state') == 'device', 'Authorize USB debugging on the phone')
        info = self.call('shell', 'dumpsys', 'package', PACKAGE)
        require(re.search(r'versionName=13\.4\.1(?:\s|$)', info) and
                re.search(r'versionCode=1055(?:\s|$)', info), 'Only ROW 13.4.1 / 1055 is supported')

    def hashes(self):
        return {k: self.call('shell', 'sha256sum', v).split()[0].lower() for k, v in REMOTE.items()}

    def stop(self):
        self.call('shell', 'am', 'force-stop', PACKAGE)

    def pull(self, key, path):
        self.call('pull', REMOTE[key], path)

    def push(self, key, path):
        self.call('push', path, REMOTE[key])

def install(device, root, manifest, backup_root):
    device.preflight()
    current = device.hashes()
    entries = manifest['resources']
    targets = {k: e['target_sha256'] for k, e in entries.items()}
    if current == targets:
        return {'status': 'ALREADY_INSTALLED_HASH_VERIFIED', 'hashes': current}
    for k, entry in entries.items():
        require(current[k] in (entry['source_sha256'], entry['target_sha256']), 'Unsupported current ' + k + '; no device writes')
        require(sha(root / entry['patch']) == entry['patch_sha256'], 'Patch damaged')
    backup_root.mkdir(parents=True, exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix='pvz2-backup-', dir=backup_root))
    receipt = {'status': 'PREPARING', 'serial': device.serial, 'before': current, 'target': targets,
               'backup': str(folder.resolve()), 'started_epoch': time.time()}
    changed = []
    try:
        for key in NAMES:
            device.pull(key, folder / NAMES[key])
            require(sha(folder / NAMES[key]) == current[key], 'Resource changed while backing up')
        save(folder / 'backup.json', receipt)
        for key, entry in entries.items():
            if current[key] != targets[key]:
                apply(folder / NAMES[key], root / entry['patch'], folder / 'patched' / NAMES[key], entry)
        require(device.hashes() == current, 'Phone resources changed during preparation')
        device.stop()
        for key in NAMES:
            if current[key] != targets[key]:
                changed.append(key)
                device.push(key, folder / 'patched' / NAMES[key])
        require(device.hashes() == targets, 'Installed resource hash mismatch')
        receipt['status'] = 'INSTALLED_HASH_VERIFIED'
    except BaseException as exc:
        receipt['status'], receipt['error'] = 'FAILED', repr(exc)
        if changed:
            try:
                device.stop()
                for key in changed:
                    device.push(key, folder / NAMES[key])
                require(device.hashes() == current, 'Rollback hash mismatch')
                receipt['rollback'] = 'VERIFIED'
            except BaseException as restore_error:
                receipt['rollback'] = 'FAILED'
                receipt['rollback_error'] = repr(restore_error)
        raise
    finally:
        receipt['finished_epoch'] = time.time()
        save(folder / 'install-result.json', receipt)
        print('Backup and receipt: ' + str(folder.resolve()), flush=True)
    return receipt

def restore(device, folder, manifest):
    device.preflight()
    receipt = json.loads((folder / 'backup.json').read_text(encoding='utf-8'))
    require(receipt['serial'] == device.serial, 'Backup belongs to another device')
    current = device.hashes()
    for key, entry in manifest['resources'].items():
        require(receipt['before'][key] in (entry['source_sha256'], entry['target_sha256']), 'Unsupported backup hash')
        require(sha(folder / NAMES[key]) == receipt['before'][key], 'Backup damaged')
        require(current[key] in (entry['source_sha256'], entry['target_sha256']), 'Phone has unrelated/new resources')
    device.stop()
    for key in NAMES:
        device.push(key, folder / NAMES[key])
    require(device.hashes() == receipt['before'], 'Restored hash mismatch; preserve backup and retry')
    return {'status': 'RESTORED_HASH_VERIFIED', 'hashes': receipt['before']}

def main():
    p = argparse.ArgumentParser(description='PvZ2 13.4.1 (1055) Korean beta patch')
    p.add_argument('mode', choices=['apply', 'install', 'verify', 'restore'])
    p.add_argument('--adb', default='adb')
    p.add_argument('--serial')
    p.add_argument('--obb', type=Path)
    p.add_argument('--cdn', type=Path)
    p.add_argument('--out', type=Path, default=Path('patched-output'))
    p.add_argument('--backup', type=Path, default=Path('backups'))
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if args.mode == 'apply':
        require(args.obb and args.cdn, 'Specify --obb and --cdn originals')
        require(not args.out.exists(), 'Choose a new output directory')
        for key, source in [('obb', args.obb), ('cdn', args.cdn)]:
            e = manifest['resources'][key]
            require(sha(source) == e['source_sha256'], 'Unsupported original ' + key)
            require(sha(root / e['patch']) == e['patch_sha256'], 'Patch damaged')
        for key, source in [('obb', args.obb), ('cdn', args.cdn)]:
            e = manifest['resources'][key]
            apply(source, root / e['patch'], args.out / NAMES[key], e)
        result = {'status': 'PATCH_OUTPUT_HASH_VERIFIED', 'output': str(args.out.resolve())}
    else:
        require(args.serial, 'Specify --serial from adb devices; device selection is explicit')
        device = Device(args.adb, args.serial)
        if args.mode == 'install':
            result = install(device, root, manifest, args.backup)
        elif args.mode == 'restore':
            result = restore(device, args.backup, manifest)
        else:
            device.preflight()
            hashes = device.hashes()
            require(hashes == {k: e['target_sha256'] for k, e in manifest['resources'].items()}, 'Phone is not this exact Korean version')
            result = {'status': 'INSTALLED_HASH_VERIFIED_READ_ONLY', 'hashes': hashes}
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        sys.exit(1)
