"""
Transport Layer: Socket communication
Handles WebSocket communication between emitter and receiver
"""

import asyncio
import websockets
import json
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


class TransportLayer:
    """Transport layer for WebSocket communication"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.client = None
    
    async def start_server(self, message_handler: Callable[[bytes], Any]):
        """
        Starts WebSocket server to receive frames.
        
        Args:
            message_handler: Function to handle received messages
        """
        async def handle_client(websocket, path):
            logger.info(f"Client connected from {websocket.remote_address}")
            try:
                async for message in websocket:
                    try:
                        # Parse JSON message
                        data = json.loads(message)
                        if 'frame_hex' in data:
                            frame_bytes = bytes.fromhex(data['frame_hex'])
                            result = message_handler(frame_bytes)
                            
                            # Send response back
                            response = {
                                'status': 'received',
                                'result': result
                            }
                            await websocket.send(json.dumps(response))
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        error_response = {
                            'status': 'error',
                            'message': str(e)
                        }
                        await websocket.send(json.dumps(error_response))
                        
            except websockets.exceptions.ConnectionClosed:
                logger.info("Client disconnected")
            except Exception as e:
                logger.error(f"Server error: {e}")
        
        self.server = await websockets.serve(handle_client, self.host, self.port)
        logger.info(f"Server started on {self.host}:{self.port}")
        return self.server
    
    async def send_frame(self, frame_bytes: bytes) -> Optional[dict]:
        """
        Sends frame as WebSocket client.
        
        Args:
            frame_bytes: Frame to send
            
        Returns:
            Server response or None if failed
        """
        uri = f"ws://{self.host}:{self.port}"
        try:
            async with websockets.connect(uri) as websocket:
                message = {
                    'frame_hex': frame_bytes.hex(),
                    'timestamp': asyncio.get_event_loop().time()
                }
                
                await websocket.send(json.dumps(message))
                response = await websocket.recv()
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Client error: {e}")
            return None
    
    async def stop_server(self):
        """Stops the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("Server stopped")


class MockTransport:
    """Mock transport for testing without network"""
    
    def __init__(self):
        self.transmitted_frames = []
        self.received_frames = []
    
    def send_frame(self, frame_bytes: bytes) -> dict:
        """
        Mock frame transmission.
        
        Args:
            frame_bytes: Frame to send
            
        Returns:
            Mock response
        """
        self.transmitted_frames.append(frame_bytes)
        
        return {
            'status': 'transmitted',
            'frame_size': len(frame_bytes),
            'frame_hex': frame_bytes.hex()
        }
    
    def receive_frame(self, frame_bytes: bytes, message_handler: Callable[[bytes], Any]) -> dict:
        """
        Mock frame reception.
        
        Args:
            frame_bytes: Frame to receive
            message_handler: Function to process the frame
            
        Returns:
            Processing result
        """
        self.received_frames.append(frame_bytes)
        result = message_handler(frame_bytes)
        
        return {
            'status': 'received',
            'result': result
        }
    
    def get_stats(self) -> dict:
        """Returns transmission statistics"""
        return {
            'transmitted_count': len(self.transmitted_frames),
            'received_count': len(self.received_frames),
            'total_transmitted_bytes': sum(len(frame) for frame in self.transmitted_frames),
            'total_received_bytes': sum(len(frame) for frame in self.received_frames)
        }