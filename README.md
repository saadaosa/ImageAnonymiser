## ImageAnonymiser 👻

### Running the app locally

- Clone the repo
- Set your PYTHONPATH environment variable to be the root of the repo
- Run `image_anonymiser/launch.sh` (set the args as described in `launch.sh`)

### Running the app using Docker

- Build the image: From the root directory, run `docker build --build-arg REQ=[name of the requirements file] --build-arg PASS=[pass for streamlit interface] . -t imageanonymiser`
- To run the container: `docker run --name [container name] --mount source=[volume name],target=/app/data_volume -it --rm -p [host port]:[container:port] imageanonymiser [add any args used in launch.sh]`. 