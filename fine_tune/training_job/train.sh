#!/bin/bash
unset PYTHONPATH

export MODEL_NAME="CompVis/stable-diffusion-v1-4"
export INSTANCE_DIR="instance-images"
export CLASS_DIR="class-images"
export OUTPUT_DIR="output"

mkdir $OUTPUT_DIR

gsutil -m cp -r $INPUT_BUCKET/* $INSTANCE_DIR

accelerate launch --config_file=accelerate_config.yaml \
  train_dreambooth.py \
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

gsutil -m cp -r $OUTPUT_DIR/* $AIP_MODEL_DIR
