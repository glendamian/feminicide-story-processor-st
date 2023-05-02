#!/bin/sh

python -m scripts.download_models

mkdir /tmp/models/

# English language LR model
mkdir /tmp/models/en
cd /tmp/models/en || exit
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder/4.tar.gz -o 4.tar.gz
tar xfz 4.tar.gz

# Korean language LR model
mkdir /tmp/models/ko
cd /tmp/models/ko || exit
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder-multilingual/3.tar.gz -o 3.tar.gz
tar xfz 3.tar.gz
