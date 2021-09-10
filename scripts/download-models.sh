#!/bin/sh

python -m scripts.download_models

mkdir /tmp/models
cd /tmp/models || exit
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder/4.tar.gz -o 4.tar.gz
tar xfz 4.tar.gz
