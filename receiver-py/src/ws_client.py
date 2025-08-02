import asyncio
import websockets

class FrameReceiver:
    def __init__(self, uri: str):
        self.uri = uri
        self.latest_frame = None

    async def _receive_once(self):
        async with websockets.connect(self.uri) as ws:
            frame = await ws.recv()        # recibe bytes o str
            # Asegurarnos de trabajar siempre con bytes
            if isinstance(frame, str):
                frame = frame.encode('latin-1')
            print("Trama recibida:", frame)
            self.latest_frame = frame

    def run_once(self):
        asyncio.run(self._receive_once())

if __name__ == "__main__":
    receiver = FrameReceiver("ws://localhost:9000")
    receiver.run_once()
