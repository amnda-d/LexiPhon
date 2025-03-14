import argparse

import pandas as pd

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', required=True)
    parser.add_argument('--wiki_code', required=True)
    parser.add_argument(
        '--code',
        choices=[
            'xpf',
            'epitran',
            'charsiu',
            'unimorph',
            'wikipron',
            'northeuralex',
            'name'
            ],
        required=True
    )
    return parser.parse_args()


def get_code(filename, wiki_code, code):
    lang_codes = pd.read_csv(filename, sep='\t', index_col='Wikipedia', dtype="string")
    if code == 'xpf':
        return lang_codes.loc[wiki_code, "XPF"]
    elif code == "epitran":
        return lang_codes.loc[wiki_code, "Epitran"]
    elif code == "charsiu":
        return lang_codes.loc[wiki_code, "CharsiuG2P"]
    elif code == "unimorph":
        return lang_codes.loc[wiki_code, "UniMorph"]
    elif code == "wikipron":
        return lang_codes.loc[wiki_code, "WikiPron"]
    elif code == "northeuralex":
        return lang_codes.loc[wiki_code, "Northeuralex"]
    elif code == "name":
        return lang_codes.loc[wiki_code, "Language"]

def main():
    opt = get_args()
    print(get_code(opt.file, opt.wiki_code, opt.code))

if __name__ == "__main__":
    main()
