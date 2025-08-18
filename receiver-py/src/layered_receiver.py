#!/usr/bin/env python3
"""
Layered Receiver - Implementación completa de arquitectura de capas
Integra: Transmisión → Enlace → Presentación → Aplicación
"""

import asyncio
import websockets
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import logging

# Import capas existentes
from algorithms import verify_crc, hamming74_decode, bytes_to_bits, bits_to_bytes, parse_frame_header
from presentation import bits_to_ascii, ascii_to_bits
from link import LinkLayer
import noise

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReceptionResult:
    """Resultado del procesamiento de una trama recibida"""
    timestamp: float
    success: bool
    original_frame_hex: str
    frame_size: int
    msg_type: int
    algorithm: str
    recovered_message: str
    error_message: Optional[str] = None
    corrected_positions: List[int] = None
    processing_time: float = 0.0
    
    # Estadísticas detalladas
    crc_valid: bool = False
    hamming_corrections: int = 0
    total_bits: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON"""
        return asdict(self)


class LayeredReceiver:
    """Receptor que implementa arquitectura de 5 capas"""
    
    def __init__(self):
        self.link_layer = LinkLayer()
        self.stats = {
            'total_received': 0,
            'successful': 0,
            'failed': 0,
            'crc_valid': 0,
            'crc_invalid': 0,
            'hamming_corrected': 0,
            'hamming_failed': 0,
            'total_processing_time': 0.0
        }
        self.recent_results = []  # Buffer circular para UI
        self.max_recent = 100
    
    def process_frame(self, frame_bytes: bytes) -> ReceptionResult:
        """
        Procesa una trama a través de todas las capas.
        
        Flujo: Transmisión → Enlace → Presentación → Aplicación
        """
        start_time = time.time()
        
        result = ReceptionResult(
            timestamp=start_time,
            success=False,
            original_frame_hex=frame_bytes.hex(),
            frame_size=len(frame_bytes),
            msg_type=0,
            algorithm="unknown",
            recovered_message="",
            total_bits=len(frame_bytes) * 8
        )
        
        try:
            logger.info(f"📥 Procesando frame de {len(frame_bytes)} bytes")
            
            # CAPA 1: TRANSMISIÓN (ya recibida)
            # Frame recibido como bytes
            
            # CAPA 2: ENLACE - Procesamiento inteligente según tipo de frame
            logger.debug("🔗 Capa Enlace: Analizando frame...")
            
            # Intentar parse básico para obtener el tipo de mensaje
            try:
                # Extraer header tentativo para determinar tipo
                if len(frame_bytes) < 7:
                    result.error_message = "Frame too short"
                    self.stats['failed'] += 1
                    return result
                    
                # Obtener tipo de mensaje del header (antes de CRC)
                tentative_msg_type = frame_bytes[0]
                result.msg_type = tentative_msg_type
                logger.info(f"🔍 Tipo de mensaje detectado: 0x{tentative_msg_type:02x}")
                
                # Manejo simple y robusto del tipo de mensaje con ruido
                if tentative_msg_type == 0x01:
                    # CRC claro
                    algorithm_type = "crc"
                elif tentative_msg_type == 0x02:
                    # Hamming claro
                    algorithm_type = "hamming"
                elif tentative_msg_type in [0x03, 0x06, 0x07]:
                    # Posible Hamming con ruido (0x02 con bits cambiados)
                    algorithm_type = "hamming"
                    logger.warning(f"⚠️ Tipo sospechoso 0x{tentative_msg_type:02x}, asumiendo Hamming")
                elif tentative_msg_type in [0x00, 0x05, 0x04]:
                    # Posible CRC con ruido (0x01 con bits cambiados) 
                    algorithm_type = "crc"
                    logger.warning(f"⚠️ Tipo sospechoso 0x{tentative_msg_type:02x}, asumiendo CRC")
                else:
                    # Por defecto, intentar Hamming (más tolerante)
                    algorithm_type = "hamming"
                    logger.warning(f"⚠️ Tipo desconocido 0x{tentative_msg_type:02x}, probando Hamming")
                
                # Procesamiento según algoritmo detectado
                if algorithm_type == "crc":
                    # RAW + CRC: verificación estándar
                    result.algorithm = "crc"
                    is_crc_valid, msg_type, payload = self.link_layer.parse_frame(frame_bytes)
                    
                    if not is_crc_valid:
                        result.error_message = "CRC validation failed"
                        self.stats['crc_invalid'] += 1
                        self.stats['failed'] += 1
                        logger.warning("❌ CRC inválido - descartando frame")
                        return result
                        
                    result.crc_valid = True
                    self.stats['crc_valid'] += 1
                    decoded_bits = bytes_to_bits(payload)
                    logger.debug("✅ Frame CRC válido")
                    
                elif algorithm_type == "hamming":
                    # HAMMING + CRC: corrección primero, luego CRC
                    result.algorithm = "hamming"
                    logger.debug("🔧 Frame Hamming detectado - aplicando corrección...")
                    
                    # Proceso especial para Hamming
                    success, corrected_frame, corrections = self._process_hamming_frame(frame_bytes)
                    
                    if not success:
                        result.error_message = "Hamming processing failed"
                        self.stats['hamming_failed'] += 1
                        self.stats['failed'] += 1
                        logger.error("❌ Error en procesamiento Hamming")
                        return result
                    
                    # Verificar CRC del frame corregido
                    is_crc_valid, msg_type, payload = self.link_layer.parse_frame(corrected_frame)
                    
                    if not is_crc_valid:
                        result.error_message = "CRC validation failed after Hamming correction"
                        self.stats['crc_invalid'] += 1
                        self.stats['failed'] += 1
                        logger.warning("❌ CRC inválido incluso después de corrección Hamming")
                        return result
                    
                    result.crc_valid = True
                    result.corrected_positions = corrections
                    result.hamming_corrections = len(corrections)
                    self.stats['crc_valid'] += 1
                    
                    if corrections:
                        logger.info(f"🔧 Hamming corrigió {len(corrections)} errores")
                        self.stats['hamming_corrected'] += 1
                    
                    # Decodificar payload corregido
                    payload_bits = bytes_to_bits(payload)
                    valid_length = (len(payload_bits) // 7) * 7
                    trimmed_bits = payload_bits[:valid_length]
                    
                    try:
                        decoded_bits, _ = hamming74_decode(trimmed_bits)
                    except Exception as e:
                        result.error_message = f"Final Hamming decode failed: {str(e)}"
                        self.stats['hamming_failed'] += 1
                        self.stats['failed'] += 1
                        return result
                        
                else:
                    result.error_message = f"Unknown message type: 0x{tentative_msg_type:02x}"
                    self.stats['failed'] += 1
                    logger.error(f"❌ Tipo de mensaje desconocido: 0x{tentative_msg_type:02x}")
                    return result
                    
            except Exception as e:
                result.error_message = f"Frame parsing error: {str(e)}"
                self.stats['failed'] += 1
                logger.error(f"❌ Error parseando frame: {e}")
                return result
            
            # CAPA 3: PRESENTACIÓN - Bits → ASCII
            logger.debug("📝 Capa Presentación: Decodificando a ASCII...")
            try:
                recovered_text = bits_to_ascii(decoded_bits)
                result.recovered_message = recovered_text.rstrip('\x00')  # Remover padding nulls
                logger.info(f"📄 Mensaje recuperado: \"{result.recovered_message}\"")
                
            except Exception as e:
                result.error_message = f"ASCII decoding failed: {str(e)}"
                self.stats['failed'] += 1
                logger.error(f"❌ Error decodificando ASCII: {e}")
                return result
            
            # CAPA 4: APLICACIÓN - Mostrar resultado
            result.success = True
            self.stats['successful'] += 1
            logger.info(f"✅ Procesamiento exitoso: \"{result.recovered_message}\"")
            
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
            self.stats['failed'] += 1
            logger.error(f"💥 Error inesperado: {e}")
            
        finally:
            # Actualizar estadísticas
            result.processing_time = time.time() - start_time
            self.stats['total_received'] += 1
            self.stats['total_processing_time'] += result.processing_time
            
            # Agregar a buffer de resultados recientes
            self.recent_results.append(result)
            if len(self.recent_results) > self.max_recent:
                self.recent_results.pop(0)
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas actuales"""
        stats = self.stats.copy()
        
        if stats['total_received'] > 0:
            stats['success_rate'] = stats['successful'] / stats['total_received']
            stats['crc_success_rate'] = stats['crc_valid'] / stats['total_received']
            stats['avg_processing_time'] = stats['total_processing_time'] / stats['total_received']
        else:
            stats['success_rate'] = 0.0
            stats['crc_success_rate'] = 0.0
            stats['avg_processing_time'] = 0.0
        
        return stats
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna los últimos N resultados para UI"""
        recent = self.recent_results[-limit:] if limit > 0 else self.recent_results
        return [result.to_dict() for result in recent]
    
    def reset_stats(self):
        """Reinicia estadísticas y resultados"""
        self.stats = {
            'total_received': 0,
            'successful': 0,
            'failed': 0,
            'crc_valid': 0,
            'crc_invalid': 0,
            'hamming_corrected': 0,
            'hamming_failed': 0,
            'total_processing_time': 0.0
        }
        self.recent_results.clear()
        logger.info("📊 Estadísticas reiniciadas")
    
    def _process_hamming_frame(self, frame_bytes: bytes) -> tuple[bool, bytes, list[int]]:
        """
        Procesa un frame Hamming aplicando corrección de errores al payload.
        
        Args:
            frame_bytes: Frame completo con posibles errores
            
        Returns:
            Tuple of (success, corrected_frame, error_positions)
        """
        try:
            # Parsear estructura básica del frame
            if len(frame_bytes) < 7:  # Mínimo: header(3) + payload(0) + CRC(4)
                return False, frame_bytes, []
            
            # Extraer componentes
            header = frame_bytes[:3]  # msg_type + length
            payload_with_crc = frame_bytes[3:]  # payload + CRC
            
            if len(payload_with_crc) < 4:  # Mínimo CRC
                return False, frame_bytes, []
                
            crc_part = payload_with_crc[-4:]  # Últimos 4 bytes son CRC
            payload = payload_with_crc[:-4]   # Todo lo anterior es payload
            
            # Verificar longitud según header
            payload_length = int.from_bytes(header[1:3], 'big')
            if len(payload) != payload_length:
                logger.warning(f"⚠️ Longitud de payload no coincide: esperado {payload_length}, recibido {len(payload)}")
                # Continuar anyway, puede ser por ruido en header
            
            # Aplicar corrección Hamming al payload
            payload_bits = bytes_to_bits(payload)
            valid_length = (len(payload_bits) // 7) * 7
            trimmed_bits = payload_bits[:valid_length]
            
            if len(trimmed_bits) == 0:
                return False, frame_bytes, []
            
            # Decodificar con corrección
            decoded_bits, corrected_positions = hamming74_decode(trimmed_bits)
            
            # Re-codificar para obtener payload corregido
            from link import LinkLayer
            corrected_hamming_bits = LinkLayer.apply_hamming(decoded_bits)
            
            # Convertir a bytes con padding si necesario
            corrected_payload = bits_to_bytes(corrected_hamming_bits)
            
            # Reconstruir frame con payload corregido
            # Usar la longitud del payload corregido
            corrected_length = len(corrected_payload)
            corrected_header = bytes([header[0]]) + corrected_length.to_bytes(2, 'big')
            
            # Recalcular CRC para frame corregido
            data_part = corrected_header + corrected_payload
            
            # Calcular CRC nuevo
            import zlib
            crc_value = zlib.crc32(data_part) & 0xffffffff
            new_crc = crc_value.to_bytes(4, 'big')
            
            corrected_frame = data_part + new_crc
            
            logger.debug(f"🔧 Frame Hamming corregido: {len(corrected_positions)} errores")
            return True, corrected_frame, corrected_positions
            
        except Exception as e:
            logger.error(f"❌ Error en _process_hamming_frame: {e}")
            return False, frame_bytes, []


class WebSocketServer:
    """Servidor WebSocket que maneja conexiones de emisores"""
    
    def __init__(self, host: str = "localhost", port: int = 9000):
        self.host = host
        self.port = port
        self.receiver = LayeredReceiver()
        self.clients = set()
        
    async def handle_client(self, websocket, path=None):
        """Maneja conexión de un cliente emisor"""
        client_addr = websocket.remote_address
        self.clients.add(websocket)
        logger.info(f"🔌 Cliente conectado: {client_addr}")
        
        try:
            async for message in websocket:
                try:
                    if isinstance(message, bytes):
                        # Mensaje binario directo
                        frame_bytes = message
                        logger.debug(f"📨 Frame binario recibido: {len(frame_bytes)} bytes")
                        
                    else:
                        # Mensaje JSON (para compatibilidad con UI)
                        try:
                            data = json.loads(message)
                            if 'frame_hex' in data:
                                frame_bytes = bytes.fromhex(data['frame_hex'])
                                logger.debug(f"📨 Frame JSON recibido: {len(frame_bytes)} bytes")
                            else:
                                logger.warning("❌ Mensaje JSON sin campo 'frame_hex'")
                                continue
                        except json.JSONDecodeError:
                            # Asumir que es string hexadecimal directo
                            frame_bytes = bytes.fromhex(message)
                            logger.debug(f"📨 Frame hex recibido: {len(frame_bytes)} bytes")
                    
                    # Procesar frame a través de capas
                    result = self.receiver.process_frame(frame_bytes)
                    
                    # Enviar respuesta opcional al cliente
                    response = {
                        'status': 'processed',
                        'success': result.success,
                        'message': result.recovered_message if result.success else result.error_message,
                        'algorithm': result.algorithm,
                        'corrections': result.hamming_corrections,
                        'processing_time': result.processing_time
                    }
                    
                    await websocket.send(json.dumps(response))
                    
                except Exception as e:
                    logger.error(f"💥 Error procesando mensaje de {client_addr}: {e}")
                    error_response = {
                        'status': 'error',
                        'message': str(e)
                    }
                    try:
                        await websocket.send(json.dumps(error_response))
                    except:
                        pass  # Cliente probablemente desconectado
                        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"🔌 Cliente desconectado: {client_addr}")
        except Exception as e:
            logger.error(f"💥 Error con cliente {client_addr}: {e}")
        finally:
            self.clients.discard(websocket)
    
    async def start_server(self):
        """Inicia el servidor WebSocket"""
        server = await websockets.serve(
            self.handle_client, 
            self.host, 
            self.port,
            ping_interval=30,  # Mantener conexiones vivas
            ping_timeout=10
        )
        logger.info(f"🚀 Servidor WebSocket iniciado en ws://{self.host}:{self.port}")
        return server
    
    def get_receiver_stats(self) -> Dict[str, Any]:
        """Proxy para estadísticas del receptor"""
        return self.receiver.get_stats()
    
    def get_recent_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Proxy para resultados recientes"""
        return self.receiver.get_recent_results(limit)
    
    def reset_stats(self):
        """Proxy para reiniciar estadísticas"""
        self.receiver.reset_stats()


async def main():
    """Función principal - servidor standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Receptor por Capas - Lab 2')
    parser.add_argument('--host', default='localhost', help='Host del servidor')
    parser.add_argument('--port', type=int, default=9000, help='Puerto del servidor')
    parser.add_argument('--verbose', '-v', action='store_true', help='Logging verbose')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear y iniciar servidor
    server = WebSocketServer(args.host, args.port)
    ws_server = await server.start_server()
    
    print("🚀 Receptor por Capas - Lab 2")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"Servidor: ws://{args.host}:{args.port}")
    print("Capas implementadas:")
    print("  1. Transmisión  - WebSocket server")
    print("  2. Enlace       - CRC-32 / Hamming(7,4)")
    print("  3. Presentación - bits → ASCII")
    print("  4. Aplicación   - mostrar mensaje")
    print("\nEsperando conexiones... (Ctrl+C para salir)")
    
    try:
        # Mostrar estadísticas periódicamente
        async def show_stats():
            while True:
                await asyncio.sleep(30)  # Cada 30 segundos
                stats = server.get_receiver_stats()
                if stats['total_received'] > 0:
                    print(f"\n📊 Estadísticas: {stats['total_received']} recibidos, "
                          f"{stats['successful']} exitosos "
                          f"({stats['success_rate']:.1%} éxito)")
        
        # Ejecutar servidor y estadísticas en paralelo
        await asyncio.gather(
            ws_server.wait_closed(),
            show_stats()
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Cerrando servidor...")
        ws_server.close()
        await ws_server.wait_closed()
        
        # Mostrar estadísticas finales
        final_stats = server.get_receiver_stats()
        print("\n📊 Estadísticas Finales:")
        print(f"  Total recibidos: {final_stats['total_received']}")
        print(f"  Exitosos: {final_stats['successful']} ({final_stats['success_rate']:.1%})")
        print(f"  CRC válidos: {final_stats['crc_valid']}")
        print(f"  Hamming correcciones: {final_stats['hamming_corrected']}")
        print(f"  Tiempo promedio: {final_stats['avg_processing_time']:.3f}s")


if __name__ == "__main__":
    asyncio.run(main())