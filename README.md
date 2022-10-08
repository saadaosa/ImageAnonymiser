## ImageAnonymiser 👻

### Running the app locally

- Clone the repo
- Set your PYTHONPATH environment variable to be the root of the repo
- Set W&B API key environment variable (Instructions below)
- From the root of the repo, run `image_anonymiser/app_launcher.py` (modify any args as described in `app_launcher.py`)

### Running the app using Docker
- Set W&B API key environment variable (Instructions below)
- Build the image: From the root directory, run `docker build --build-arg REQ=[name of the requirements file] --build-arg WANDB_API_KEY=$WANDB_API_KEY . -t imageanonymiser`
- To run the container: `docker run -it --rm -p [host port]:[container:port] imageanonymiser [add any args used in app_launcher]`


### Setting W&B API key
- Copy your API key from https://wandb.ai/authorize
- Set the WANDB_API_KEY environment variable by running `export WANDB_API_KEY=[paste your api key]`
