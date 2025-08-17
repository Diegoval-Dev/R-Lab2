"""
Streamlit UI for Lab 2 - Error Detection and Correction
Provides a demo interface for testing CRC-32 and Hamming(7,4) algorithms
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import asyncio
from typing import Dict, List, Any

# Import our layer modules
from presentation import ascii_to_bits, bits_to_ascii
from link import LinkLayer
from noise import inject_noise, calculate_error_stats
from transport import MockTransport
from algorithms import bytes_to_bits, bits_to_bytes


class LabDemo:
    """Main demo class for the lab"""
    
    def __init__(self):
        self.transport = MockTransport()
        self.link = LinkLayer()
        self.reset_stats()
    
    def reset_stats(self):
        """Reset demo statistics"""
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'crc_valid': 0,
            'crc_invalid': 0,
            'hamming_corrected': 0,
            'hamming_errors': 0,
            'total_bits_sent': 0,
            'total_errors_injected': 0,
            'transmission_times': []
        }
    
    def process_message(self, message: str, algorithm: str, ber: float) -> Dict[str, Any]:
        """
        Process a message through the complete pipeline.
        
        Args:
            message: Input text message
            algorithm: 'crc' or 'hamming'
            ber: Bit Error Rate for noise injection
            
        Returns:
            Dictionary with processing results
        """
        start_time = time.time()
        
        # Step 1: Presentation Layer - ASCII to bits
        original_bits = ascii_to_bits(message)
        
        # Step 2: Link Layer - Apply error detection/correction
        if algorithm == 'crc':
            # CRC: Convert bits to bytes, build frame
            payload_bytes = bits_to_bytes(original_bits)
            frame = self.link.build_frame(payload_bytes, msg_type=0x01)
            transmission_bits = bytes_to_bits(frame)
            
        elif algorithm == 'hamming':
            # Hamming: Encode bits, then build frame
            encoded_bits = self.link.apply_hamming(original_bits)
            payload_bytes = bits_to_bytes(encoded_bits)
            frame = self.link.build_frame(payload_bytes, msg_type=0x02)
            transmission_bits = bytes_to_bits(frame)
        
        # Step 3: Noise Layer - Inject errors
        noisy_bits, error_positions = inject_noise(transmission_bits, ber)
        
        # Step 4: Transport Layer - Simulate transmission
        noisy_frame = bits_to_bytes(noisy_bits)
        transport_result = self.transport.send_frame(noisy_frame)
        
        # Step 5: Reception and processing
        reception_result = self.process_received_frame(noisy_frame)
        
        # Calculate statistics
        processing_time = time.time() - start_time
        error_stats = calculate_error_stats(transmission_bits, noisy_bits)
        
        # Update global stats
        self.update_stats(algorithm, reception_result, error_stats, processing_time)
        
        return {
            'original_message': message,
            'original_bits': original_bits,
            'transmission_bits': transmission_bits,
            'noisy_bits': noisy_bits,
            'error_positions': error_positions,
            'error_stats': error_stats,
            'transport_result': transport_result,
            'reception_result': reception_result,
            'processing_time': processing_time,
            'algorithm': algorithm,
            'ber': ber
        }
    
    def process_received_frame(self, frame_bytes: bytes) -> Dict[str, Any]:
        """Process a received frame"""
        result = {
            'valid': False,
            'recovered_message': '',
            'msg_type': 0,
            'corrected_positions': [],
            'error': None
        }
        
        try:
            # Parse frame
            is_valid, msg_type, payload = self.link.parse_frame(frame_bytes)
            result['msg_type'] = msg_type
            
            if not is_valid:
                result['error'] = 'CRC validation failed'
                return result
            
            if msg_type == 0x01:  # RAW + CRC
                # Direct payload to ASCII
                payload_bits = bytes_to_bits(payload)
                recovered_message = bits_to_ascii(payload_bits)
                result['recovered_message'] = recovered_message
                result['valid'] = True
                
            elif msg_type == 0x02:  # HAMMING + CRC
                # Decode Hamming first
                payload_bits = bytes_to_bits(payload)
                decoded_bits, corrected_positions, success = self.link.verify_hamming(payload_bits)
                
                if success:
                    result['corrected_positions'] = corrected_positions
                    recovered_message = bits_to_ascii(decoded_bits)
                    result['recovered_message'] = recovered_message
                    result['valid'] = True
                else:
                    result['error'] = 'Hamming decoding failed'
            
            else:
                result['error'] = f'Unknown message type: {msg_type}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def update_stats(self, algorithm: str, reception_result: Dict, error_stats: Dict, processing_time: float):
        """Update global statistics"""
        self.stats['messages_sent'] += 1
        self.stats['total_bits_sent'] += error_stats['total_bits']
        self.stats['total_errors_injected'] += error_stats['error_bits']
        self.stats['transmission_times'].append(processing_time)
        
        if reception_result['valid']:
            self.stats['messages_received'] += 1
            if algorithm == 'crc':
                self.stats['crc_valid'] += 1
            elif reception_result['corrected_positions']:
                self.stats['hamming_corrected'] += 1
        else:
            if algorithm == 'crc':
                self.stats['crc_invalid'] += 1
            else:
                self.stats['hamming_errors'] += 1


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="Lab 2 - Error Detection & Correction Demo",
        page_icon="='",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize demo
    if 'demo' not in st.session_state:
        st.session_state.demo = LabDemo()
    
    demo = st.session_state.demo
    
    st.title("=' Lab 2 - Error Detection & Correction Demo")
    st.markdown("**Esquemas de detecci�n y correcci�n con CRC-32 y Hamming(7,4)**")
    
    # Sidebar controls
    st.sidebar.header("� Configuration")
    
    # Message input
    message = st.sidebar.text_input(
        "Input Message",
        value="Hello World!",
        help="ASCII text to transmit"
    )
    
    # Algorithm selection
    algorithm = st.sidebar.selectbox(
        "Algorithm",
        options=['crc', 'hamming'],
        format_func=lambda x: f"CRC-32 (Detection)" if x == 'crc' else "Hamming(7,4) (Correction)",
        help="Choose error detection or correction algorithm"
    )
    
    # BER control
    ber = st.sidebar.slider(
        "Bit Error Rate (BER)",
        min_value=0.0,
        max_value=0.1,
        value=0.01,
        step=0.001,
        format="%.3f",
        help="Probability of bit error during transmission"
    )
    
    # Controls
    col1, col2 = st.sidebar.columns(2)
    with col1:
        send_button = st.button("=� Send Message", type="primary")
    with col2:
        reset_button = st.button("= Reset Stats")
    
    if reset_button:
        demo.reset_stats()
        st.rerun()
    
    # Main content
    if send_button and message:
        with st.spinner("Processing message..."):
            result = demo.process_message(message, algorithm, ber)
        
        # Display results
        display_results(result)
    
    # Statistics dashboard
    display_statistics(demo.stats)


def display_results(result: Dict[str, Any]):
    """Display processing results"""
    st.header("=� Transmission Results")
    
    # Message info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Original Message", f'"{result["original_message"]}"')
    with col2:
        st.metric("Algorithm", result["algorithm"].upper())
    with col3:
        st.metric("Processing Time", f"{result['processing_time']:.3f}s")
    
    # Error injection results
    error_stats = result["error_stats"]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bits", error_stats["total_bits"])
    with col2:
        st.metric("Errors Injected", error_stats["error_bits"])
    with col3:
        st.metric("Error Rate", f"{error_stats['error_rate']:.3%}")
    with col4:
        success = result["reception_result"]["valid"]
        st.metric("Reception", " Success" if success else "L Failed")
    
    # Reception results
    st.subheader("= Reception Analysis")
    reception = result["reception_result"]
    
    if reception["valid"]:
        st.success(f"**Message recovered:** \"{reception['recovered_message']}\"")
        
        if reception["corrected_positions"]:
            st.info(f"**Hamming corrections:** {len(reception['corrected_positions'])} bits corrected at positions {reception['corrected_positions']}")
    else:
        st.error(f"**Reception failed:** {reception.get('error', 'Unknown error')}")
    
    # Bit visualization
    if st.checkbox("Show bit-level details"):
        display_bit_visualization(result)


def display_bit_visualization(result: Dict[str, Any]):
    """Display bit-level visualization"""
    st.subheader("= Bit-Level Analysis")

    original_bits = result["original_bits"]
    transmission_bits = result["transmission_bits"]
    noisy_bits = result["noisy_bits"]
    error_positions = result["error_positions"]
    
    # Create bit comparison
    bit_data = []
    for i in range(min(len(transmission_bits), 100)):  # Limit to first 100 bits for display
        bit_data.append({
            'Position': i,
            'Original': transmission_bits[i],
            'Received': noisy_bits[i],
            'Error': i in error_positions
        })
    
    df = pd.DataFrame(bit_data)
    
    if not df.empty:
        # Color-coded bit display
        fig = px.scatter(df, x='Position', y='Original', color='Error',
                        title="Bit Transmission (Red = Error)",
                        color_discrete_map={True: 'red', False: 'blue'})
        fig.add_scatter(x=df['Position'], y=df['Received'] + 0.1, 
                       mode='markers', name='Received',
                       marker=dict(symbol='triangle-up'))
        st.plotly_chart(fig, use_container_width=True)


def display_statistics(stats: Dict[str, Any]):
    """Display global statistics dashboard"""
    st.header("=� Session Statistics")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Messages Sent", stats["messages_sent"])
    with col2:
        success_rate = (stats["messages_received"] / max(stats["messages_sent"], 1)) * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col3:
        st.metric("Total Bits", stats["total_bits_sent"])
    with col4:
        error_rate = (stats["total_errors_injected"] / max(stats["total_bits_sent"], 1)) * 100
        st.metric("Error Rate", f"{error_rate:.2f}%")
    
    # Algorithm breakdown
    if stats["messages_sent"] > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("CRC Results")
            crc_total = stats["crc_valid"] + stats["crc_invalid"]
            if crc_total > 0:
                crc_success = (stats["crc_valid"] / crc_total) * 100
                st.metric("CRC Success Rate", f"{crc_success:.1f}%")
                st.metric("Valid Frames", stats["crc_valid"])
                st.metric("Invalid Frames", stats["crc_invalid"])
        
        with col2:
            st.subheader("Hamming Results")
            st.metric("Corrections Made", stats["hamming_corrected"])
            st.metric("Failed Decodings", stats["hamming_errors"])
        
        # Performance chart
        if len(stats["transmission_times"]) > 1:
            st.subheader("Processing Time Trend")
            time_df = pd.DataFrame({
                'Transmission': range(1, len(stats["transmission_times"]) + 1),
                'Time (s)': stats["transmission_times"]
            })
            fig = px.line(time_df, x='Transmission', y='Time (s)',
                         title="Processing Time per Transmission")
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()