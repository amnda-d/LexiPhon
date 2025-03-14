import os

entities = set()
cnt = 0

with open("data/paranames/paranames.tsv", "r", encoding="utf-8") as fp:
    for line in fp:
        cnt += 1
        if cnt % 1000000 == 0:
            print(f'line {cnt / 1000000} million')
        if line is not os.linesep:
            _, eng, ent, _, _ = line.strip().split('\t')
            entities.add(eng)
            entities.add(ent)

print(len(entities))

with open("data/paranames/paranames_list", "w", encoding="utf-8") as fp:
    fp.write('\n'.join(entities))