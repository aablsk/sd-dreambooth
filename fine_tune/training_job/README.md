Contains the required resources to build the training job image and a cloudbuild pipeline definition to do so automatically.

# Update container
1. Adapt training script `train_dreambooth.py`, wrapper script `train.sh`, dependencies in `requirements.txt` or `Dockerfile`
1. Commit and push to GitHub repo. This will trigger a rebuild of the image.
