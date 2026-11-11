"""Write a staged, append-only JSONL file into a directory of the repository in parts below 50 MB.

Earlier parts stay byte-identical from one sync to the next.  An incomplete last line (a writer in
mid-flush) is left out; a record whose key was seen before is dropped.
usage: split_refs.py <staged file> <directory> <key field>
  e.g. split_refs.py $STAGE/ref_census.jsonl data/ref_census name
"""
import json
import os
import sys

PART = 40 * 1024 * 1024


def main():
    src, target, key_field = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(target, exist_ok=True)
    old = {f for f in os.listdir(target) if f.endswith('.jsonl')}
    new, n, size, out, lines, seen = set(), 0, 0, None, 0, set()
    with open(src, 'rb') as f:
        for line in f:
            if not line.endswith(b'\n'):
                break
            key = json.loads(line)[key_field]
            if key in seen:
                continue
            seen.add(key)
            if out is None or size + len(line) > PART:
                if out:
                    out.close()
                name = 'part-%03d.jsonl' % n
                out, size, n = open(os.path.join(target, name + '.tmp'), 'wb'), 0, n + 1
                new.add(name)
            out.write(line)
            size += len(line)
            lines += 1
    if out:
        out.close()
    for name in new:
        os.replace(os.path.join(target, name + '.tmp'), os.path.join(target, name))
    for name in old - new:
        os.remove(os.path.join(target, name))
    print('%s: %d records in %d parts' % (target, lines, n))


if __name__ == '__main__':
    main()
