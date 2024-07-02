import asyncio

import dotenv
from microdot import Microdot
from zmq import PAIR as ZMQ_PAIR
from zmq.asyncio import Context

dotenv.load_dotenv()
config = dotenv.dotenv_values()

SERVER_PORT = config["DEFAULT_SERVER_USER_MANAGE_PORT"]
SOCKET_QUEUE_PORT = config["SOCKET_QUEUE_PORT"]
SOCKET_QUEUE_ADDRESS = "tcp://localhost:%s" % SOCKET_QUEUE_PORT

app = Microdot()

ctx = Context()
sock = ctx.socket(ZMQ_PAIR)


@app.route("/")
def index(request):
    return "Ok"


if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    app.run(debug=True, port=SERVER_PORT)
    sock.connect(SOCKET_QUEUE_ADDRESS)
