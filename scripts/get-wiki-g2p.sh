#!/bin/bash

lang=$1
date=$2

wikipron_file=$(python src/get_lang_code.py --wiki_code $lang --code wikipron --file languages.tsv)
xpf_rule=$(python src/get_lang_code.py --wiki_code $lang --code xpf --file languages.tsv)
charsiu_code=$(python src/get_lang_code.py --wiki_code $lang --code charsiu --file languages.tsv)

echo "Downloading Wikipedia data..."
if [ ! -f data/wikipedia/zip/$lang.xml.bz2 ]; then
    mkdir -p data/wikipedia/zip
    wget https://dumps.wikimedia.org/${lang}wiki/${date}/${lang}wiki-${date}-pages-articles.xml.bz2 -O data/wikipedia/zip/$lang.xml.bz2
else
    echo "  File data/wikipedia/zip/$lang.xml.bz2 already exists"
fi

echo "Preprocessing Wikipedia data..."
if [ ! -f data/wikipedia/zip/"$lang"wiki-"$date".json.gz ]; then
    limactl shell apptainer apptainer run --app wikipedia -B $(pwd)/data/wikipedia:/wikipedia -C images/preprocess.sif $lang $date
else
    echo "  File data/wikipedia/zip/"$lang"wiki-"$date".json.gz already exists"
fi

echo "Counting number of articles..."
articles=$(limactl shell apptainer apptainer run --app count-articles -B $(pwd)/data/wikipedia:/wikipedia -C images/count_xpf.sif $lang $date)
echo "  There are $articles articles"

# download wikipron file if exists
echo "Downloading WikiPron data..."
if [ $wikipron_file != "<NA>" ]; then
    if [ ! -f data/wikipron/"$wikipron_file" ]; then
        mkdir -p data/wikipron
        curl "https://raw.githubusercontent.com/CUNY-CL/wikipron/v1.3.2/data/scrape/tsv/${wikipron_file}" > data/wikipron/"$wikipron_file"
    else
        echo "  File data/wikipron/"$lang".tsv already exists."
    fi
else
    echo "  No WikiPron file given."
fi

mkdir -p data/wikipedia/split

echo "Counting word frequencies..."
for i in $(seq 0 $((articles/500000))); do
    echo "  Processing articles $((i*500000)) - $((((i+1)*500000)-1))"
    if [ ! -f data/wikipedia/split/"$lang"_"$i".pkl ]; then
        limactl shell apptainer apptainer run --app countwiki -B $(pwd)/data/wikipedia:/wikipedia -C images/count_xpf.sif $lang $i $date
    else
        echo "      File data/wikipedia/split/"$lang"_"$i".pkl already exists, skipping."
    fi
done

if [ ! -f data/wikipedia/"$lang".wiki.cnt ]; then
    limactl shell apptainer apptainer run --app combine -B $(pwd)/data/wikipedia:/wikipedia -C images/count_xpf.sif $lang $((articles/500000)) $date
else
    echo "  File data/wikipedia/"$lang".wiki.cnt already exists."
fi

# get xpf transcriptions if exists
echo "Getting XPF transcriptions..."
mkdir -p data/wikipedia/xpf
if [ $xpf_rule != "<NA>" ]; then
    if [ ! -f data/wikipedia/xpf/"$lang"_xpf.tsv ]; then
        limactl shell apptainer apptainer run --app xpf -B $(pwd)/data/wikipedia:/wikipedia -C images/count_xpf.sif /wikipedia/"$lang".wiki.cnt /wikipedia/xpf/"$lang"_xpf.tsv $xpf_rule
    else
        echo "  File data/wikipedia/xpf/"$lang"_xpf.tsv already exists."
    fi
else
    echo "  No XPF rule file given"
fi

echo "Getting G2P transcriptions..."
mkdir -p data/wikipedia/split/$lang
split -l 500000 -d data/wikipedia/$lang.wiki.cnt data/wikipedia/split/$lang/$lang

shopt -s extglob

for file in data/wikipedia/split/$lang/!(*.*); do
    if [ ! -f "$file"_g2p.tsv ]; then
        echo "  Running G2P script on file data/wikipedia/split/$lang/$(basename "$file")"
        limactl shell apptainer apptainer run --app g2p --nv -B $(pwd)/data/wikipron:/wikipron -B $(pwd)/data/wikipedia:/wikipedia -C images/transformer.sif /wikipedia/split/$lang/$(basename "$file") $lang /wikipron /wikipedia/xpf
    else
        echo "   File "$file"_g2p.tsv already exists, skipping."
    fi
done

echo "Filtering..."
mkdir -p data/wikipedia/filtered

if [ ! -f data/wikipedia/filtered/"$lang"_filtered.tsv ]; then
    echo "  Running filter script on files data/wikipedia/split/$lang"
    limactl shell apptainer apptainer run --app filter -B $(pwd)/data/wikipedia:/wikipedia -B $(pwd)/data/paranames:/paranames -C images/count_xpf.sif $lang
else
    echo "   File data/wikipedia/filtered/"$lang"_filtered.tsv already exists, skipping."
fi
