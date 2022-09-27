FROM python:3.7-buster

RUN set -ex && mkdir /repo
WORKDIR /repo

COPY requirements/requirements_prod.txt ./requirements.txt
RUN pip install --upgrade pip==22.2.2
RUN pip install -r requirements.txt
ENV PYTHONPATH ".:"

COPY image_anonymiser/ ./image_anonymiser

ENTRYPOINT ["python3", "-m", "image_anonymiser.app_gradio.app", "--port", "7861", "--server", "0.0.0.0"]