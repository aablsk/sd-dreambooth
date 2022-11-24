import kfp
from kfp.v2 import compiler
from google.cloud import aiplatform
from google_cloud_pipeline_components import aiplatform as gcc_aip
from datetime import datetime as dt

@kfp.components.create_component_from_func
def build_labels(model_name: str, instance_prompt: str, class_prompt: str, input_bucket: str, timestamp: str) -> str:
    import json
    import re
    def clean_str(string: str):
        return re.sub(r'[^A-Za-z0-9\_\-]', '', string)

    return json.dumps({
        "base_model": clean_str(model_name),
        "instance_prompt": clean_str(instance_prompt),
        "class_prompt": clean_str(class_prompt),
        "instance_images": clean_str(input_bucket),
        "timestamp": clean_str(timestamp),
    })

@kfp.components.create_component_from_func
def build_training_env(input_bucket: str, output_bucket: str, instance_prompt: str, class_prompt: str, model_name: str, access_token: str) -> str:
    import json
    return json.dumps({
        "INPUT_BUCKET": input_bucket,
        "OUTPUT_BUCKET": output_bucket,
        "INSTANCE_PROMPT": instance_prompt,
        "CLASS_PROMPT": class_prompt,
        "MODEL_NAME": model_name,
        "ACCESS_TOKEN": access_token
    })

@kfp.components.create_component_from_func
def build_serving_env(project_id: str, serving_output_bucket: str) -> str:
    import json
    return json.dumps({
        "PROJECT_ID": project_id,
        "BUCKET": serving_output_bucket,
        "MODEL_PATH": "/home/bentoml/bento/src/model"
    })

@kfp.components.create_component_from_func
def build_model_description(input_bucket: str, instance_prompt: str, class_prompt: str) -> str:
    return "StableDiffusion Dreambooth fine-tuned on {} images with instance_prompt {} and class_prompt {}.".format(input_bucket, instance_prompt, class_prompt)


@kfp.components.create_component_from_func
def build_base_output_dir(output_bucket: str, pipeline_instance_identifier: str) -> str:
    return "{}/{}/".format(output_bucket, pipeline_instance_identifier)

@kfp.dsl.pipeline(
    name="stablediffusion-dreambooth",
)
def stablediffusion_dreambooth_pipeline(
    project_id: str,
    location: str,
    staging_bucket: str,
    input_bucket: str,
    output_bucket: str,
    instance_prompt: str,
    access_token: str, #consider getting this from secret manager?
    training_container_uri: str,
    serving_container_uri: str,
    serving_output_bucket: str,
    service_account: str,
    training_machine_type: str,
    training_accelerator_type: str,
    training_accelerator_count: int,
    serving_service_account: str,
    class_prompt: str = "",
    #parent_model: str = None,
    model_name: str = "CompVis/stable-diffusion-v1-4",
    ): 

    timestamp = dt.now().strftime("%Y_%m_%d__%H_%M_%S")
    pipeline_identifier = "stablediffusion-dreambooth"
    pipeline_instance_identifier = "{}_{}".format(pipeline_identifier, timestamp)

    labels = build_labels(model_name=model_name, instance_prompt=instance_prompt, class_prompt=class_prompt, input_bucket=input_bucket, timestamp=timestamp).outputs['Output']
    training_env = build_training_env(input_bucket=input_bucket, output_bucket=output_bucket, instance_prompt=instance_prompt, class_prompt=class_prompt, model_name=model_name, access_token=access_token).outputs['Output']
    serving_env = build_serving_env(project_id=project_id, serving_output_bucket=serving_output_bucket).outputs['Output']

    model_description = build_model_description(input_bucket, instance_prompt, class_prompt).outputs['Output']
    base_output_dir = build_base_output_dir(output_bucket, pipeline_instance_identifier).outputs['Output']

    fine_tuning_job = gcc_aip.CustomContainerTrainingJobRunOp(
        display_name = "training-pipeline_{}".format(pipeline_instance_identifier),
        container_uri = training_container_uri,
        model_serving_container_image_uri = serving_container_uri,
        model_serving_container_predict_route = "/txt2img",
        model_serving_container_health_route = "/healthz",
        model_serving_container_command = ["serve", "production"],
        model_serving_container_environment_variables = serving_env,
        model_serving_container_ports = [3000],
        model_description = model_description,
        project = project_id,
        location = location,
        #labels = labels,
        staging_bucket = staging_bucket,
        model_display_name = pipeline_identifier,
        #model_labels = labels,
        #parent_model = parent_model,
        is_default_version = True,
        model_version_description = pipeline_instance_identifier,
        base_output_dir = base_output_dir,
        service_account = service_account,
        environment_variables = training_env,
        replica_count = 1,
        machine_type = training_machine_type,
        accelerator_type = training_accelerator_type,
        accelerator_count = training_accelerator_count,
        boot_disk_type = "pd-ssd",
        boot_disk_size_gb = 100,
    )

    endpoint_create_op = gcc_aip.EndpointCreateOp(
        project = project_id,
        location = location,
        display_name = pipeline_identifier
    )

    gcc_aip.ModelDeployOp(
        model = fine_tuning_job.outputs["model"],
        endpoint = endpoint_create_op.outputs["endpoint"],
        dedicated_resources_min_replica_count = 1,
        dedicated_resources_max_replica_count = 1,
        dedicated_resources_machine_type = "n1-standard-4",
        dedicated_resources_accelerator_type = "NVIDIA_TESTLA_T4",
        dedicated_resources_accelerator_count = 1,
        service_account = serving_service_account
    )

compiler.Compiler().compile(pipeline_func=stablediffusion_dreambooth_pipeline,
    package_path='stablediffusion_dreambooth_pipeline.json')
