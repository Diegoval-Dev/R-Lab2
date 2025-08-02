# receiver-py/src/ws_server.py
import asyncio
import websockets
from websockets.exceptions import ConnectionClosedError

async def handler(websocket):
    print(f"Cliente conectado: {websocket.remote_address}")
    try:
        async for message in websocket:
            frame = message if isinstance(message, bytes) else message.encode('latin-1')
            print("Trama recibida:", frame)
    except ConnectionClosedError:
        # El cliente cerró sin enviar close frame: lo ignoramos
        pass

async def main():
    server = await websockets.serve(handler, "localhost", 9000)
    print("Servidor WebSocket escuchando en ws://localhost:9000")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
