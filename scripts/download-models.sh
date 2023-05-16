#!/bin/sh

python -m scripts.download_models

# English language LR model
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder/4.tar.gz -o 4.tar.gz
tar xfz 4.tar.gz -C files/models/embeddings-en

# Multilingual language LR model (for Korean)
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder-multilingual/3.tar.gz -o 3.tar.gz
tar xfz 3.tar.gz -C files/models/embeddings-multi
