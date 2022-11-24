import os
from google.cloud import aiplatform

project_id = "sd-db-tf"
location = "europe-west1"
staging_bucket = "gs://vertexai_pipeline_staging_{}".format(project_id)
input_bucket = "gs://instance_images_dog_{}".format(project_id)
output_bucket ="gs://stable-diffusion-dreambooth-models_{}".format(project_id)
instance_prompt="\"a photo of sks dog\""
access_token=os.environ['ACCESS_TOKEN'] #consider getting this from secret manager!
serving_output_bucket="render-results_{}".format(project_id)
training_service_account="vertexai-training@{}.iam.gserviceaccount.com".format(project_id)
serving_service_account="vertexai-prediction@{}.iam.gserviceaccount.com".format(project_id)

aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)

job = aiplatform.PipelineJob(
    display_name = "fine-tune-sd-db-pipeline",
    template_path = "gs://vertexai_pipeline_definition_sd-db-tf/stablediffusion_dreambooth_pipeline.json",
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
