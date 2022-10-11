FROM python:3.7-buster

RUN set -ex && mkdir /app
WORKDIR /app

ARG REQ
ARG PASS
COPY requirements/$REQ ./requirements.txt
COPY image_anonymiser/ ./image_anonymiser

RUN pip install --upgrade pip==22.2.2
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"
ENV STPASS $PASS
RUN chmod +x image_anonymiser/launch.sh
RUN chmod +x image_anonymiser/models/artifacts/get_model_weights.sh
RUN image_anonymiser/models/artifacts/get_model_weights.sh


ENTRYPOINT ["sh", "image_anonymiser/launch.sh"]