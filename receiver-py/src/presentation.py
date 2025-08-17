"""
Presentation Layer: ASCII ↔ Binary conversion
Handles text to bits conversion for transmission
"""

from typing import List


def ascii_to_bits(text: str) -> List[int]:
    """
    Converts ASCII text to binary bits.
    
    Args:
        text: ASCII string to convert
        
    Returns:
        List of bits (0 or 1) representing the text
    """
    bits = []
    for char in text:
        # Get ASCII value and convert to 8-bit binary
        ascii_val = ord(char)
        for i in range(8):
            bits.append((ascii_val >> (7 - i)) & 1)
    return bits


def bits_to_ascii(bits: List[int]) -> str:
    """
    Converts binary bits back to ASCII text.
    
    Args:
        bits: List of bits (0 or 1)
        
    Returns:
        ASCII string representation
    """
    if len(bits) % 8 != 0:
        # Pad with zeros if not multiple of 8
        bits = bits + [0] * (8 - len(bits) % 8)
    
    text = ""
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        ascii_val = 0
        for j, bit in enumerate(byte_bits):
            ascii_val |= bit << (7 - j)
        
        # Only add printable ASCII characters
        if 32 <= ascii_val <= 126:
            text += chr(ascii_val)
        else:
            text += '?'  # Replace non-printable with ?
    
    return text