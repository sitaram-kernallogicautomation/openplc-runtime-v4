import asyncio
import struct
import logging

logger = logging.getLogger(__name__)

class AsyncUnixClient:
    def __init__(self, command_queue, socket_path="/tmp/plc_runtime.socket"):
        self.command_queue = command_queue
        self.socket_path = socket_path
        self.reader = None
        self.writer = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_unix_connection(self.socket_path)
        logger.info("Connected to %s", self.socket_path)

    async def send_message(self, message: str):
        if not self.writer:
            raise RuntimeError("Writer not connected")

        data = message.encode()
        prefix = struct.pack("!I", len(data))   # 4-byte big-endian length
        raw = prefix + data

        self.writer.write(raw)
        await self.writer.drain()

        logger.info("Sent message: %s (len=%d)", message, len(data))

    async def recv_message(self, timeout: float = 0.5) -> str:
        if not self.reader:
            raise RuntimeError("Reader not connected")

        try:
            # Read 4-byte length prefix
            data = await asyncio.wait_for(self.reader.readline(), timeout)
        except TimeoutError:
            logger.error("Timeout waiting for message prefix")
            return "ERROR"

        # msg_len = struct.unpack("!I", prefix)[0]
        # msg_len = struct.unpack("!I", prefix)[0]

        # Read message body
        # data = await self.reader.readexactly(msg_len)
        message = data.decode()

        logger.info("Received message: %s", message)
        return message

async def main():
    client = AsyncUnixClient(None, "/tmp/plc_runtime.socket")
    await client.connect()
    await client.send_message("\nSTART\n")
    print("Sent START command")
    reply = await client.recv_message()
    print("Server replied:", reply)
    await client.send_message("\nSTOP\n")
    print("Sent STOP command")
    reply = await client.recv_message()
    print("Server replied:", reply)
    client.writer.close()
    await client.writer.wait_closed()

asyncio.run(main())
