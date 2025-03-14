import os
import sys
import csv
import argparse
import unicodedata
from collections import Counter

from tqdm import tqdm

WORD_FREQ_CUTOFF = 1.0
WORD_COUNT_CUTOFF = 1
CHAR_FREQ_CUTOFF = 1.0
CHAR_COUNT_CUTOFF = 50

exclude = [
    'Nd',   # number, decimal digit
    'Nl',   # number, letter
    'No',   # number, other
    'Pc',   # punctuation, connector
    'Pe',   # punctuation, close
    'Pf',   # punctuation, final quote
    'Pi',   # punctuation, initial quote
    'Po',   # punctuation, other
    'Ps',   # punctuation, open
    'Sc',   # symbol, currency
    'Sm',   # symbol, math
    'So',   # symbol, other
    'Zl',   # line separator
    'Zp',   # paragraph separator
    'Zs'    # space separator
]

include = [chr(c) for c in [
    0x0027, # apostrophes
    0x055A,
    0xFF07,
    0x2032,
    0x2035,
    0x055F, # abbreviation signs
    0x0836,
    0x0970,
    0x09FD,
    0x0A76,
    0x0AF0,
    0x10B39,
    0x110BB,
    0x11174,
    0x111C7,
    0x1123D,
    0x1144F,
    0x114C6,
    0x11643,
    0x116B9,
    0x1183B,
    0x2027,   # hyphens
    0x2043
]]

punct = {chr(i) for i in range(sys.maxunicode) if unicodedata.category(chr(i)) in exclude and chr(i) not in include}

def filter(word, freq, count, freq_cutoff, count_cutoff, punct, inventory):
    word_chars = set(word)
    if freq <= freq_cutoff:
        return False
    if count <= count_cutoff:
        return False
    elif len(word_chars & punct) != 0:
        return False
    elif len(word_chars - inventory) != 0:
        return False
    else:
        return True


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki_dir", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--inv_outfile", required=True)
    parser.add_argument("--entities_list", required=True)
    return parser.parse_args()

opt = get_args()

print(opt)

entities = []

def count_lines(file):
    with open(file, "rb") as f:
        num_lines = sum(1 for _ in f)
    return num_lines

with open(opt.entities_list, "r", encoding="utf-8") as fp:
    for line in tqdm(fp, total=count_lines(opt.entities_list)):
        entities += [line.strip()]

entities = set(entities)

cnt = Counter()

for f in os.listdir(opt.wiki_dir):
    if '.' not in f and len(f) < 6 and f.startswith(opt.lang):
        with open(f'{opt.wiki_dir}/{f}', "r", encoding="utf-8") as fp:
            for line in tqdm(fp, total=count_lines(f'{opt.wiki_dir}/{f}')):
                line = line.split('\t')
                word = line[0]
                freq = float(line[1])
                if freq > WORD_FREQ_CUTOFF and len(set(word) & punct) == 0:
                    cnt.update(set(word))

total = cnt.total()

inventory = Counter()

for x in sorted(cnt.items(), key=lambda item: (-item[1], item[0])):
    char = x[0]
    count = x[1]
    freq = (count * 1000000.0) / total
    if freq >= CHAR_FREQ_CUTOFF and count >= CHAR_COUNT_CUTOFF:
        inventory[char] = count

words = {}

inv_set = set(inventory.keys())

for f in os.listdir(opt.wiki_dir):
    if len(f) < 6 and f.startswith(opt.lang):
        with open(f'{opt.wiki_dir}/{f}', "r", encoding="utf-8") as fp:
            for line in tqdm(fp, total=count_lines(f'{opt.wiki_dir}/{f}')):
                line = line.split('\t')
                word = line[0]
                freq = float(line[1])
                word_count = int(line[2])
                if filter(word, freq, word_count, WORD_FREQ_CUTOFF, CHAR_FREQ_CUTOFF, punct, inv_set):
                    words[word] = {
                        'Freq': freq,
                        'Count': word_count
                    }

print(f'Before removing named entities: {len(words)} words')

# keep_words = set(words.keys()).difference(entities)

# print(len(keep_words))

for k in entities:
    words.pop(k, None)

print(f'After removing named entities: {len(words)} words')

inv_epi = Counter()
inv_cs = Counter()
inv_xpf = Counter()
inv_wp = Counter()

for f in os.listdir(opt.wiki_dir):
    if f.startswith(opt.lang) and f.endswith('_g2p.tsv'):
        with open(f'{opt.wiki_dir}/{f}', "r", encoding="utf-8") as fp:
            for line in tqdm(fp, total=count_lines(f'{opt.wiki_dir}/{f}')):
                word, epitran, charsiu, xpf, wikipron = line.strip('\n').split('\t')
                if word in words:
                    inv_epi.update(epitran.split(' '))
                    inv_cs.update(charsiu.split(' '))
                    inv_xpf.update(xpf.split(' '))
                    inv_wp.update(wikipron.split(' '))
                    words[word] = {
                        'Word': word,
                        'Freq': words[word]['Freq'],
                        'Count': words[word]['Count'],
                        'Epitran': epitran,
                        'CharSiu': charsiu,
                        'XPF': xpf,
                        'WikiPron': wikipron
                    }

inv = '\n'.join([f'\t{x[0]} {x[1]}' for x in sorted(inventory.items(), key = lambda x: -x[1])])
epi = '\n'.join([f'\t{x[0]} {x[1]}' for x in sorted(inv_epi.items(), key = lambda x: -x[1])])
cs = '\n'.join([f'\t{x[0]} {x[1]}' for x in sorted(inv_cs.items(), key = lambda x: -x[1])])
xpf = '\n'.join([f'\t{x[0]} {x[1]}' for x in sorted(inv_xpf.items(), key = lambda x: -x[1])])
wp = '\n'.join([f'\t{x[0]} {x[1]}' for x in sorted(inv_wp.items(), key = lambda x: -x[1])])

with open(opt.inv_outfile, "w", encoding="utf-8") as fp:
    fp.write(f'Alphabet:\n{inv}\n')
    fp.write(f'Epitran Inventory:\n{epi}\n')
    fp.write(f'CharSiu Inventory:\n{cs}\n')
    fp.write(f'XPF Inventory:\n{xpf}\n')
    fp.write(f'WikiPron Inventory:\n{wp}\n')

with open(f'{opt.outfile}', "w", encoding="utf-8") as fp:
    writer = csv.DictWriter(fp, fieldnames=["Word", "Freq", "Count", "Epitran", "CharSiu", "XPF", "WikiPron"], delimiter = '\t')
    writer.writeheader()
    writer.writerows(words.values())