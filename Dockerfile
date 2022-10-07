FROM python:3.7-buster

RUN set -ex && mkdir /repo
WORKDIR /repo

ARG REQ
COPY requirements/$REQ ./requirements.txt
COPY image_anonymiser/ ./image_anonymiser
RUN chmod +x image_anonymiser/models/artifacts/get_model_weights.sh
RUN image_anonymiser/models/artifacts/get_model_weights.sh

RUN pip install --upgrade pip==22.2.2
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"

ENTRYPOINT ["python3", "image_anonymiser/app_launcher.py", "--port", "7861", "--server", "0.0.0.0"]