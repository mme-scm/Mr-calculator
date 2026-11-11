#!/usr/bin/env python3
"""Convert an export directory between the packed and the plain layout (FORMAT.md, section 1).

usage: export_pack.py unpack <export_dir> <out_dir>    X.jsonl.gz parts -> one X.jsonl; archives -> chains/<node>.txt
       export_pack.py pack   <export_dir> <out_dir>    the reverse (gzip parts and chain archives below 40 MiB)

Only the JSONL files and the chain files change; all other files are copied.  Standard library only.
"""
import gzip
import io
import os
import shutil
import sys
import tarfile

LIMIT = 40 * 2 ** 20
NAMES = ('knots', 'edges', 'constraints', 'events')


def parts(directory, stem):
    out, k = [], 0
    while True:
        base = os.path.join(directory, stem + ('.%d' % k if k else '') + '.jsonl')
        path = base if os.path.exists(base) else base + '.gz' if os.path.exists(base + '.gz') else None
        if path is None:
            if k:
                return out
        else:
            out.append(path)
        k += 1


def lines(directory, stem):
    for path in parts(directory, stem):
        opener = gzip.open if path.endswith('.gz') else open
        with opener(path, 'rb') as f:
            for line in f:
                yield line


def chains(cdir):
    for fn in sorted(os.listdir(cdir)) if os.path.isdir(cdir) else []:
        path = os.path.join(cdir, fn)
        if fn.endswith('.tar.gz'):
            with tarfile.open(path, 'r:gz') as tar:
                for m in tar:
                    if m.isfile():
                        yield m.name, tar.extractfile(m).read()
        else:
            with open(path, 'rb') as f:
                yield fn, f.read()


def gz(raw):
    return gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6)


def main(argv):
    if len(argv) != 4 or argv[1] not in ('pack', 'unpack'):
        print(__doc__)
        return 2
    mode, src, dst = argv[1], argv[2], argv[3]
    os.makedirs(os.path.join(dst, 'chains'), exist_ok=True)
    skip = set()
    for stem in NAMES:
        skip.update(os.path.basename(p) for p in parts(src, stem))
        if not parts(src, stem):
            continue
        if mode == 'unpack':
            with open(os.path.join(dst, stem + '.jsonl'), 'wb') as f:
                for line in lines(src, stem):
                    f.write(line)
        else:
            k, n, raw, f = 0, 0, None, None
            for line in lines(src, stem):
                n += 1
                if raw is None or (n % 500 == 0 and raw.tell() > LIMIT):
                    if raw:
                        f.close()
                        raw.close()
                        k += 1
                    raw = open(os.path.join(dst, stem + ('.%d' % k if k else '') + '.jsonl.gz'), 'wb')
                    f = gz(raw)
                f.write(line)
            if raw:
                f.close()
                raw.close()
    k, raw, tar = 0, None, None
    for name, data in chains(os.path.join(src, 'chains')):
        if mode == 'unpack':
            with open(os.path.join(dst, 'chains', name), 'wb') as f:
                f.write(data)
            continue
        if tar is None:
            raw = open(os.path.join(dst, 'chains', 'chains-%03d.tar.gz' % k), 'wb')
            g = gz(raw)
            tar = tarfile.open(fileobj=g, mode='w', format=tarfile.GNU_FORMAT)
        ti = tarfile.TarInfo(name)
        ti.size, ti.mtime, ti.mode = len(data), 0, 0o644
        tar.addfile(ti, io.BytesIO(data))
        if raw.tell() > LIMIT:
            tar.close(), g.close(), raw.close()
            tar, k = None, k + 1
    if tar is not None:
        tar.close(), g.close(), raw.close()
    for fn in os.listdir(src):
        p = os.path.join(src, fn)
        if fn in skip or fn == 'chains':
            continue
        if os.path.isdir(p):
            shutil.copytree(p, os.path.join(dst, fn), dirs_exist_ok=True)
        else:
            shutil.copy2(p, os.path.join(dst, fn))
    print('%sed %s -> %s' % (mode, src, dst))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
