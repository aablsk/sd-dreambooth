FROM europe-docker.pkg.dev/vertex-ai/training/pytorch-gpu.1-11:latest

# Installs gcloud.
#RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC
#RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg  add - && apt-get update -y && apt-get install google-cloud-cli -y

WORKDIR /trainer
RUN unset PYTHONPATH
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN mkdir ./instance-images

COPY accelerate_config.yaml .
COPY train_dreambooth.py .
COPY train.sh .

ENTRYPOINT ["./train.sh"]