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
from google.cloud import aiplatform

# TODO: refactor all of this and make it more configurable
project_id = "sd-db-tf"
location = "europe-west1"
staging_bucket = "gs://vertexai_pipeline_staging_{}".format(project_id)
input_bucket = "gs://instance_images_dog_{}".format(project_id) # change this to use different input images
output_bucket ="gs://stable-diffusion-dreambooth-models_{}".format(project_id)
instance_prompt="\"a photo of sks dog\""
access_token=os.environ['ACCESS_TOKEN'] # TODO: get this from secret manager instead
serving_output_bucket="render-results_{}".format(project_id)
training_service_account="vertexai-training@{}.iam.gserviceaccount.com".format(project_id)
serving_service_account="vertexai-prediction@{}.iam.gserviceaccount.com".format(project_id)

aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)

# TODO: expose train_dreambooth.py args directly and build arg-string right here based on input to keep logic out of pipeline and docker image
# TODO: consider checking for last changed timestamp of bucket and use for caching to make sure that we don't rebuild model without change of images
# TODO: consider better strategy for pipeline, job and model identifiers
job = aiplatform.PipelineJob(
    display_name = "fine-tune-sd-db-pipeline",
    template_path = "gs://vertexai_pipeline_definition_{}/stablediffusion_dreambooth_pipeline.json".format(project_id),
    pipeline_root = staging_bucket,
    parameter_values = {
        "project_id": project_id,
        "location": location,
        "staging_bucket": staging_bucket,
        "input_bucket": input_bucket,
        "output_bucket": output_bucket,
        "instance_prompt": instance_prompt,
        "access_token": access_token, 
        "training_container_uri": "{}-docker.pkg.dev/{}/stablediffusion-dreambooth/finetune-16gb-prebuilt:latest".format(location, project_id),
        "serving_container_uri": "{}-docker.pkg.dev/{}/stablediffusion-dreambooth/bentoml-server-no-model:latest".format(location, project_id),
        "serving_output_bucket": serving_output_bucket,
        "service_account": training_service_account,
        "training_machine_type": "n1-standard-8",
        "training_accelerator_type": "NVIDIA_TESLA_P100",
        "training_accelerator_count": 1,
        "class_prompt": "\"a photo of dog\"",
        #"parent_model": None,
        "model_name": "CompVis/stable-diffusion-v1-4",
        "serving_service_account": serving_service_account
    },
    project = project_id,
    location = location,
)

job.submit(service_account=training_service_account)
