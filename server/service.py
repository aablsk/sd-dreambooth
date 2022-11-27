from contextlib import ExitStack
from pathlib import Path

import torch
from typing import List
from torch import autocast
from diffusers import StableDiffusionPipeline
from diffusers import StableDiffusionImg2ImgPipeline
from diffusers import StableDiffusionInpaintPipeline

from pydantic import BaseModel
import bentoml
from bentoml.io import Image, JSON, Multipart

from gcloud import storage
import os
from datetime import datetime
import io
import re

class StableDiffusionRunnable(bentoml.Runnable):
    SUPPORTED_RESOURCES = ("nvidia.com/gpu", "cpu")
    SUPPORTS_CPU_MULTI_THREADING = True

    def __init__(self):  
        self.storage_client = storage.Client(project=os.environ['PROJECT_ID'])
        try:
            model_id = self.download_model(remote_model_path=os.environ['AIP_STORAGE_URI'], local_model_path=os.environ['MODELS_PATH'])
        except Exception as e:
            print(e)
        print(model_id)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        txt2img_pipe = StableDiffusionPipeline.from_pretrained(model_id)

        self.txt2img_pipe = txt2img_pipe.to(self.device)

        self.img2img_pipe = StableDiffusionImg2ImgPipeline(
            vae=self.txt2img_pipe.vae,
            text_encoder=self.txt2img_pipe.text_encoder,
            tokenizer=self.txt2img_pipe.tokenizer,
            unet=self.txt2img_pipe.unet,
            scheduler=self.txt2img_pipe.scheduler,
            safety_checker=self.txt2img_pipe.safety_checker,
            feature_extractor=txt2img_pipe.feature_extractor,
        ).to(self.device)

        self.inpaint_pipe = StableDiffusionInpaintPipeline(
            vae=self.txt2img_pipe.vae,
            text_encoder=self.txt2img_pipe.text_encoder,
            tokenizer=self.txt2img_pipe.tokenizer,
            unet=self.txt2img_pipe.unet,
            scheduler=self.txt2img_pipe.scheduler,
            safety_checker=self.txt2img_pipe.safety_checker,
            feature_extractor=self.txt2img_pipe.feature_extractor,
        ).to(self.device)

    def download_model(self, remote_model_path, local_model_path):
        matches = re.match("gs://(.*?)/(.*)", remote_model_path)
        bucket_name, gcs_folder_name = matches.groups()
        print(bucket_name)
        print(gcs_folder_name)
        bucket = self.storage_client.get_bucket(bucket_name=bucket_name)
        blobs = bucket.list_blobs(prefix=gcs_folder_name)  # Get list of files
        for blob in blobs:
            print(blob.name)
            if blob.name.endswith("/"):
                continue
            file_split = blob.name.split("/")
            directory = f"{local_model_path}/{'/'.join(file_split[0:-1])}"
            Path(directory).mkdir(parents=True, exist_ok=True)
            file_path = directory + "/" + file_split[-1:][0]
            print(f"downloading {blob.name} to {file_path}")
            blob.download_to_filename(file_path)
        return f"{local_model_path}/{gcs_folder_name}"


    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def txt2img(self, data):
        prompt = data.get('prompt')
        guidance_scale = data.get('guidance_scale', 7.5)
        height = data.get('height', 512)
        width = data.get('width', 512)
        num_inference_steps = data.get('num_inference_steps', 50)
        generator = torch.Generator(self.device)
        generator.manual_seed(data.get('seed'))

        if not data['safety_check']:
            self.txt2img_pipe.safety_checker = lambda images, **kwargs: (images, False)

        with ExitStack() as stack:
            if self.device != "cpu":
                _ = stack.enter_context(autocast(self.device))
            images = self.txt2img_pipe(
                prompt=prompt,
                guidance_scale=guidance_scale,
                height=height,
                width=width,
                num_inference_steps=num_inference_steps,
                generator=generator
            ).images
            image = images[0]
            return image

    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def img2img(self, init_image, data):
        new_size = None
        longer_side = max(*init_image.size)
        if longer_side > 512:
            new_size = (512, 512)
        elif init_image.width != init_image.height:
            new_size = (longer_side, longer_side)

        if new_size:
            init_image =init_image.resize(new_size)

        prompt = data["prompt"]
        strength = data.get('strength', 0.8)
        guidance_scale = data.get('guidance_scale', 7.5)
        num_inference_steps = data.get('num_inference_steps', 50)
        generator = torch.Generator(self.device)
        generator.manual_seed(data.get('seed'))

        if not data['safety_check']:
            self.img2img_pipe.safety_checker = lambda images, **kwargs: (images, False)

        with ExitStack() as stack:
            if self.device != "cpu":
                _ = stack.enter_context(autocast(self.device))

            images = self.img2img_pipe(
                prompt=prompt,
                init_image=init_image,
                strength=strength,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
            ).images
            image = images[0]
            return image

    @bentoml.Runnable.method(batchable=False, batch_dim=0)
    def inpaint(self, image, mask, data):
        prompt = data["prompt"]
        strength = data.get('strength', 0.8)
        guidance_scale = data.get('guidance_scale', 7.5)
        num_inference_steps = data.get('num_inference_steps', 50)
        generator = torch.Generator(self.device)
        generator.manual_seed(data.get('seed'))

        if not data['safety_check']:
            self.inpaint_pipe.safety_checker = lambda images, **kwargs: (images, False)

        with ExitStack() as stack:
            if self.device != "cpu":
                _ = stack.enter_context(autocast(self.device))

            images = self.inpaint_pipe(
                prompt=prompt,
                init_image=image,
                mask_image=mask,
                strength=strength,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
            ).images
            image = images[0]
            return image
        
    def upload_to_gcs(self, image, prompt):
        bucket = self.storage_client.get_bucket(os.environ['BUCKET'])
        blob_name = str(datetime.now().microsecond) + prompt + '.png'
        blob = bucket.blob(blob_name)
        link = 'https://storage.cloud.google.com/' + os.environ['BUCKET'] + '/' + blob_name
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        blob.upload_from_string(img_byte_arr.getvalue(), content_type='image/png')
        return link


stable_diffusion_runner = bentoml.Runner(StableDiffusionRunnable, name='stable_diffusion_runner', max_batch_size=10)

svc = bentoml.Service("stable_diffusion_service", runners=[stable_diffusion_runner])

def generate_seed_if_needed(seed):
    if seed is None:
        generator = torch.Generator()
        seed = torch.seed()
    return seed

class Instances(BaseModel):
    prompt: str
    guidance_scale: float = 7.5
    height: int = 512
    width: int = 512
    num_inference_steps: int = 50
    safety_check: bool = True
    seed: int = None
    
class Txt2ImgInput(BaseModel):
    instances: List[Instances]    

@svc.api(input=JSON(pydantic_model=Txt2ImgInput), output=JSON()) # TODO: expose more parameters for higher configurability
def txt2img(data, context):
    data = data.instances[0].dict()
    data['seed'] = generate_seed_if_needed(data['seed'])
    print(data.get('prompt')) # TODO: remove these debug log statements
    print(str(data)) # TODO: remove these debug log statements
    prompt = data.get('prompt')
    image = stable_diffusion_runner.txt2img.run(data)
    for i in data:
        context.response.headers.append(i, str(data[i]))
    link = stable_diffusion_runner.upload_to_gcs(image, prompt)
    return {'predictions': [{'link': link}]}

class Img2ImgInput(BaseModel):
    prompt: str
    strength: float = 0.8
    guidance_scale: float = 7.5
    num_inference_steps: int = 50
    safety_check: bool = True
    seed: int = None

img2img_input_spec = Multipart(img=Image(), data=JSON(pydantic_model=Img2ImgInput)) # TODO: needs to be reworked to work with VertexAI endpoint REST structure like txt2img()
@svc.api(input=img2img_input_spec, output=Image())
def img2img(img, data, context):
    data = data.dict()
    data['seed'] = generate_seed_if_needed(data['seed'])
    image = stable_diffusion_runner.img2img.run(img, data)
    for i in data:
        context.response.headers.append(i, str(data[i]))
    return image

inpaint_input_spec = Multipart(img=Image(), mask=Image(), data=JSON(pydantic_model=Img2ImgInput)) # TODO: needs to be reworked to work with VertexAI endpoint REST structure like txt2img()
@svc.api(input=inpaint_input_spec, output=Image())
def inpaint(img, mask, data, context):
    data = data.dict()
    data['seed'] = generate_seed_if_needed(data['seed'])
    image = stable_diffusion_runner.inpaint.run(img, mask, data)
    for i in data:
        context.response.headers.append(i, str(data[i]))
    return image
