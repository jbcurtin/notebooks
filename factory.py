#!/usr/bin/env python

import logging
import os
import subprocess
import shutil
import sys
import tarfile
import tempfile
import time
import types
import typing

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
root.addHandler(handler)

logger = logging.getLogger(__file__)

IPYDB_REQUIRED_FILES: typing.List[str] = ['requirements.txt']
ENCODING: str = 'utf-8'

def run_command(cmd: typing.List[str], allow_error: typing.List[int] = [0]) -> str:
    proc = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while proc.poll() is None:
        time.sleep(.1)

    if proc.poll() > 0:
        if not proc.poll() in allow_error:
            raise NotImplementedError(f'{proc.poll()}, {proc.stderr.read()}')

        return proc.stderr.read().decode(ENCODING)

    return proc.stdout.read().decode(ENCODING)

def find_ipynb_files(start_path: str) -> types.GeneratorType:
    for root, dirnames, filenames in os.walk(start_path):
        is_ipydb_directory: bool = False
        for filename in filenames:
            if filename.endswith('.ipynb'):
                is_ipydb_directory = True
                break

        if is_ipydb_directory:
            has_error: bool = False
            for filename in IPYDB_REQUIRED_FILES:
                if not filename in filenames:
                    logger.error(f'Missing file[{filename}] in dir[{os.path.relpath(root)}]')
                    has_error = True

            if has_error is False:
                yield os.path.abspath(root)

for notebook_path in find_ipynb_files(os.getcwd()):
    logger.info(f'Found notebook in path[{os.path.relpath(notebook_path)}]. Building Artifact')
    notebook_name: str = os.path.basename(notebook_path)
    notebook_name_plain: str = notebook_name.rsplit('.', 1)[0]
    build_path = tempfile.mkdtemp(prefix=notebook_name)
    shutil.rmtree(build_path)
    build_script_path = os.path.join(build_path, 'build.sh')
    shutil.copytree(notebook_path, build_path)
    setup_script: str = f"""#!/usr/bin/env bash
set -e
cd {build_path}
virtualenv -p $(which python3) env
source env/bin/activate
pip install -r requirements.txt
pip install jupyter
jupyter nbconvert --stdout --to html {notebook_name} > {notebook_name_plain}.html
cd -
"""
    with open(build_script_path, 'w') as stream:
        stream.write(setup_script)

    logger.info(f'Taring Notebook[{notebook_name}]')
    artifact_name: str = f'{notebook_name_plain}.tar.gz'
    artifact_dir_path: str = os.path.dirname(tempfile.NamedTemporaryFile().name)
    artifact_path: str = os.path.join(artifact_dir_path, artifact_name)
    with tarfile.open(artifact_path, "w:gz") as tar:
        tar.add(build_path, arcname=os.path.basename(build_path))

    artifact_dest_dir: str = '/tmp/artifacts'
    if not os.path.exists(artifact_dest_dir):
        os.makedirs(artifact_dest_dir)

    artifact_dest: str = os.path.join(artifact_dest_dir, artifact_name)
    logger.info(f'Moving Notebook[{notebook_name_plain}]')
    shutil.move(artifact_path, artifact_dest)
    # run_command(['bash', setup_script_path])
    # import ipdb; ipdb.set_trace()
    # pass

# from nbpages import make_parser, run_parsed, make_html_index
# 
# args = make_parser().parse_args()
# 
# converted = run_parsed('.', output_type='HTML', args=args)
# 
# converted = [item for item in converted if not os.path.basename(item) in ['test-fail.html', 'test-succeed.html']]
# make_html_index(converted, './index.tpl')
