import asyncio

import dotenv
from microdot.asgi import Microdot
from microdot.sse import with_sse
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


@app.route('/events')
@with_sse
async def events(request, sse):
    for i in range(10):
        await asyncio.sleep(1)
        await sse.send({
            'counter': i
        })


if __name__ == "__main__":
    app.run(debug=True, port=SERVER_PORT)
    sock.connect(SOCKET_QUEUE_ADDRESS)
