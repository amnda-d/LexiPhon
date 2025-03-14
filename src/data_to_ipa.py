import os
import argparse
import csv

import torch
import epitran
from tqdm import tqdm
import pandas as pd
from transformers import T5ForConditionalGeneration, AutoTokenizer
from ipapy.ipastring import IPAString

from get_lang_code import get_code


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--lang", required=True)
    parser.add_argument("--wikipron_path", required=True)
    parser.add_argument("--xpf_path", required=True)
    return parser.parse_args()

opt = get_args()

epitran_code = get_code("/languages.tsv", opt.lang, "epitran")
charsiu_code = get_code("/languages.tsv", opt.lang, "charsiu")
xpf_code = get_code("/languages.tsv", opt.lang, "xpf")
wikipron_code = get_code("/languages.tsv", opt.lang, "wikipron")

print(f'Epitran: {epitran_code}')
print(f'Charsiu: {charsiu_code}')
print(f'XPF: {xpf_code}')
print(f'Wikipron: {wikipron_code}')

def get_ipa(ipa_string):
    ipa = IPAString(unicode_string=ipa_string, ignore=True)
    ipa_filtered = []
    for i in ipa:
        if i.is_diacritic or (i.is_suprasegmental and i.is_long):
            if len(ipa_filtered) == 0:
                continue
            else:
                # ipa_filtered[-1] = IPAString(ipa_chars=[ipa_filtered[-1], i])
                ipa_filtered[-1] = ipa_filtered[-1] + str(i)
        elif i.is_tone:
            continue
        elif i.is_suprasegmental and (i.is_stress or i.is_break):
            continue
        else:
            ipa_filtered += [str(i)]
    return ' '.join([str(i) for i in ipa_filtered])

if not pd.isna(epitran_code):
    epi_mod = epitran.Epitran(epitran_code)

def get_epitran(word):
    if pd.isna(epitran_code):
        return None
    else:
        return ' '.join(epi_mod.trans_list(word))

if not pd.isna(charsiu_code):
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = T5ForConditionalGeneration.from_pretrained('/charsiu').to(device)
    tokenizer = AutoTokenizer.from_pretrained('/charsiu_token')

def get_charsiu(word):
    if pd.isna(charsiu_code):
        return None
    else:
        out = tokenizer(
            [f'<{charsiu_code}>: {word}'],
            padding=True,
            add_special_tokens=False,
            return_tensors='pt'
        ).to(device)
        preds = model.generate(**out, num_beams=1, max_length=50)
        phones = tokenizer.batch_decode(preds.tolist(), skip_special_tokens=True)
        return get_ipa(''.join([p for p in phones[0] if p != "ˈ"]))

if not pd.isna(xpf_code):
    xpf_path = f'{opt.xpf_path}/{opt.lang}_xpf.tsv'
    xpf_data = {}
    with open(xpf_path, "r", encoding="utf-8") as fp:
        for line in fp:
            try:
                word, ipa = line.strip().split('\t')
                xpf_data[word] = ipa
            except ValueError as e:
                print(e, line)

def get_xpf(word):
    if pd.isna(xpf_code):
        return None 
    else:
        return xpf_data[word] if word in xpf_data else None

if not pd.isna(wikipron_code):
    wiki_path = os.path.join(opt.wikipron_path, wikipron_code)
    wiki_data = {}
    with open(wiki_path, "r", encoding="utf-8") as fp:
        for line in fp:
            word, ipa = line.strip().split('\t')
            wiki_data[word] = ipa

def get_wikipron(word):
    if pd.isna(wikipron_code):
        return None
    else:
        return wiki_data[word] if word in wiki_data else None

alphabet = set()
inv_epi = set()
inv_cs = set()
inv_xpf = set()
inv_wp = set()

def wiki_g2p():
    g2p_data = {}
    num_lines = sum(1 for _ in open(opt.file, "rb"))
    with open(opt.file, "r", encoding="utf-8") as fp:
        for line in tqdm(fp, mininterval = 5, total = num_lines):
            if line is not os.linesep:
                word = line.strip().split('\t')[0]
                alphabet.update(word)
                epi = get_epitran(word)
                charsiu = get_charsiu(word)
                xpf = get_xpf(word)
                wp = get_wikipron(word)

                if epi:
                    inv_epi.update(epi.split(' '))
                if charsiu:
                    inv_cs.update(charsiu.split(' '))
                if xpf:
                    inv_xpf.update(xpf.split(' '))
                if wp:
                    inv_wp.update(wp.split(' '))

                g2p_data[word] = {
                    "Word": word,
                    "Epitran": epi,
                    "CharSiu": charsiu,
                    "XPF": xpf,
                    "WikiPron": wp
                }
    return g2p_data

g2p_data = wiki_g2p()

al = ' '.join(alphabet)
epi = ' '.join(inv_epi)
cs = ' '.join(inv_cs)
xpf = ' '.join(inv_xpf)
wp = ' '.join(inv_wp)

with open (f'{opt.file}_inventory.txt', "w", encoding="utf-8") as fp:
    fp.write(f'Alphabet: {al}\n')
    fp.write(f'Epitran Inventory: {epi}\n')
    fp.write(f'CharSiu Inventory: {cs}\n')
    fp.write(f'XPF Inventory: {xpf}\n')
    fp.write(f'WikiPron Inventory: {wp}\n')

with open(f'{opt.file}_g2p.tsv', "w", encoding="utf-8") as fp:
    writer = csv.DictWriter(fp, fieldnames=["Word", "Epitran", "CharSiu", "XPF", "WikiPron"], delimiter = '\t', escapechar='\\')
    writer.writeheader()
    writer.writerows(g2p_data.values())