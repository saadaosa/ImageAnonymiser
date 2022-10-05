FROM python:3.7-buster

RUN set -ex && mkdir /repo
WORKDIR /repo

ARG REQ
COPY requirements/$REQ ./requirements.txt
RUN pip install --upgrade pip==22.2.2
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"

COPY image_anonymiser/ ./image_anonymiser

ENTRYPOINT ["python3", "image_anonymiser/app_launcher.py", "--port", "7861", "--server", "0.0.0.0"]