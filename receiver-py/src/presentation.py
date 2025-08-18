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


def bits_to_ascii(bits: List[int], original_length: int = None) -> str:
    """
    Converts binary bits back to ASCII text.
    
    Args:
        bits: List of bits (0 or 1)
        original_length: Original bit length before padding (optional)
        
    Returns:
        ASCII string representation
    """
    # If original length specified, truncate to that length
    if original_length is not None:
        bits = bits[:original_length]
    
    # Pad only if necessary for byte conversion
    working_bits = bits[:]
    if len(working_bits) % 8 != 0:
        working_bits = working_bits + [0] * (8 - len(working_bits) % 8)
    
    text = ""
    for i in range(0, len(working_bits), 8):
        byte_bits = working_bits[i:i+8]
        ascii_val = 0
        for j, bit in enumerate(byte_bits):
            ascii_val |= bit << (7 - j)
        
        # Only add printable ASCII characters
        if 32 <= ascii_val <= 126:
            text += chr(ascii_val)
        else:
            text += '?'  # Replace non-printable with ?
    
    return text