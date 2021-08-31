#!/bin/bash
set -x -e

# Set up venv
PYTHON3="$(which python3)"
${PYTHON3} -m venv ${VENV_DIR}

# activate venv & download necessary packages
source ${VENV_DIR}/bin/activate
PIP3="$(which pip3)"
${PIP3} install --quiet --upgrade pip
${PIP3} install -r requirements.txt
