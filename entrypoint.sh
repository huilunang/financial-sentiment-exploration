#!/bin/bash
set -e

# activate venv & run app
source ${VENV_DIR}/bin/activate
streamlit run ./src/app.py --server.port $PORT
