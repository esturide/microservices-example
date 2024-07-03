import asyncio
import dataclasses
import collections
import sys
import json
import abc

import zmq
import zmq.asyncio


@dataclasses.dataclass
class Message:
    sender: str
    addressee: str
    body: str

    @property
    def json(self) -> dict:
        return {
            "sender": self.sender,
            "addressee": self.addressee,
            "body": self.body
        }

    @staticmethod
    def create_from_b(_recv: bytes):
        decode = _recv.decode()


class PipelineInterface(abc.ABC):
    @abc.abstractmethod
    async def run(self): ...


class PipelineCommunicationServer(PipelineInterface):
    def __init__(self, socket: zmq.asyncio.Socket) -> None:
        self.__socket = socket
        self.__queue = collections.deque()

    async def run(self):
        while True:
            print("Waiting...")

            recv = await self.__socket.recv()
            recv_s = recv.decode()

            self.__queue.appendleft(json.loads(recv_s))
            print(self.__queue)

            await self.__socket.send_string("Ok, message received")

    async def recv(self):
        pass

    async def send(self):
        pass


class PipelineClient(PipelineInterface):
    def __init__(self):
        pass

    async def run(self):
        pass


if __name__ == '__main__':
    import dotenv

    dotenv.load_dotenv()
    config = dotenv.dotenv_values()

    conx = zmq.asyncio.Context()
    sock = conx.socket(zmq.PAIR)

    DEFAULT_SOCKET_SERVER_SOCKET = config["DEFAULT_SOCKET_SERVER_SOCKET"]

    sock.bind(DEFAULT_SOCKET_SERVER_SOCKET)

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    server = PipelineCommunicationServer(sock)
    asyncio.run(server.run())
