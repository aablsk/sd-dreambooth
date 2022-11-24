from google.cloud import aiplatform

project_id = "sd-dreambooth-aablsk"
location = "europe-west1"
staging_bucket = "gs://pipeline-artifacts-aablsk"
input_bucket = "gs://instance-images-aablsk"
output_bucket ="gs://sd-db-model-finetuned"
instance_prompt="\"a photo of sks dog\""
access_token="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" #consider getting this from secret manager!
serving_output_bucket="stable-diffusion-endpoint-results"

aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)

job = aiplatform.PipelineJob(
    display_name = "fine-tune-sd-db-pipeline",
    template_path = "./stablediffusion_dreambooth_pipeline.json",
    pipeline_root = "gs://pipeline-artifacts-aablsk",
    parameter_values = {
        "project_id": project_id,
        "location": location,
        "staging_bucket": staging_bucket,
        "input_bucket": input_bucket,
        "output_bucket": output_bucket,
        "instance_prompt": instance_prompt,
        "access_token": access_token, 
        "training_container_uri": "europe-west1-docker.pkg.dev/${project_id}/stablediffusion-dreambooth/finetune-16gb-prebuilt:latest",
        "serving_container_uri": "europe-west1-docker.pkg.dev/${project_id}/stablediffusion-dreambooth/server-no-model:latest",
        "serving_output_bucket": serving_output_bucket,
        "service_account": "vertexai-training@${project_id}.iam.gserviceaccount.com",
        "training_machine_type": "n1-standard-8",
        "training_accelerator_type": "NVIDIA_TESLA_P100",
        "training_accelerator_count": 1,
        "class_prompt": "\"a photo of dog\"",
        #"parent_model": None,
        "model_name": "CompVis/stable-diffusion-v1-4",
    },
    project = project_id,
    location = "europe-west1",
)

job.submit(service_account="vertexai-training@${project_id}.iam.gserviceaccount.com")
