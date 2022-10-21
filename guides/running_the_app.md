## 👻 Guide: How to run the app 

This guide will help you in running the app in both local and docker modes

### Running the app locally

- Clone the repo
- Set your `PYTHONPATH` environment variable to be the root of the repo
- Create a virtual environment and install the requirements ([see below](####Installing-the-requirements)). Activate the environment
- If you are using the **FastAPI** prediction endpoint, you need first to start the server ([see below](####Starting-the-FastAPI-app)). You also need to set the environment variable `FASTAPIURL` which contains the host and port of the FastAPI app (defaults to `http://127.0.0.1:8000` if the variable is not set)
- Run `image_anonymiser/models/artifacts/get_model_weights.sh` in order to download the model weights and store them in the folder `image_anonymiser/models/artifacts`
<br>

- To run the **Gradio app** (from the root folder):
  - `python image_anonymiser/app_gradio/app.py [args]`
  - The args are:
    - `--port`: Port for the gradio server. Default is 7861
    - `--server`: Server name, to make app accessible on local network, set this to `0.0.0.0`. Default is None
    - `--share`: If True creates a 72h shareable link on gradio domain. Default is False
    - `--debug`: Used for gradio debug mode. Default is False
    - `--bconfig`: Name of the backend config file. Default is config.yml (backend config files need to be placed in `image_anonymiser/backend/configs`)
<br>

- To run the **Streamlit app** (from the root folder):
  - `python -m streamlit run image_anonymiser/app_streamlit/1__Home.py -- [args]`
  - The args are:
    - `--bconfig`: Name of the backend config file. Default is config.yml (backend config files need to be placed in `image_anonymiser/backend/configs`)
  - Notes:
    - You can specify arguments that are specific to the streamlit engine (example: to limit the file size use `--server.maxUploadSize=your_limit`). For more information see [Streamlit docs](https://docs.streamlit.io/library/advanced-features/configuration)
    - Streamlit args need to be seperated from the app args by using `--`; for instance to limit the upload size to 5MB and specify a different config file use `--server.maxUploadSize=5 -- --bconfig=other_config.yml`
    - The admin interface reads the password from an environment variable called `STPASS`. Set this variable to your own password (if not, a default one will be used)
<br>

- A script (`image_anonymiser/launch.sh`) can be used/modified to run either the Gradio or Streamlit app:
  - It expects the following arguments: `[local | docker] [streamlit | gradio] [gpu | cpu] [gradio_args]`
  - Example: To start the streamlit app locally in cpu mode, run `launch.sh local streamlit cpu` 

#### Installing the requirements

- If you are not using the prediction endpoint which means that the detection models are embedded in the app (**inapp mode**), install `requirements_all.txt` (or the gpu version if you have access to a GPU during inference)
- If you want to use the `FatAPI` app (**api mode**), you can either install the additional requirements (FastAPI, uvicorn and Pydantic), or have two separate environments: one for the api server (`requirements_api.txt`) and one for the web apps (`requirements_app.txt`). This can be helpful if you want ultimately to deploy the prediction server and the web apps separately    

#### Starting the FastAPI app

- Run `uvicorn image_anonymiser.backend.apiserver:app`
- If you are in development mode, you can also add the `--reload` argument, in order to restart the app when you change any source file (as long as they are watched)
- You can also change the host name (using `--host`) and the port (using `--port`)
- The FastAPI app requires a backend config file that is also retrieved from `image_anonymiser/backend/configs`. The name of the conig file should be in the environment variable `FASTAPICONFIG`. If this variable is not set, the default is config.yml

### Running the app using Docker

#### Docker files

There are three docker files in the `docker` folder that you can use/adapt to your need:

- **Dockerfile.all**:
  - Used to build the application in **inapp mode** (no FastAPI inference endpoint)
  - The `build` arguments that need to be passed during the build process are `REQ` (name of the requirements file in the requirements folder), and `STPASS` (the password for the Streamlit admin interface)
  - For example, to build an `imageanonymiser` image for cpu inference, from the root folder use `docker build -f docker/Dockerfile.all --build-arg REQ=requirements_all.txt --build-arg PASS=your_password . -t imageanonymiser`
  - The entrypoint is the `launch.sh` script (mentioned above), which allows you to choose between Streamlit and Gradio 
  - To run the container: `docker run -it --rm -p host_port:container_port imageanonymiser [add args used in launch.sh]` (there are potentially other points to consider when running your container, [see below](####Other-runtime-considerations))
<br>

- **Dockerfile.api**:
  - Used to build the FastAPI application (**api mode**)
  - The `build` arguments that need to be passed during the build process are `REQ` (name of the requirements file in the requirements folder), and `CONFIG` (the name of the config file in `image_anonymiser/backend/configs`)
  - For example, to build an `imageanonymiser_api` image for cpu inference, from the root folder use `docker build -f docker/Dockerfile.api --build-arg REQ=requirements_api.txt --build-arg CONFIG=config.yml . -t imageanonymiser_api`
  - The entrypoint runs `uvicorn` with a 0.0.0.0 hostname (but doesn't specify the port) 
  - To run the container: `docker run -d -p host_port:container_port imageanonymiser_api --port=container_port` (there are potentially other points to consider when running your container, [see below](####Other-runtime-considerations))
<br>

- **Dockerfile.app**:
  - Used to build the web apps in **api mode**
  - The `build` arguments that need to be passed during the build process are `REQ` (name of the requirements file in the requirements folder), `STPASS` (the password for the Streamlit admin interface) and `URL` (the host and port of the FastAPI app)
  - For example, to build an `imageanonymiser_app` image for cpu inference, from the root folder use `docker build -f docker/Dockerfile.app --build-arg REQ=requirements_app.txt --build-arg PASS=your_password --build-arg URL=host_name:fastapi_host_port . -t imageanonymiser_app`
  - The entrypoint is the `launch.sh` script (mentioned above), which allows you to choose between Streamlit and Gradio
  - To run the container: `docker run -it --rm -p host_port:container_port imageanonymiser_app [add args used in launch.sh]` (there are potentially other points to consider when running your container, [see below](####Other-runtime-considerations))
<br>

Note: During the build process of the images containing the inference code, the script `get_model_weights.sh` is executed in order to download the model weights

#### Other runtime considerations

- To make the gpus available in [Lambda Labs](https://lambdalabs.com/) use `--gpus \"device=${CUDA_VISIBLE_DEVICES}\"` when your run the container with the inference code (in the examples above, this is relevant for `imageanonymiser` and `imageanonymiser_api`)
<br>

- The Streamlit app saves feedbacks and user annotations in a folder called `data_volume`. To persist the data on the host machine and have access to it accross different container runs, you can use a `docker volume`. In the run command add `--mount source=your_volume_name,target=/app/data_volume` (in the examples above, this is relevant for `imageanonymiser` and `imageanonymiser_app`)  


#### Adding https support through Ngrok in Docker

- Run a Ngrok agent with the following command: `docker run --net=host -d -e NGROK_AUTHTOKEN=your_token ngrok/ngrok:latest http application_port` ([see Ngrok doc](https://ngrok.com/docs/using-ngrok-with#docker))
<br>

- To retrieve your public url, from the host where docker is running, use: 
  
  `curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"`
