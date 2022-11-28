Contains the code to build a serving container based on bentoml. The service loads the model from GCS and then serves it at `:3000/txt2img`. Code could be adapted to serve image-to-image or inpainting pipeline, too.

# Update container
1. Make changes to `service.py`. 
1. If you change dependencies, make sure to add them in both `bentofile.yaml` and `requirements.txt`
1. Commit and push to Github repository. This will trigger a rebuild of the image with Cloud Build.
