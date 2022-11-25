# This repository is for demonstration purposes only. 
Any code is provided on "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. This is intended to be used in a hands-on demonstration session with aablsk and nothing else.

# Content
This repository contains code to deploy StableDiffusion Dreambooth to Google Cloud from fine-tuning the image, building the required container images to automatically deploying the trained model to VertexAI endpoints.

# Structure

## server
The `server` directory contains required code to run, build & containerize a bentoml server that is able to host StableDiffusion Models on VertexAI endpoints.

## iac
The `iac` directory contains terraform code to set up a manually created project with the necessary resources to run 

## fine-tune
The `fine-tune` directory contains code to fine-tune a StableDiffusion model with Dreambooth as well as a pipeline to automate running the training job, creating an endpoint and deploying the new model to VertexAI.

### training_job
Contains the code for the container image that executes the actual training. Includes downloading instance images and uploading the fine tuned model.

### pipeline
Contains the pipeline code to fine tune the model with the container image from training_job, creating an VertexAI endpoint and deploying the new model to the endpoint.