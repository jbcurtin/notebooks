#!/bin/bash

if [[ ! -d /opt/conda/envs/notebooks_env ]]; then
    conda info --envs
    conda env update --file=environment.yml
    source activate notebooks_env
    apt-get install build-essential gcc -y
    pip install -e https://github.com/eteq/nbpages.git@b9ec8410803357939210e068af7e14a6f0625fab#egg=nbpages
    conda info --envs
else
    echo "Using cached miniconda environment";
fi
