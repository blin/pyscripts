#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "more-itertools",
# ]
# ///
"""Accepts https://github.com/open-dict-data/ipa-dict as input"""

import sys
from pprint import pprint
from collections import Counter

from more_itertools import pairwise, flatten

lines = sys.stdin.read().splitlines()

words = [l.split("\t")[0] for l in lines]

char_pairs = flatten([list(pairwise(w)) for w in words])

pair_counts = Counter(["".join(p) for p in char_pairs])

pprint(pair_counts.most_common(100))
