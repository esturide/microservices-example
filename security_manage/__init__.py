import asyncio
import dotenv

from tinydb import TinyDB
from microdot import Microdot
from microdot.websocket import with_websocket
from zmq import PAIR as ZMQ_PAIR
from zmq.asyncio import Context

from security_manage.models import UserModel, TokenModel

# from microdot.asgi import Microdot, with_websocket

dotenv.load_dotenv()
config = dotenv.dotenv_values()

SERVER_PORT = config["DEFAULT_SERVER_SECURITY_MANAGE_PORT"]
SOCKET_QUEUE_PORT = config["SOCKET_QUEUE_PORT"]
SOCKET_QUEUE_ADDRESS = "tcp://*:%s" % SOCKET_QUEUE_PORT

app = Microdot()
db_user = TinyDB(config["DATA_USER_FILENAME"])
db_tokens = TinyDB(config["DATA_TOKEN_CACHE_FILENAME"])

ctx = Context()
sock = ctx.socket(ZMQ_PAIR)


@app.route('/login', methods=['POST'])
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


@app.route('/register', methods=['POST'])
async def register(request):
    if user := UserModel.create(request.json):
        if UserModel.load(db_user, user.username):
            return "User was created", 409

        user.save(db_user)

        return "Success", 201

    return "Failure", 409


@app.route('/token/validate', methods=['GET'])
def token_validate(request):
    token = TokenModel(**request.json)
    query_token = TokenModel.load(db_tokens, token.username)

    if query_token is None:
        return "Failure, token not found", 404

    if token.token != query_token.token:
        return "Failure, token is invalid", 403

    return "Success, token is valid", 200


@app.route('/token/update', methods=['POST'])
def token_update(request):
    return request.json


@app.route('/echo')
@with_websocket
async def message(request, ws):
    async def queue_message():
        while True:
            recv = await ws.receive()
            await sock.send(recv.encode())

            msg = await sock.recv()
            await ws.send(
                f"Echo: {msg}"
            )

    task_message_queue = asyncio.create_task(queue_message())

    await task_message_queue


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


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    app.run(debug=True, port=SERVER_PORT)
    sock.bind(SOCKET_QUEUE_ADDRESS)
