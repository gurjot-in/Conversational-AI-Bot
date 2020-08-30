import aiohttp
import asyncio
import async_timeout
from flask import Flask, request, abort


loop = asyncio.new_event_loop()
app = Flask(__name__)


async def incoming_2_outgoing_payload(payload):
    """Conveert json to xml."""
    from decoder import Dict2XML
    # need to convert int keys to str, dict2xml can't handle int values
    return Dict2XML().parse({
        "vacation": {k: str(v) for k, v in payload.items()}})


async def fetch(url, payload):
    print("Triggering url {}".format(url))
    body = incoming_2_outgoing_payload(payload)

    async with aiohttp.ClientSession() as session, \
            async_timeout.timeout(10):
        async with session.post(url, data=body) as response:
            return await response.text()
    return None


def notified(responses):
    return "I notifed everyone - you are ready to go on vacation 🏖"


def ensure_future(tasks):
    if not asyncio.futures.isfuture(tasks):
        return None
    return asyncio.gather(tasks)


def is_valid_vacation_request(payload):
    return (payload["employee"] is not None and
            payload["end"] > payload["start"])


@app.route("/health")
def health():
    return "Ok"


@app.route("/vacation", methods=["POST"])
def index():
    """Employe can send a webrequest to this endpoint to request vacation.

    The request will be forwarded to internal systems to register the
    vacation. The format of the reuqest should be

    Example:
        $ curl \
            -XPOST \
            -H "Content-Type: application/json" \
            localhost:5000/vacation \
            -d '{"employee":"tom", "start": 1549381557, "end": 1549581523}'

    """

    payload = request.json
    if not is_valid_vacation_request(payload):
        abort(404, "Invalid vacation request!")

    # perform multiple async requests concurrently
    # to notify webhooks
    responses = loop.run_until_complete(asyncio.gather(
        fetch("https://api.hr-management.com/webhook", payload),
        fetch("https://api.hr-management.com/webhook", payload),
        fetch("https://api.sprintboard.com/notify", payload)
    ))

    # do something with the results
    return notified(responses)


app.run(debug=False, use_reloader=False)
