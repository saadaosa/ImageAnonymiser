## ImageAnonymiser 👻

### Running the app locally

- Clone the repo
- Set your PYTHONPATH environment variable to be the root of the repo
- Run `image_anonymiser/launch.sh` (set the args as described in `launch.sh`)
- Example: To start the streamlit app locally in cpu mode, run `launch.sh local streamlit cpu` (to access the admin interface of the app, you need to set the password in an environment variable called `STPASS`)

### Running the app using Docker

- Build the image: From the root directory, run `docker build --build-arg REQ=[name of the requirements file] --build-arg PASS=[your password for the streamlit admin interface] . -t imageanonymiser`
<br>
- To run the container: `docker run --mount source=[your volume name],target=/app/data_volume -it --rm -p [host port]:[container:port] imageanonymiser [add any args used in launch.sh]` (to make the gpus available in [Lambda Labs](https://lambdalabs.com/) use `--gpus \"device=${CUDA_VISIBLE_DEVICES}\"`) 

### Adding https support through Ngrok in Docker
- Run a Ngrok agent with the following command: `docker run --net=host -d -e NGROK_AUTHTOKEN=[Your token here] ngrok/ngrok:latest http [port of your application]` ([see Ngrok doc](https://ngrok.com/docs/using-ngrok-with#docker))
<br>
- To retrieve your public url, from the host where docker is running, use: `curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])"`
