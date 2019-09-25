#!/usr/bin/env python

import logging
import json
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
ARTIFACT_DEST_DIR: str = '/tmp/artifacts'
BUILD_STATE_PATH: str = os.path.join('/tmp', 'build-state.json')
BUILD_STATE: typing.Dict[str, typing.Any] = {}
if os.path.exists(BUILD_STATE_PATH):
    with open(BUILD_STATE_PATH, 'r') as stream:
        data = stream.read()
        if data:
            BUILD_STATE: typing.Dict[str, typing.Any] = json.loads(data)

def run_command(cmd: typing.List[str]) -> types.GeneratorType:
    proc = subprocess.Popen(' '.join(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while proc.poll() is None:
        time.sleep(.1)

    if proc.poll() > 0:
        yield proc.poll(), proc.stderr.read().decode(ENCODING)

    elif proc.poll() != None:
        yield proc.poll(), proc.stdout.read().decode(ENCODING)

    else:
        # if proc.poll() is None, its still running the subprocess.
        # block until done
        pass


def find_artifacts(start_dir: str) -> types.GeneratorType:
    for root, dirnames, filenames in os.walk(start_dir):
        for filename in filenames:
            if filename.endswith('.tar.gz'):
                yield os.path.join(start_dir, filename)

for artifact_path in find_artifacts(ARTIFACT_DEST_DIR):
    logger.info(f'Found Artifact in path[{artifact_path}]. Building Artifact')
    notebook_name: str = os.path.basename(artifact_path).rsplit('.', 1)[0]
    extraction_path: str = tempfile.mkdtemp(prefix=notebook_name)
    build_script_path: str = None
    with tarfile.open(artifact_path, "r:gz") as tar:
        for member in tar.getmembers():
            if member.isdir():
                dir_path: str = os.path.join(extraction_path, member.path)
                os.makedirs(dir_path)

            elif member.isfile():
                filepath: str = os.path.join(extraction_path, member.path)
                with open(filepath, 'wb') as stream:
                    stream.write(tar.extractfile(member).read())

                if os.path.basename(member.path) == 'build.sh':
                    build_script_path = filepath

            else:
                raise NotImplementedError


    owd: str = os.getcwd()
    build_dir: str = os.path.dirname(build_script_path)
    logger.info(f'Changing to build_dir[{build_dir}]')
    os.chdir(build_dir)
    BUILD_STATE[notebook_name] = {'logs': {'stdout': [], 'stderr': []}}
    for return_code, comm, in run_command(['bash', 'build.sh']):
        if return_code > 0:
            logger.error(comm)
            BUILD_STATE[notebook_name]['exit-code'] = return_code
            BUILD_STATE[notebook_name]['logs']['stderr'].append(comm)

        else:
            BUILD_STATE[notebook_name]['exit-code'] = return_code
            BUILD_STATE[notebook_name]['logs']['stdout'].append(comm)
            logger.info(comm)

    logger.info(f'Changing back to old working dir[{owd}]')
    os.chdir(owd)
    break

with open(BUILD_STATE_PATH, 'w') as stream:
    stream.write(json.dumps(BUILD_STATE, indent=2))
# from nbpages import make_parser, run_parsed, make_html_index
# 
# args = make_parser().parse_args()
# 
# converted = run_parsed('.', output_type='HTML', args=args)
# 
# converted = [item for item in converted if not os.path.basename(item) in ['test-fail.html', 'test-succeed.html']]
# make_html_index(converted, './index.tpl')

