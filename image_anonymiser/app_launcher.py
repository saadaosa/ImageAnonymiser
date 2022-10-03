import argparse
from pathlib import Path

from image_anonymiser.app_gradio.app import App

DEFAULT_PORT = 7861
PAR_DIR = Path(__file__).resolve().parent
FAVICON = PAR_DIR / "favicon.png"

def main(args):
    if args.engine == "gradio":
        app = App()
        app.make_ui()
        app.demo.launch(server_name = args.server, server_port= args.port, share=args.share, 
                        debug=args.debug, show_api=False, favicon_path=FAVICON)
    else:
        raise ValueError("Incorrect app engine. Use gradio")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", 
                        default="gradio", 
                        type=str, 
                        help="App engine. Only Gradio supported for the time being")
    parser.add_argument("--port", 
                        default=DEFAULT_PORT, 
                        type=int, 
                        help=f"Port for the gradio server. Default is {DEFAULT_PORT}")
    parser.add_argument("--server", 
                        default=None, 
                        type=str, 
                        help=f"Server name, to make app accessible on local network, set this to 0.0.0.0. Default is None")
    parser.add_argument("--share", 
                        default=False, 
                        type=bool, 
                        help=f"If True creates a 72h shareable link on gradio domain. Default is False")
    parser.add_argument("--debug", 
                        default=False, 
                        type=bool, 
                        help=f"Used for gradio debug mode. Default is False")
    args = parser.parse_args()
    main(args)