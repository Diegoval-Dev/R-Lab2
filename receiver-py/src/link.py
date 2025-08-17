"""
Link Layer: Error detection and correction algorithms
Handles CRC-32 and Hamming(7,4) processing
"""

import binascii
from typing import List, Tuple
from algorithms import hamming74_decode, bytes_to_bits, bits_to_bytes


class LinkLayer:
    """Link layer for error detection and correction"""
    
    @staticmethod
    def apply_crc(data: bytes) -> bytes:
        """
        Applies CRC-32 to data and returns data + CRC.
        
        Args:
            data: Input data bytes
            
        Returns:
            Data with CRC-32 appended
        """
        crc = binascii.crc32(data) & 0xffffffff
        crc_bytes = crc.to_bytes(4, 'big')
        return data + crc_bytes
    
    @staticmethod
    def verify_crc(data_with_crc: bytes) -> Tuple[bool, bytes]:
        """
        Verifies CRC-32 and extracts original data.
        
        Args:
            data_with_crc: Data with CRC-32 appended
            
        Returns:
            Tuple of (is_valid, original_data)
        """
        if len(data_with_crc) < 4:
            return False, b''
        
        data = data_with_crc[:-4]
        received_crc_bytes = data_with_crc[-4:]
        received_crc = int.from_bytes(received_crc_bytes, 'big')
        
        calculated_crc = binascii.crc32(data) & 0xffffffff
        
        return received_crc == calculated_crc, data
    
    @staticmethod
    def apply_hamming(data_bits: List[int]) -> List[int]:
        """
        Applies Hamming(7,4) encoding to data bits.
        Uses the Go implementation logic.
        
        Args:
            data_bits: Input data bits
            
        Returns:
            Hamming encoded bits
        """
        # Pad to multiple of 4 bits
        padded_bits = data_bits.copy()
        while len(padded_bits) % 4 != 0:
            padded_bits.append(0)
        
        encoded_bits = []
        
        for i in range(0, len(padded_bits), 4):
            # Extract 4 data bits: [d3, d2, d1, d0]
            d3, d2, d1, d0 = padded_bits[i:i+4]
            
            # Calculate parity bits
            p0 = d3 ^ d2 ^ d0
            p1 = d3 ^ d1 ^ d0
            p2 = d2 ^ d1 ^ d0
            
            # Arrange as [p2, p1, d3, p0, d2, d1, d0]
            block = [p2, p1, d3, p0, d2, d1, d0]
            encoded_bits.extend(block)
        
        return encoded_bits
    
    @staticmethod
    def verify_hamming(encoded_bits: List[int]) -> Tuple[List[int], List[int], bool]:
        """
        Verifies and corrects Hamming(7,4) encoded bits.
        
        Args:
            encoded_bits: Hamming encoded bits
            
        Returns:
            Tuple of (decoded_bits, corrected_positions, success)
        """
        try:
            decoded_bits, corrected_positions = hamming74_decode(encoded_bits)
            return decoded_bits, corrected_positions, True
        except Exception:
            return [], [], False
    
    @staticmethod
    def build_frame(payload: bytes, msg_type: int = 0x01) -> bytes:
        """
        Builds a frame with header + payload + CRC.
        
        Args:
            payload: Payload data
            msg_type: Message type (0x01 = RAW+CRC, 0x02 = HAMMING+CRC)
            
        Returns:
            Complete frame bytes
        """
        # Build header: type (1 byte) + length (2 bytes, big-endian)
        header = bytes([msg_type]) + len(payload).to_bytes(2, 'big')
        
        # Combine header + payload
        data = header + payload
        
        # Add CRC
        frame = LinkLayer.apply_crc(data)
        
        return frame
    
    @staticmethod
    def parse_frame(frame: bytes) -> Tuple[bool, int, bytes]:
        """
        Parses a received frame and validates CRC.
        
        Args:
            frame: Complete frame bytes
            
        Returns:
            Tuple of (is_valid, msg_type, payload)
        """
        if len(frame) < 7:  # Minimum: 3 header + 0 payload + 4 CRC
            return False, 0, b''
        
        # Verify CRC and extract data part
        is_valid, data_part = LinkLayer.verify_crc(frame)
        if not is_valid:
            return False, 0, b''
        
        # Parse header
        msg_type = data_part[0]
        payload_length = int.from_bytes(data_part[1:3], 'big')
        payload = data_part[3:]
        
        # Verify payload length matches header
        if len(payload) != payload_length:
            return False, msg_type, payload
        
        return True, msg_type, payload