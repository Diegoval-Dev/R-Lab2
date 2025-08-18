import binascii
from typing import List, Tuple, Optional


def bytes_to_bits(data: bytes) -> List[int]:
    """Convierte bytes a lista de bits (0 o 1)"""
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_bytes(bits: List[int]) -> bytes:
    """Convierte lista de bits a bytes, agregando padding si es necesario"""
    if not bits:
        return b''
    
    # Work with a copy to avoid mutating the input
    working_bits = bits.copy()
    
    # Padding si no es multiplo de 8
    while len(working_bits) % 8 != 0:
        working_bits.append(0)
    
    result = bytearray()
    for i in range(0, len(working_bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val |= working_bits[i + j] << (7 - j)
        result.append(byte_val)
    
    return bytes(result)


def verify_crc(frame_bytes: bytes) -> Tuple[bool, bytes]:
    """
    Verifica el CRC-32 de una trama y extrae el payload.
    
    Args:
        frame_bytes: Trama completa [Header(3)] + Payload + [CRC(4)]
        
    Returns:
        (is_valid, payload): tupla con validez del CRC y payload extraido
    """
    if len(frame_bytes) < 7:  # minimo: 3 header + 0 payload + 4 CRC
        return False, b''
    
    # Extraer componentes
    data_part = frame_bytes[:-4]  # Todo excepto los ultimos 4 bytes (CRC)
    received_crc_bytes = frame_bytes[-4:]  # Ultimos 4 bytes
    
    # Convertir CRC recibido de Big-Endian
    received_crc = int.from_bytes(received_crc_bytes, 'big')
    
    # Calcular CRC sobre header + payload
    calculated_crc = binascii.crc32(data_part) & 0xffffffff
    
    # Extraer payload (saltando header de 3 bytes)
    payload = data_part[3:]
    
    return received_crc == calculated_crc, payload


def hamming74_decode(code_bits: List[int]) -> Tuple[List[int], List[int]]:
    """
    Decodifica bits usando Hamming (7,4) con correccion de error unico.
    
    Args:
        code_bits: Lista de bits codificados (multiplo de 7)
        
    Returns:
        (data_bits, corrected_positions): datos decodificados y posiciones corregidas
    """
    if len(code_bits) % 7 != 0:
        raise ValueError("La longitud debe ser multiplo de 7")
    
    num_blocks = len(code_bits) // 7
    data_bits = []
    corrected_positions = []
    
    for block_idx in range(num_blocks):
        start = block_idx * 7
        block = code_bits[start:start + 7]
        
        # Estructura del bloque: [p2, p1, d3, p0, d2, d1, d0]
        p2, p1, d3, p0, d2, d1, d0 = block
        
        # Calcular sindrome
        s0 = p0 ^ d3 ^ d2 ^ d0  # sindrome para p0
        s1 = p1 ^ d3 ^ d1 ^ d0  # sindrome para p1  
        s2 = p2 ^ d2 ^ d1 ^ d0  # sindrome para p2
        
        syndrome = s2 * 4 + s1 * 2 + s0
        
        # Corregir error si existe
        if syndrome != 0:
            # Mapeo de sindrome a posicion en el bloque [p2, p1, d3, p0, d2, d1, d0]
            error_pos_map = {
                1: 3,  # p0
                2: 1,  # p1
                3: 2,  # d3
                4: 0,  # p2
                5: 4,  # d2
                6: 5,  # d1
                7: 6   # d0
            }
            
            if syndrome in error_pos_map:
                error_pos = error_pos_map[syndrome]
                block[error_pos] = 1 - block[error_pos]  # flip bit
                corrected_positions.append(start + error_pos)
                
                # Actualizar variables despues de correccion
                p2, p1, d3, p0, d2, d1, d0 = block
        
        # Extraer bits de datos: [d3, d2, d1, d0]
        data_bits.extend([d3, d2, d1, d0])
    
    return data_bits, corrected_positions


def parse_frame_header(frame_bytes: bytes) -> Tuple[int, int]:
    """
    Parsea el header de la trama.
    
    Args:
        frame_bytes: Trama completa
        
    Returns:
        (msg_type, payload_length): tipo de mensaje y longitud del payload
    """
    if len(frame_bytes) < 3:
        raise ValueError("Frame demasiado corto para contener header")
    
    msg_type = frame_bytes[0]
    payload_length = int.from_bytes(frame_bytes[1:3], 'big')
    
    return msg_type, payload_length