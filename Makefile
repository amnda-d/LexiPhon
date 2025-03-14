build_count_xpf:
	limactl shell apptainer apptainer build images/count_xpf.sif images/count_xpf.def

build_preprocess:
	limactl shell apptainer apptainer build images/preprocess.sif images/preprocess.def

build_transformer:
	limactl shell apptainer apptainer build images/transformer.sif images/transformer.def

download_paranames:
	mkdir -p data/paranames
	curl -L https://github.com/bltlab/paranames/releases/download/v2024.05.07.0/paranames.tsv.gz > data/paranames/paranames.tsv.gz
	gunzip data/paranames/paranames.tsv.gz
	python src/parse_paranames.py