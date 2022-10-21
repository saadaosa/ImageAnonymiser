FROM python:3.7-buster

RUN set -ex && mkdir /app
WORKDIR /app

ARG REQ
COPY requirements/$REQ ./requirements.txt
RUN pip install --upgrade pip==22.3
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"

ARG PASS
ENV STPASS $PASS
ARG URL
ENV FASTAPIURL $URL
COPY image_anonymiser/ ./image_anonymiser
RUN chmod +x image_anonymiser/launch.sh


ENTRYPOINT ["image_anonymiser/launch.sh"]