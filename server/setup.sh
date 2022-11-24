#!/bin/bash
mkdir $MODEL_PATH
gsutil -m cp -r $AIP_STORAGE_URI* $MODEL_PATH
