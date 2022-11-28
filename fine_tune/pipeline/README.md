Contains the required resources to run an automated pipeline which builds fine-tunes the image then stores the model in Model Registry and deploys it to an Endpoint.

# Create a pipeline job
1. Adapt configuration in create_pipeline_job.py
1. ```ACCESS_TOKEN=$YOUR_HUGGING_FACE_ACCESS_TOKEN_VALUE python3 create_pipeline_job.py```

# Manually import a model
1. Adapt configuration in import_model.py
1. ```python3 import_model.py```

# Update pipeline definition
1. Adapt pipeline definition in `pipeline.yaml`
1. Commit & push to git which will trigger Cloud Build pipeline
