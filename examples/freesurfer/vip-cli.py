import argparse
import json
import os

from src.VipSession import VipSession

_apikey_default = ".api_token.txt"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True, help="session name")
    parser.add_argument("--input", required=True, help="inputs directory")
    parser.add_argument("--pipeline", required=True, help="pipeline to run")
    parser.add_argument(
        "--arguments", required=True, help="JSON file containing pipeline's arguments "
    )
    parser.add_argument(
        "--api-key",
        default=_apikey_default,
        help="API key to connect to the VIP server",
    )
    args = parser.parse_args()
    return args


def unpack_json(filename):
    """
    read JSON file and returns the object
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(filename)

    with open(filename, "r", encoding="utf-8") as fi:
        return json.load(fi)


def run(args):
    # 0. Connect with VIP
    VipSession.init(api_key=args.api_key)
    # One call applies to multiple Sessions (until connection is lost).

    # 1. Create a Session
    session = VipSession(session_name=args.session)
    # 2. Upload your data on VIP servers
    session.upload_inputs(input_dir=args.input)
    # 3. Launch a pipeline on VIP
    arguments = unpack_json(args.arguments)
    session.launch_pipeline(pipeline_id=args.pipeline, input_settings=arguments)
    # 4. Monitor its progress on VIP until all executions are over
    session.monitor_workflows()
    # 5. Download the outputs from VIP servers when all executions are over
    session.download_outputs()
    # 6. Remove the data from VIP servers (inputs and outputs)
    session.finish()


def main():
    args = parse_args()
    run(args)


if "__main__" == __name__:
    main()
