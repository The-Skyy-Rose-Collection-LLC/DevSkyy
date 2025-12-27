#!/bin/bash

# Set environment variables for Tripo3D generation
export TRIPO_API_KEY="tsk_UcZp-Gjk5ZAa8lOv8sTApdOqcvISeWdCSmj0BGk-Mvn"
export SSL_CERT_FILE="/Library/Frameworks/Python.framework/Versions/3.14/lib/python3.14/site-packages/certifi/cacert.pem"
export PYTHONHTTPSVERIFY=0

# Run the generation script
python3 scripts/generate_3d_models_official_sdk.py
