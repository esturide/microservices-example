import asyncio
import dataclasses
import collections

import zmq
import zmq.asyncio


@dataclasses.dataclass
class Message:
    pass


class PipelineCommunication:
    def __init__(self, socket: zmq.asyncio.Socket) -> None:
        self.__socket = socket
        self.__queue = collections.deque()

    def run(self):
        async def asyncio_run():
            while True:
                print("Waiting...")

                recv = await self.__socket.recv()

                print(recv)
                self.__queue.appendleft(recv)

                await self.__socket.send_string("Ok")

        asyncio.run(asyncio_run())


if __name__ == '__main__':
    import dotenv

    dotenv.load_dotenv()
    config = dotenv.dotenv_values()

    conx = zmq.asyncio.Context()
    sock = conx.socket(zmq.PAIR)

    DEFAULT_SOCKET_SERVER_SOCKET = config["DEFAULT_SOCKET_SERVER_SOCKET"]

    sock.bind(DEFAULT_SOCKET_SERVER_SOCKET)

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    pipeline = PipelineCommunication(sock)
    pipeline.run()
