#!/bin/bash

if [[ ! -d /opt/conda/envs/notebooks_env ]]; then
    conda info --envs
    conda env update --file=environment.yml
    apt-get install build-essential gcc -y
    source activate notebooks_env
    conda info --envs
else
    echo "Using cached miniconda environment";
fi
