#!/bin/bash

if [[ ! -d /opt/conda/envs/notebooks_env ]]; then
    # apt-get install build-essential gcc -y
    conda info --envs
    conda env update --file=environment.yml
    source activate notebooks_env
    conda info --envs
else
    echo "Using cached miniconda environment";
fi
