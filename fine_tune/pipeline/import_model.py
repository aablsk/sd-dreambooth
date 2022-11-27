from google.cloud import aiplatform

project_id = "sd-db-tf"
location = "europe-west1"
serving_output_bucket = f"render-results_{project_id}"

def upload_model_sample(project_id: str, location: str, serving_output_bucket: str):

    aiplatform.init(project=project_id, location=location)

    model = aiplatform.Model.upload(
        display_name="stable-diffusion-manual-upload",
        artifact_uri="gs://stable-diffusion-dreambooth-models_sd-db-tf/stablediffusion-dreambooth_2022_11_25__08_59_03/model",
        serving_container_image_uri="{}-docker.pkg.dev/{}/stablediffusion-dreambooth/bentoml-server-no-model:latest".format(
            location, project_id),
        serving_container_predict_route="/txt2img",
        serving_container_health_route="/healthz",
        # instance_schema_uri=instance_schema_uri,
        # parameters_schema_uri=parameters_schema_uri,
        # prediction_schema_uri=prediction_schema_uri,
        description="stablediffusion-dreambooth_2022_11_25__08_59_03",
        # serving_container_command=serving_container_command,
        # serving_container_args=serving_container_args,
        serving_container_environment_variables={"PROJECT_ID": project_id,
                                                 "BUCKET": serving_output_bucket,
                                                 "MODELS_PATH": "models"},
        serving_container_ports=[3000],
        # explanation_metadata=explanation_metadata,
        # explanation_parameters=explanation_parameters,
    )

    model.wait()

    print(model.display_name)
    print(model.resource_name)
    return model


upload_model_sample(project_id=project_id, location=location, serving_output_bucket=serving_output_bucket)
