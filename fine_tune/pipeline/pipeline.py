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

import kfp
from kfp.v2 import compiler
from google.cloud import aiplatform
from google_cloud_pipeline_components import aiplatform as gcc_aip
from datetime import datetime as dt

# @kfp.components.create_component_from_func
# def build_labels(model_name: str, instance_prompt: str, class_prompt: str, input_bucket: str, timestamp: str) -> str:
#     import json
#     import re
#     def clean_str(string: str):
#         return re.sub(r'[^A-Za-z0-9\_\-]', '', string)

#     return json.dumps({
#         "base_model": clean_str(model_name),
#         "instance_prompt": clean_str(instance_prompt),
#         "class_prompt": clean_str(class_prompt),
#         "instance_images": clean_str(input_bucket),
#         "timestamp": clean_str(timestamp),
#     })


@kfp.components.create_component_from_func
def build_training_env(input_bucket: str, access_token: str, accelerate_args: str, train_script: str,
                       train_script_args: str, project_id: str) -> str:
    import json
    return json.dumps({
        "INPUT_BUCKET": input_bucket,
        "ACCESS_TOKEN": access_token,
        "ACCELERATE_ARGS": accelerate_args.strip('\''),
        "TRAIN_SCRIPT": train_script,
        "TRAIN_SCRIPT_ARGS": train_script_args.strip('\''),
        "PROJECT_ID": project_id,
    })


@kfp.components.create_component_from_func
def build_serving_env(project_id: str, serving_output_bucket: str, base_output_dir: str) -> str:
    import json
    return json.dumps({
        "PROJECT_ID": project_id,
        "BUCKET": serving_output_bucket,
        "MODELS_PATH": "models",
        "GCS_MODEL_PATH": f"{base_output_dir}/model"
    })


@kfp.components.create_component_from_func
def build_model_description(pipeline_identifier: str, train_script_args: str) -> str:
    return f"StableDiffusion Dreambooth fine-tuned with pipeline_identifier {pipeline_identifier}. Training script args: {train_script_args}"


# TODO:generate a hash including all inputs here
@kfp.components.create_component_from_func
def build_base_output_dir(output_bucket: str, pipeline_identifier: str) -> str:
    return f"{output_bucket}/{pipeline_identifier}/"


# TODO: refactor params
# TODO: make injection of train_dreambooth.py script params easier by passing them from higher in the chain
# TODO: refactor how identifiers are built to ensure proper caching (possibly makes sense to check when last changes to instance image buckets were done)
@kfp.dsl.pipeline(
    name="stablediffusion-dreambooth",)
def stablediffusion_dreambooth_pipeline(
    project_id: str,
    location: str,
    pipeline_identifier: str,
    training_container_uri: str,
    accelerate_args: str,
    train_script_args: str,
    train_script: str,
    input_bucket: str,
    output_bucket: str,
    access_token: str,
    service_account: str,
    staging_bucket: str,
    training_machine_type: str,
    training_accelerator_type: str,
    training_accelerator_count: int,
    serving_container_uri: str,
    serving_output_bucket: str,
    serving_service_account: str,
    parent_model: str,
):
    #labels = build_labels(model_name=model_name, instance_prompt=instance_prompt, class_prompt=class_prompt, input_bucket=input_bucket, timestamp=timestamp).outputs['Output']
    training_env = build_training_env(
        input_bucket=input_bucket,
        access_token=access_token,
        accelerate_args=accelerate_args,
        train_script=train_script,
        train_script_args=train_script_args,
        project_id=project_id
    ).outputs['Output']
    model_description = build_model_description(pipeline_identifier, train_script_args).outputs['Output']
    base_output_dir = build_base_output_dir(output_bucket, pipeline_identifier).outputs['Output']
    serving_env = build_serving_env(
        project_id=project_id,
        serving_output_bucket=serving_output_bucket,
        base_output_dir=base_output_dir,
    ).outputs['Output']

    fine_tuning_job = gcc_aip.CustomContainerTrainingJobRunOp(
        display_name=pipeline_identifier,
        container_uri=training_container_uri,
        #labels = labels,
        environment_variables=training_env,
        service_account=service_account,
        machine_type=training_machine_type,
        accelerator_type=training_accelerator_type,
        accelerator_count=training_accelerator_count,
        replica_count=1,
        boot_disk_type="pd-ssd",
        boot_disk_size_gb=100,
        base_output_dir=base_output_dir,
        # resulting model
        model_display_name=pipeline_identifier,
        model_serving_container_image_uri=serving_container_uri,
        model_serving_container_predict_route="/txt2img",
        model_serving_container_health_route="/healthz",
        model_serving_container_command=[],
        model_serving_container_environment_variables=serving_env,
        model_serving_container_ports=[3000],
        model_description=model_description,
        #parent_model=parent_model,
        #model_labels = labels,
        is_default_version=True,
        model_version_description=model_description,
        staging_bucket=staging_bucket)

    endpoint_create_op = gcc_aip.EndpointCreateOp(project=project_id,
                                                  location=location,
                                                  display_name=pipeline_identifier)

    gcc_aip.ModelDeployOp(model=fine_tuning_job.outputs["model"],
                          endpoint=endpoint_create_op.outputs["endpoint"],
                          dedicated_resources_min_replica_count=1,
                          dedicated_resources_max_replica_count=1,
                          dedicated_resources_machine_type="n1-standard-4",
                          dedicated_resources_accelerator_type="NVIDIA_TESLA_T4",
                          dedicated_resources_accelerator_count=1,
                          service_account=serving_service_account)


compiler.Compiler().compile(pipeline_func=stablediffusion_dreambooth_pipeline,
                            package_path='stablediffusion_dreambooth_pipeline.json')
