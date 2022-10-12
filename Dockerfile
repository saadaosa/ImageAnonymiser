FROM python:3.7-buster

RUN set -ex && mkdir /app
WORKDIR /app

ARG REQ
COPY requirements/$REQ ./requirements.txt
RUN pip install --upgrade pip==22.2.2
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"

ARG PASS
ENV STPASS $PASS
COPY image_anonymiser/ ./image_anonymiser
RUN chmod +x image_anonymiser/launch.sh
RUN chmod +x image_anonymiser/models/artifacts/get_model_weights.sh
RUN image_anonymiser/models/artifacts/get_model_weights.sh


ENTRYPOINT ["sh", "image_anonymiser/launch.sh"]