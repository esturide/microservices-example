import asyncio
import sys

import dotenv
from microdot.asgi import Microdot, with_websocket
from microdot.sse import with_sse
from zmq import PAIR as ZMQ_PAIR
from zmq.asyncio import Context

dotenv.load_dotenv()
config = dotenv.dotenv_values()

SERVER_PORT = config["DEFAULT_SERVER_USER_MANAGE_PORT"]
DEFAULT_SOCKET_CLIENT_SOCKET = config["DEFAULT_SOCKET_CLIENT_SOCKET"]

app = Microdot()

ctx = Context()
sock = ctx.socket(ZMQ_PAIR)


@app.route("/")
def index(request):
    return "Ok"


@app.route('/events')
@with_sse
async def events(request, sse):
    async def fibonacci(n: int):
        a, b = 0, 1

        while a < n:
            yield str(a)
            a, b = b, a + b
            await asyncio.sleep(1)

    if fib_n := request.args.get('fibonacci'):
        number = int(fib_n)

        async for n in fibonacci(number):
            await sse.send(str(n))

        return "Ok", 200

    return "Failure", 403


@app.get('/echo')
@with_websocket
async def message(request, ws):
    async def queue_message():
        while True:
            recv_ws = await ws.receive()
            print(f"Ok - Received: {recv_ws}")

            sock.send_json({
                "from": "user",
                "to": "security",
                "body": recv_ws
            })

            recv_sock = await sock.recv_string()
            await ws.send(f"Ok - Received: {recv_sock}")

    await queue_message()


@app.get("/healthy")
def healthy(request):
    return "Ok", 200


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    sock.connect(DEFAULT_SOCKET_CLIENT_SOCKET)
    app.run(debug=True, port=SERVER_PORT)
