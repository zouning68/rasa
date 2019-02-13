import argparse
import logging

from sanic import Sanic
from sanic.response import json

from rasa_core.domain import Domain
from rasa_core.nlg import TemplatedNaturalLanguageGenerator
from rasa_core.trackers import DialogueStateTracker

logger = logging.getLogger(__name__)

DEFAULT_SERVER_PORT = 5056

app = Sanic(__name__)


def create_argument_parser():
    """Parse all the command line arguments for the nlg server script."""

    parser = argparse.ArgumentParser(
        description='starts the nlg endpoint')
    parser.add_argument(
        '-p', '--port',
        default=DEFAULT_SERVER_PORT,
        type=int,
        help="port to run the server at")
    parser.add_argument(
        '--sanic_workers',
        default=1,
        type=int,
        help="Number of sanic workers")
    parser.add_argument(
        '-d', '--domain',
        type=str,
        default=None,
        help="path of the domain file to load utterances from"
    )

    return parser


def generate_response(nlg_call, domain):
    """Mock response generator which generates the responses from the
    bot's domain file.
    """
    kwargs = nlg_call.get("arguments", {})
    template = nlg_call.get("template")
    sender_id = nlg_call.get("tracker", {}).get("sender_id")
    events = nlg_call.get("tracker", {}).get("events")
    tracker = DialogueStateTracker.from_dict(
        sender_id, events, domain.slots)
    channel_name = nlg_call.get("channel")

    return TemplatedNaturalLanguageGenerator(domain.templates).generate(
        template, tracker, channel_name, **kwargs)


@app.route("/nlg", methods=['POST', 'OPTIONS'])
async def nlg(request):
    """Generates the bot's response."""
    nlg_call = request.json
    response = await generate_response(nlg_call, domain)

    return json(response)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Running as standalone python application
    arg_parser = create_argument_parser()
    cmdline_args = arg_parser.parse_args()

    domain = Domain.load(cmdline_args.domain)

    app.run(host='0.0.0.0',
            port=cmdline_args.port,
            workers=cmdline_args.sanic_workers)
