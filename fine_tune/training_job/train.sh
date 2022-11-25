#!/bin/bash

# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

unset PYTHONPATH

export MODEL_NAME="CompVis/stable-diffusion-v1-4"
export INSTANCE_DIR="instance-images"
export CLASS_DIR="class-images"
export OUTPUT_DIR="output"

mkdir $OUTPUT_DIR

gsutil -m cp -r $INPUT_BUCKET/* $INSTANCE_DIR # TODO: consider if we want to put this into the training script

accelerate launch --config_file=accelerate_config.yaml \ 
  train_dreambooth.py \
  # TODO: get all of below args from an ENV_VAR instead so we can easily pass them when we create a training job
  --pretrained_model_name_or_path="$MODEL_NAME"  \
  --instance_data_dir="$INSTANCE_DIR" \
  --class_data_dir=$CLASS_DIR \
  --output_dir="$OUTPUT_DIR" \
  --with_prior_preservation --prior_loss_weight=1.0 \
  --instance_prompt="$INSTANCE_PROMPT" \
  --class_prompt="$CLASS_PROMPT" \
  --resolution=512 \
  --train_batch_size=1 \
  --gradient_accumulation_steps=2 --gradient_checkpointing \
  --use_8bit_adam \
  --learning_rate=5e-6 \
  --lr_scheduler="constant" \
  --lr_warmup_steps=0 \
  --num_class_images=200 \
  --max_train_steps=400 \
  --access_token="$ACCESS_TOKEN"

# TODO: store class-images to a bucket as well (generating these costs resources so why not save them for re-use); investigate if there is a possibility to use images pre-generated images withing the training script
gsutil -m cp -r $OUTPUT_DIR/* $AIP_MODEL_DIR # TODO: consider if we want to put this into the training script
