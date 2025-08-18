import streamlit as st
import websockets
import asyncio
import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
import logging

# Import layer modules for proper frame construction
from presentation import ascii_to_bits
from link import LinkLayer
from algorithms import bits_to_bytes
from noise import inject_noise

# Configuración de la página
st.set_page_config(
    page_title="Lab 2 - Receptor en Tiempo Real",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealReceiverAPI:
    """API real para comunicarse con LayeredReceiver"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.ws_url = f"ws://{host}:{port}"
        self.connected = False
        self.last_check = 0
        self.connection_cache_duration = 3  # segundos
    
    async def check_connection_async(self) -> bool:
        """Verifica conexión de forma asíncrona"""
        try:
            # Usar asyncio.wait_for para el timeout
            connection = await asyncio.wait_for(websockets.connect(self.ws_url), timeout=5)
            async with connection as _:
                # Solo verificar que podemos conectar
                # No enviar mensajes que puedan causar errores en el servidor
                return True
        except Exception as e:
            logger.debug(f"Error conectando a {self.ws_url}: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Verifica si el servidor está disponible (con cache)"""
        now = time.time()
        if now - self.last_check < self.connection_cache_duration:
            return self.connected
        
        try:
            # Crear nuevo loop de eventos para la verificación
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.connected = loop.run_until_complete(self.check_connection_async())
            loop.close()
        except Exception as e:
            logger.debug(f"Error verificando conexión: {e}")
            self.connected = False
        
        self.last_check = now
        return self.connected
    
    async def send_test_frame_async(self, frame_hex: str) -> Optional[Dict[str, Any]]:
        """Envía frame de prueba de forma asíncrona"""
        try:
            connection = await asyncio.wait_for(websockets.connect(self.ws_url), timeout=5)
            async with connection as ws:
                message = {
                    'frame_hex': frame_hex,
                    'timestamp': time.time(),
                    'source': 'streamlit_ui'
                }
                
                await ws.send(json.dumps(message))
                response = await asyncio.wait_for(ws.recv(), timeout=10)
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Error enviando frame: {e}")
            return None
    
    def send_test_frame(self, frame_hex: str) -> Optional[Dict[str, Any]]:
        """Envía frame de prueba (versión sincrónica para Streamlit)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_test_frame_async(frame_hex))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error en send_test_frame: {e}")
            return None


def initialize_session_state():
    """Inicializa estado de la sesión"""
    if 'api' not in st.session_state:
        st.session_state.api = RealReceiverAPI()
    
    # Estadísticas simuladas para demo
    if 'stats' not in st.session_state:
        st.session_state.stats = {
            'total_received': 0,
            'successful': 0,
            'failed': 0,
            'crc_valid': 0,
            'crc_invalid': 0,
            'hamming_corrected': 0,
            'hamming_failed': 0
        }
    
    if 'recent_results' not in st.session_state:
        st.session_state.recent_results = []


def display_connection_status():
    """Muestra estado de conexión al servidor real"""
    api = st.session_state.api
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if api.check_connection():
            st.success("🟢 Conectado al receptor")
        else:
            st.error("🔴 Receptor no disponible")
            with st.expander("💡 Solución"):
                st.write("""
                **El servidor WebSocket no está corriendo. Para solucionarlo:**
                
                1. Abrir una terminal nueva
                2. Ejecutar:
                ```bash
                cd receiver-py
                source venv/bin/activate
                python src/layered_receiver.py --host localhost --port {port}
                ```
                3. Dejar corriendo y refrescar esta página
                """.format(port=api.port))
    
    with col2:
        if st.button("🔄 Reconectar"):
            api.connected = False
            api.last_check = 0
            st.rerun()
    
    with col3:
        st.write(f"📡 {api.ws_url}")


def display_server_config():
    """Configuración del servidor en el sidebar"""
    st.sidebar.header("⚙️ Configuración")
    
    st.sidebar.subheader("🌐 Servidor WebSocket")
    
    # Configuración del servidor
    host = st.sidebar.text_input("Host:", value=st.session_state.api.host)
    port = st.sidebar.number_input("Puerto:", value=st.session_state.api.port, min_value=1, max_value=65535)
    
    if st.sidebar.button("🔄 Actualizar Conexión"):
        st.session_state.api = RealReceiverAPI(host, port)
        st.rerun()
    
    # Estado actual
    st.sidebar.write(f"**URL actual:** {st.session_state.api.ws_url}")
    
    # Test de conexión manual
    if st.sidebar.button("🔍 Test Conexión"):
        with st.sidebar:
            with st.spinner("Probando conexión..."):
                if st.session_state.api.check_connection():
                    st.success("✅ Conexión exitosa")
                else:
                    st.error("❌ No se puede conectar")


def test_frame_sender():
    """Sección para enviar frames de prueba al servidor real"""
    st.header("🧪 Enviar Frame de Prueba")
    
    if not st.session_state.api.check_connection():
        st.warning("⚠️ Servidor no disponible. No se pueden enviar frames de prueba.")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        test_message = st.text_input(
            "Mensaje de prueba:",
            value="Hello Test!",
            help="Mensaje que será codificado y enviado al servidor"
        )
        
        algorithm = st.selectbox(
            "Algoritmo:",
            options=['crc', 'hamming'],
            format_func=lambda x: 'CRC-32 (Detección)' if x == 'crc' else 'Hamming(7,4) (Corrección)'
        )
        
        # Control de ruido (BER)
        st.subheader("🔊 Control de Ruido")
        
        enable_noise = st.checkbox(
            "Aplicar ruido al frame",
            value=False,
            help="Inyecta errores aleatorios en el frame antes de enviarlo"
        )
        
        ber = 0.0
        if enable_noise:
            ber = st.slider(
                "BER (Bit Error Rate):",
                min_value=0.0,
                max_value=0.1,
                value=0.01,
                step=0.001,
                format="%.3f",
                help="Probabilidad de error por bit (0.0 = sin ruido, 0.1 = 10% de errores)"
            )
            
            if ber > 0.0:
                st.warning(f"⚠️ Se aplicará ruido con BER = {ber:.3f} ({ber*100:.1f}% de probabilidad de error por bit)")
        else:
            st.info("💡 El frame se enviará sin ruido.")
    
    with col2:
        st.write("**Frame que se enviará:**")
        if test_message:
            try:
                # Construcción correcta del frame usando las capas
                link_layer = LinkLayer()
                
                # Paso 1: ASCII → bits
                message_bits = ascii_to_bits(test_message)
                payload = bits_to_bytes(message_bits)
                
                # Paso 2: Crear frame según el algoritmo
                if algorithm == 'crc':
                    frame_bytes = link_layer.build_frame(payload, 0x01)  # RAW+CRC
                else:  # hamming
                    # Para Hamming, primero codificar y luego crear frame
                    hamming_bits = link_layer.apply_hamming(message_bits)
                    hamming_payload = bits_to_bytes(hamming_bits)
                    frame_bytes = link_layer.build_frame(hamming_payload, 0x02)  # HAMMING+CRC
                
                frame_hex = frame_bytes.hex()
                # Mostrar frame completo si es corto, truncado si es largo
                if len(frame_hex) <= 64:
                    st.code(frame_hex, language='text')
                else:
                    st.code(f"{frame_hex[:32]}...{frame_hex[-32:]}", language='text')
                
                st.write(f"**Tamaño:** {len(frame_hex)//2} bytes ({len(frame_hex)} caracteres hex)")
                st.write(f"**Algoritmo:** {algorithm.upper()}")
                st.write(f"**Mensaje original:** \"{test_message}\"")
                
                if st.button("📤 Enviar Frame al Servidor", type="primary"):
                    # Aplicar ruido si está habilitado
                    final_frame_bytes = frame_bytes
                    noise_applied = False
                    errors_injected = 0
                    
                    if enable_noise and ber > 0.0:
                        # Convertir frame a bits, aplicar ruido y volver a bytes
                        frame_bits = []
                        for byte in frame_bytes:
                            for i in range(8):
                                frame_bits.append((byte >> (7-i)) & 1)
                        
                        # Aplicar ruido
                        noisy_bits, positions_changed = inject_noise(frame_bits, ber)
                        errors_injected = len(positions_changed)
                        
                        if errors_injected > 0:
                            # Convertir bits con ruido de vuelta a bytes
                            noisy_frame_bytes = bytearray()
                            for i in range(0, len(noisy_bits), 8):
                                byte_bits = noisy_bits[i:i+8]
                                if len(byte_bits) == 8:
                                    byte_value = 0
                                    for j, bit in enumerate(byte_bits):
                                        byte_value |= (bit << (7-j))
                                    noisy_frame_bytes.append(byte_value)
                            
                            final_frame_bytes = bytes(noisy_frame_bytes)
                            noise_applied = True
                    
                    st.write("### 📊 Enviando Frame...")
                    
                    if noise_applied:
                        st.warning(f"🔊 Ruido aplicado: {errors_injected} bits cambiados (BER real: {errors_injected/len(frame_bits):.4f})")
                        st.code(f"Frame original: {frame_bytes.hex()[:64]}...")
                        st.code(f"Frame con ruido: {final_frame_bytes.hex()[:64]}...")
                    
                    # Enviar el frame (con o sin ruido)
                    final_frame_hex = final_frame_bytes.hex()
                    with st.spinner("Enviando frame..."):
                        result = st.session_state.api.send_test_frame(final_frame_hex)
                    
                    if result:
                        st.success("✅ Frame enviado exitosamente")
                        st.json(result)
                        
                        # Actualizar estadísticas locales
                        st.session_state.stats['total_received'] += 1
                        if result.get('success', False):
                            st.session_state.stats['successful'] += 1
                        else:
                            st.session_state.stats['failed'] += 1
                        
                        # Agregar a resultados recientes
                        new_result = {
                            'timestamp': time.time(),
                            'message': test_message,
                            'algorithm': algorithm,
                            'noise_applied': noise_applied,
                            'ber': ber if noise_applied else 0.0,
                            'errors_injected': errors_injected if noise_applied else 0,
                            'result': result
                        }
                        st.session_state.recent_results.insert(0, new_result)
                        if len(st.session_state.recent_results) > 20:
                            st.session_state.recent_results.pop()
                        
                        st.rerun()
                    else:
                        st.error("❌ Error enviando frame al servidor")
                        
            except Exception as e:
                st.error(f"Error preparando frame: {e}")


def display_stats():
    """Muestra estadísticas actuales"""
    stats = st.session_state.stats
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📥 Total Recibidos", stats['total_received'])
    
    with col2:
        success_rate = stats['successful'] / max(stats['total_received'], 1) * 100
        st.metric("✅ Tasa de Éxito", f"{success_rate:.1f}%")
    
    with col3:
        st.metric("🔗 CRC Válidos", stats['crc_valid'])
    
    with col4:
        st.metric("🔧 Correcciones", stats['hamming_corrected'])


def display_recent_results():
    """Muestra resultados recientes"""
    results = st.session_state.recent_results
    
    if not results:
        st.info("📭 No hay resultados recientes")
        return
    
    st.write("**Últimos frames procesados:**")
    
    for i, result in enumerate(results[:10]):
        timestamp = datetime.fromtimestamp(result['timestamp']).strftime('%H:%M:%S')
        message = result['message'][:30] + "..." if len(result['message']) > 30 else result['message']
        
        with st.expander(f"{timestamp} - {message}", expanded=(i==0)):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Mensaje:** {result['message']}")
                st.write(f"**Algoritmo:** {result['algorithm'].upper()}")
                
                # Información del ruido si está disponible
                if result.get('noise_applied', False):
                    st.write(f"🔊 **Ruido:** BER {result.get('ber', 0):.3f}")
                    st.write(f"⚡ **Errores inyectados:** {result.get('errors_injected', 0)}")
                else:
                    st.write("📡 **Sin ruido**")
                    
            with col2:
                if result['result']:
                    if result['result'].get('success', False):
                        st.success("✅ Procesado exitosamente")
                    else:
                        st.error("❌ Error en procesamiento")
                    st.json(result['result'])


def main():
    """Función principal"""
    initialize_session_state()
    
    # Header
    st.title("📡 Lab 2 - Receptor en Tiempo Real")
    st.markdown("**Monitor de transmisiones con detección y corrección de errores**")
    
    # Configuración del servidor
    display_server_config()
    
    # Estado de conexión
    display_connection_status()
    
    st.divider()
    
    # Contenido principal
    tab1, tab2, tab3 = st.tabs(["📊 Estadísticas", "📋 Resultados", "🧪 Pruebas"])
    
    with tab1:
        st.header("📊 Estadísticas en Tiempo Real")
        display_stats()
        
        # Auto-refresh opcional
        if st.checkbox("🔄 Auto-refresh (cada 5s)"):
            time.sleep(5)
            st.rerun()
    
    with tab2:
        st.header("📋 Resultados Recientes")
        display_recent_results()
    
    with tab3:
        test_frame_sender()
    
    # Información en el sidebar
    with st.sidebar:
        st.divider()
        st.subheader("ℹ️ Información")
        
        if st.session_state.api.check_connection():
            st.success("Servidor activo")
        else:
            st.error("Servidor inactivo")
            
        st.write("**Puertos estándar:**")
        st.write("• LayeredReceiver: 9000")
        st.write("• Streamlit UI: 8501")
        
        if st.button("🗑️ Limpiar Datos"):
            st.session_state.stats = {
                'total_received': 0,
                'successful': 0,
                'failed': 0,
                'crc_valid': 0,
                'crc_invalid': 0,
                'hamming_corrected': 0,
                'hamming_failed': 0
            }
            st.session_state.recent_results = []
            st.success("Datos limpiados")
            st.rerun()


if __name__ == "__main__":
    main()