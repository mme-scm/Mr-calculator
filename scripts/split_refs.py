"""Write the census reference records of the staging file into data/ref_census/ in parts below 50 MB.

The staging file is append-only, so earlier parts stay byte-identical from one sync to the next.
An incomplete last line (a writer in mid-flush) is left out; repeated records are written once.
usage: split_refs.py <staged ref_census.jsonl>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrcalc.config import REF_CENSUS_DIR  # noqa: E402

PART = 40 * 1024 * 1024


def main():
    src = sys.argv[1]
    os.makedirs(REF_CENSUS_DIR, exist_ok=True)
    old = {f for f in os.listdir(REF_CENSUS_DIR) if f.endswith('.jsonl')}
    new, n, size, out, lines, seen = set(), 0, 0, None, 0, set()
    with open(src, 'rb') as f:
        for line in f:
            if not line.endswith(b'\n'):
                break
            key = line.split(b'"', 4)[3]            # the name; later repetitions of a record are dropped
            if key in seen:
                continue
            seen.add(key)
            if out is None or size + len(line) > PART:
                if out:
                    out.close()
                name = 'part-%03d.jsonl' % n
                out, size, n = open(os.path.join(REF_CENSUS_DIR, name + '.tmp'), 'wb'), 0, n + 1
                new.add(name)
            out.write(line)
            size += len(line)
            lines += 1
    if out:
        out.close()
    for name in new:
        os.replace(os.path.join(REF_CENSUS_DIR, name + '.tmp'), os.path.join(REF_CENSUS_DIR, name))
    for name in old - new:
        os.remove(os.path.join(REF_CENSUS_DIR, name))
    print('census references: %d records in %d parts' % (lines, n))


if __name__ == '__main__':
    main()
