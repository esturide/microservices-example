import asyncio

import dotenv
from microdot.asgi import Microdot, with_websocket
from microdot.sse import with_sse
from tinydb import TinyDB
from zmq import PAIR as ZMQ_PAIR
from zmq.asyncio import Context, Socket

from security_service.models import UserModel, TokenModel

dotenv.load_dotenv()
config = dotenv.dotenv_values()

SERVER_PORT = config["DEFAULT_SERVER_SECURITY_MANAGE_PORT"]
DEFAULT_SOCKET_CLIENT_SOCKET = config["DEFAULT_SOCKET_CLIENT_SOCKET"]

app = Microdot()
db_user = TinyDB(config["DATA_USER_FILENAME"])
db_tokens = TinyDB(config["DATA_TOKEN_CACHE_FILENAME"])

ctx: Context = Context()
sock: Socket = ctx.socket(ZMQ_PAIR)


@app.post('/login')
async def login(request):
    user_req = UserModel.create(request.json)

    if user_req is None:
        return "Failure, user no found", 404

    query_user = UserModel.load(db_user, user_req.username)
    if query_user is None:
        return "Failure, user no register", 403

    if not user_req.validate_password(query_user):
        return "Failure, password is invalid", 403

    token = TokenModel.create(user_req.username)
    if not TokenModel.load(db_tokens, user_req.username):
        token.save(db_tokens)

    return token.json, 200


@app.post('/register')
async def register(request):
    if user := UserModel.create(request.json):
        if UserModel.load(db_user, user.username):
            return "User was created", 409

        user.save(db_user)

        return "Success", 201

    return "Failure", 409


@app.get('/token/validate')
def token_validate(request):
    query_token = TokenModel.load(db_tokens, request.json["username"])

    if query_token is None:
        return "Failure, token not found", 404

    if request.json["token"] != query_token.token:
        return "Failure, token is invalid", 403

    return "Success, token is valid", 200


@app.post('/token/update')
def token_update(request):
    return request.json


@app.get('/echo')
@with_websocket
async def message(request, ws):
    async def queue_message():
        while True:
            recv_ws = await ws.receive()
            print(f"Ok - Received: {recv_ws}")

            sock.send_json({
                "from": "security",
                "body": "Hello world"
            })

            recv_sock = await sock.recv_string()
            await ws.send(f"Ok - Received: {recv_sock}")

    await queue_message()


@app.route('/fibonacci')
@with_websocket
async def echo(request, ws):
    async def fibonacci(n: int):
        a, b = 0, 1

        while a < n:
            yield str(a)
            a, b = b, a + b
            await asyncio.sleep(5)

    while True:
        message = await ws.receive()
        n_fib = int(message)

        async for n in fibonacci(n_fib):
            await ws.send(n)


@app.get("/healthy")
def healthy(request):
    return "Ok", 200


@app.route('/events')
@with_sse
async def events(request, sse):
    for i in range(10):
        await asyncio.sleep(1)
        await sse.send({
            'counter': i
        })


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sock.connect(DEFAULT_SOCKET_CLIENT_SOCKET)
    app.run(debug=True, port=SERVER_PORT)
