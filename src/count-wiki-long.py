import argparse
import json
import os
import math
import string
import unicodedata
import sys
import re
import pickle
from collections import Counter
from functools import partial
from itertools import islice

import langcodes
from nltk.tokenize import word_tokenize
from smart_open import smart_open
from tqdm import tqdm
from sudachipy import dictionary


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--part", required=True)
    parser.add_argument("--combine", required=False)
    return parser.parse_args()


def maybe_mkdir(filename):
    """
    maybe mkdir
    """
    path = os.path.dirname(filename)
    if not os.path.isdir(path):
        try:
            os.makedirs(path)
        except FileExistsError:
            pass


def main():
    opt = get_args()
    if opt.combine:
        maybe_mkdir(opt.outfile)
        total_cnt = Counter()
        for part in range(int(opt.combine) + 1):
            with open(f'/wikipedia/split/{opt.lang}_{part}.pkl', 'rb') as inp:
                cnt = pickle.load(inp)
                total_cnt = total_cnt + cnt
        total = total_cnt.total()
        with open(opt.outfile, "w", encoding="utf-8") as fp:
            # for x in sorted(cnt.items(), key=lambda item: (-item[1], item[0])):
            for x in tqdm(total_cnt.items(), total=len(total_cnt.items())):
                word = x[0]
                wordcnt = x[1]
                wordcntpm = (x[1] * 1000000.0) / total
                fp.write(f"{word}\t{wordcntpm}\t{wordcnt}\n")
    else:
        cnt = Counter()
        punct = string.punctuation + "0123456789"
        unicode_categories = ["Nd", "Nl", "No", "Pc", "Pd", "Pe", "Pf", "Pi", "Po", "Ps", "Sc", "Sk", "Sm", "So"]
        punct = [chr(i) for i in range(sys.maxunicode) if unicodedata.category(chr(i)) in unicode_categories] + [str(x) for x in range(10)]
        language = langcodes.Language.get(opt.lang).language_name().lower()
        tokenize = partial(word_tokenize, language=language)

        nb_article = 0
        for line in tqdm(smart_open(opt.wiki)):
            nb_article += 1
        start_article = int(opt.part) * 500000
        stop_article = min(nb_article, start_article + 500000)
        for line in tqdm(islice(smart_open(opt.wiki), start_article, stop_article), total=stop_article, initial=start_article):
            article = json.loads(line)
            text = " ".join(article["section_texts"]).lower()
            if opt.lang == "ja":
                tokens = []
                for s in text.split():
                    for sent_part in re.split('。|、|！', s):
                        tokens += [m.surface() for m in tokenizer_jp.tokenize(sent_part)]
            else:
                try:
                    tokens = tokenize(text)
                except LookupError:
                    print("Using default tokenizer")
                    tokenize = partial(word_tokenize, language="english")
                    tokens = tokenize(text)
            for t in tokens:
                if not all(s in punct for s in t):
                    cnt[t] += 1

        with open(f'/wikipedia/split/{opt.lang}_{opt.part}.pkl', 'wb') as outp:
            pickle.dump(cnt, outp, pickle.HIGHEST_PROTOCOL)


if __name__ == "__main__":
    main()
