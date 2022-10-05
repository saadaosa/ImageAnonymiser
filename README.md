## ImageAnonymiser 👻

### Running the app locally

- Clone the repo
- Set your PYTHONPATH environment variable to be the root of the repo
- From the root of the repo, run `image_anonymiser/app_launcher.py` (modify any args as described in `app_launcher.py`)

### Running the app using Docker

- Build the image: From the root directory, run `docker build --build-arg REQ=[name of the requirements file] . -t imageanonymiser`
- To run the container: `docker run -it --rm -p [host port]:[container:port] imageanonymiser [add any args used in app_launcher]`
