#!/bin/sh

mkdir /tmp/models
cd /tmp/models
curl -SL https://storage.googleapis.com/tfhub-modules/google/universal-sentence-encoder/4.tar.gz -o 4.tar.gz
tar xfz 4.tar.gz
