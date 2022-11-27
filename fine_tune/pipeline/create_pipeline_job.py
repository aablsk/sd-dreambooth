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

import os
import re
from datetime import datetime as dt
from google.cloud import aiplatform
from google.cloud import storage

project_id = "sd-db-tf"
location = "europe-west1"
# change this to use different input images
input_bucket = f"gs://instance_images_dog_{project_id}"
instance_prompt = "photo of sks dog"
class_prompt = "photo of dog"
# TODO: get this from secret manager instead
access_token = os.environ['ACCESS_TOKEN']

aiplatform.init(project=project_id, location=location)


def get_bucket_last_changed_timestamp(bucket_uri: str):
    client = storage.Client(project=project_id)
    bucket_name = bucket_uri.split("/")[2]
    bucket = client.bucket(bucket_name)
    last_updated = None
    for blob in bucket.list_blobs():
        last_updated = blob.updated if last_updated == None or blob.updated > last_updated else last_updated
    return last_updated


def render_train_script_args(instance_prompt=str,
                             pretrained_model_name: str = 'CompVis/stable-diffusion-v1-4',
                             resolution: int = 512,
                             train_batch_size: int = 1,
                             learning_rate: float = 5e-6,
                             lr_scheduler: str = 'constant',
                             lr_warmup_steps: int = 0,
                             max_train_steps: int = 500,
                             ram_16_gb: bool = True,
                             class_prompt: str = None,
                             class_data_dir: str = 'class-images',
                             num_class_images: int = 200,
                             prior_loss_weight: float = 1.0):
    args = []
    # constants: DO NOT CHANGE AS THESE ARE CURRENTLY HARD-CODED INTO THE IMAGE!
    args.append('--instance_data_dir="instance-images"')
    args.append('--output_dir="output"')
    # required
    args.append(f'--instance_prompt="{instance_prompt}"')
    args.append(f'--pretrained_model_name_or_path="{pretrained_model_name}"')
    args.append(f'--resolution={resolution}')
    args.append(f'--train_batch_size={train_batch_size}')
    args.append(f'--learning_rate={learning_rate}')
    args.append(f'--lr_scheduler={lr_scheduler}')
    args.append(f'--lr_warmup_steps={lr_warmup_steps}')
    args.append(f'--max_train_steps={max_train_steps}')  # should be instance_images * 100

    if ram_16_gb:
        args.append('--gradient_accumulation_steps=2')
        args.append('--gradient_checkpointing')
        args.append('--use_8bit_adam')

    if class_prompt is not None:
        args.append('--with_prior_preservation')
        args.append(f'--prior_loss_weight={prior_loss_weight}')
        args.append(f'--class_prompt="{class_prompt}"')
        args.append(f'--class_data_dir="{class_data_dir}"')
        args.append(f'--num_class_images={num_class_images}')

    return " ".join(args)


train_script_args = render_train_script_args(instance_prompt=instance_prompt, class_prompt=class_prompt)

#get_bucket_last_changed_timestamp("stable-diffusion-dreambooth-models_sd-db-tf/stablediffusion-dreambooth_2022_11_25__08_59_03/model", project_id)


def clean_str(string: str):
    return re.sub(r'[^A-Za-z0-9\_\-]', '', string)

pipeline_identifier = f'finetune-sd-db-{input_bucket.split("/")[2]}-{clean_str(instance_prompt)}-{clean_str(class_prompt)}'

# TODO: expose more train_dreambooth.py args
# TODO: consider checking for last changed timestamp of bucket and use for caching to make sure that we don't rebuild model without change of images
# TODO: consider better strategy for pipeline, job and model identifiers
job = aiplatform.PipelineJob(
    display_name=f'pipeline_identifier-{dt.now().strftime("%Y_%m_%d__%H_%M_%S")}',
    #template_path=f'gs://vertexai_pipeline_definition_{project_id}/stablediffusion_dreambooth_pipeline.json',
    template_path='stablediffusion_dreambooth_pipeline.json',
    pipeline_root=f'gs://vertexai_pipeline_staging_{project_id}',
    parameter_values={
        'project_id': project_id,
        'location': location,
        'pipeline_identifier': f'{pipeline_identifier}-{get_bucket_last_changed_timestamp(input_bucket).strftime("%Y_%m_%d__%H_%M_%S")}',
        # training
        'training_container_uri':
            f'{location}-docker.pkg.dev/{project_id}/stablediffusion-dreambooth/finetune-16gb-prebuilt:latest',
        'accelerate_args': '--config_file=accelerate_config.yaml',
        'train_script': 'train_dreambooth.py',
        'train_script_args':
            train_script_args,
        'input_bucket':
            input_bucket,
        'output_bucket':
            f'gs://stable-diffusion-dreambooth-models_{project_id}',
        'access_token':
            access_token,
        'service_account':
            f'vertexai-training@{project_id}.iam.gserviceaccount.com',
        'training_machine_type':
            'n1-standard-8',
        'training_accelerator_type':
            'NVIDIA_TESLA_P100',
        'training_accelerator_count':
            1,
        # resulting model & serving
        'parent_model': f'stablediffusion-dreambooth-{input_bucket.split("/")[2]}',
        'serving_container_uri':
            f'{location}-docker.pkg.dev/{project_id}/stablediffusion-dreambooth/bentoml-server-no-model:latest',
        'serving_output_bucket':
            f'render-results_{project_id}',
        'serving_service_account':
            f'vertexai-prediction@{project_id}.iam.gserviceaccount.com'
    },
    project=project_id,
    location=location,
)

# job.submit(service_account=training_service_account)
