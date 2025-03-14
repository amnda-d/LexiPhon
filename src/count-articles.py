import argparse

from smart_open import smart_open
from tqdm import tqdm

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wiki", required=True)
    parser.add_argument("--outfile", required=True)
    return parser.parse_args()

def main():
    opt = get_args()
    nb_article = 0
    for line in tqdm(smart_open(opt.wiki)):
        nb_article += 1
    with open(opt.outfile, "w", encoding="utf-8") as fp:
        fp.write(str(nb_article))
    print(nb_article)

if __name__ == "__main__":
    main()