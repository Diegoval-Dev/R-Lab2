import pytest
import binascii
from src.algorithms import (
    verify_crc, hamming74_decode, bytes_to_bits, bits_to_bytes,
    parse_frame_header
)


class TestUtilityFunctions:
    """Pruebas para funciones utilitarias de conversion"""
    
    def test_bytes_to_bits(self):
        # Caso simple: un byte
        assert bytes_to_bits(b'\x00') == [0, 0, 0, 0, 0, 0, 0, 0]
        assert bytes_to_bits(b'\xFF') == [1, 1, 1, 1, 1, 1, 1, 1]
        assert bytes_to_bits(b'\x0F') == [0, 0, 0, 0, 1, 1, 1, 1]
        
        # Caso multiples bytes
        assert bytes_to_bits(b'\x00\xFF') == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
    
    def test_bits_to_bytes(self):
        # Caso exacto multiplo de 8
        assert bits_to_bytes([0, 0, 0, 0, 0, 0, 0, 0]) == b'\x00'
        assert bits_to_bytes([1, 1, 1, 1, 1, 1, 1, 1]) == b'\xFF'
        
        # Caso con padding
        assert bits_to_bytes([1, 1, 1, 1]) == b'\xF0'  # Se completa con ceros
        
        # Caso vacio
        assert bits_to_bytes([]) == b''


class TestCRCVerification:
    """Pruebas para verificacion CRC-32"""
    
    def test_verify_crc_valid_frame(self):
        # Crear frame valido usando algoritmo conocido
        # Header: [0x01, 0x00, 0x05] (tipo 1, longitud 5)
        # Payload: "Hello"
        header = b'\x01\x00\x05'
        payload = b'Hello'
        data_part = header + payload
        
        # Calcular CRC correcto
        crc = binascii.crc32(data_part) & 0xffffffff
        crc_bytes = crc.to_bytes(4, 'big')
        
        frame = data_part + crc_bytes
        
        is_valid, extracted_payload = verify_crc(frame)
        assert is_valid == True
        assert extracted_payload == payload
    
    def test_verify_crc_invalid_frame(self):
        # Frame con CRC incorrecto
        header = b'\x01\x00\x05'
        payload = b'Hello'
        bad_crc = b'\x00\x00\x00\x00'  # CRC obviamente incorrecto
        
        frame = header + payload + bad_crc
        
        is_valid, extracted_payload = verify_crc(frame)
        assert is_valid == False
        assert extracted_payload == payload  # Payload se extrae aunque CRC sea malo
    
    def test_verify_crc_too_short(self):
        # Frame demasiado corto
        short_frame = b'\x01\x00'  # Solo 2 bytes
        
        is_valid, extracted_payload = verify_crc(short_frame)
        assert is_valid == False
        assert extracted_payload == b''


class TestHammingDecoding:
    """Pruebas para decodificacion Hamming (7,4)"""
    
    def test_hamming_decode_no_errors(self):
        # Caso conocido sin errores: datos [1,0,1,1] -> codigo [0,1,1,0,0,1,1]
        # Estructura: [p2=0, p1=1, d3=1, p0=0, d2=0, d1=1, d0=1]
        code_bits = [0, 1, 1, 0, 0, 1, 1]
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        
        assert data_bits == [1, 0, 1, 1]  # [d3, d2, d1, d0]
        assert corrected_positions == []  # No hubo correcciones
    
    def test_hamming_decode_single_error_data_bit(self):
        # Mismo caso pero con error en d3 (posicion 2): cambiar 1 -> 0
        # Codigo original: [0,1,1,0,0,1,1]
        # Codigo con error: [0,1,0,0,0,1,1] (d3 cambiado de 1 a 0)
        code_bits = [0, 1, 0, 0, 0, 1, 1]
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        
        # Debe corregir el error y devolver datos originales
        assert data_bits == [1, 0, 1, 1]  # [d3, d2, d1, d0] corregidos
        assert len(corrected_positions) == 1
        assert 2 in corrected_positions  # posicion 2 fue corregida
    
    def test_hamming_decode_single_error_parity_bit(self):
        # Error en bit de paridad p1 (posicion 1): cambiar 1 -> 0
        # Codigo original: [0,1,1,0,0,1,1]
        # Codigo con error: [0,0,1,0,0,1,1]
        code_bits = [0, 0, 1, 0, 0, 1, 1]
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        
        # Los datos deben ser correctos (error solo en paridad)
        assert data_bits == [1, 0, 1, 1]  # [d3, d2, d1, d0]
        assert len(corrected_positions) == 1
        assert 1 in corrected_positions  # posicion 1 fue corregida
    
    def test_hamming_decode_multiple_blocks(self):
        # Dos bloques: [1,0,1,1] y [0,1,0,0]
        # Primer bloque codificado: [0,1,1,0,0,1,1]
        # Segundo bloque para [0,1,0,0]: calcular paridades
        # p0 = 0⊕1⊕0 = 1, p1 = 0⊕0⊕0 = 0, p2 = 1⊕0⊕0 = 1
        # Segundo bloque: [1,0,0,1,1,0,0]
        
        code_bits = [0, 1, 1, 0, 0, 1, 1,  # primer bloque
                     1, 0, 0, 1, 1, 0, 0]  # segundo bloque
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        
        assert data_bits == [1, 0, 1, 1, 0, 1, 0, 0]  # 8 bits de datos
        assert corrected_positions == []  # Sin errores
    
    def test_hamming_decode_invalid_length(self):
        # Longitud no multiplo de 7
        code_bits = [0, 1, 1, 1, 0, 1]  # 6 bits
        
        with pytest.raises(ValueError, match="multiplo de 7"):
            hamming74_decode(code_bits)


class TestFrameHeader:
    """Pruebas para parsing de header"""
    
    def test_parse_frame_header_valid(self):
        frame = b'\x01\x00\x05Hello\x12\x34\x56\x78'
        msg_type, payload_length = parse_frame_header(frame)
        
        assert msg_type == 0x01
        assert payload_length == 5
    
    def test_parse_frame_header_large_payload(self):
        frame = b'\x02\x01\x00' + b'x' * 256  # 256 bytes de payload
        msg_type, payload_length = parse_frame_header(frame)
        
        assert msg_type == 0x02
        assert payload_length == 256
    
    def test_parse_frame_header_too_short(self):
        frame = b'\x01\x00'  # Solo 2 bytes
        
        with pytest.raises(ValueError, match="demasiado corto"):
            parse_frame_header(frame)


class TestIntegrationScenarios:
    """Pruebas de escenarios integrados como se especifica en la consigna"""
    
    def test_scenario_crc_no_errors(self):
        """Escenario CRC sin errores: debe aceptar y mostrar mensaje original"""
        # Crear frame valido con mensaje conocido
        header = b'\x01\x00\x04'
        payload = b'test'
        data_part = header + payload
        
        crc = binascii.crc32(data_part) & 0xffffffff
        crc_bytes = crc.to_bytes(4, 'big')
        frame = data_part + crc_bytes
        
        is_valid, extracted_payload = verify_crc(frame)
        assert is_valid == True
        assert extracted_payload == b'test'
    
    def test_scenario_crc_one_error(self):
        """Escenario CRC con 1 error: debe detectar y descartar"""
        # Crear frame valido y luego corromper 1 bit
        header = b'\x01\x00\x04'
        payload = b'test'
        data_part = header + payload
        
        crc = binascii.crc32(data_part) & 0xffffffff
        crc_bytes = crc.to_bytes(4, 'big')
        frame = bytearray(data_part + crc_bytes)
        
        # Corromper primer bit del payload
        frame[3] ^= 0x80  # flip primer bit de 't'
        
        is_valid, extracted_payload = verify_crc(bytes(frame))
        assert is_valid == False  # Debe detectar error
    
    def test_scenario_hamming_no_errors(self):
        """Escenario Hamming sin errores: debe aceptar y mostrar mensaje original"""
        # Codigo valido sin errores
        code_bits = [0, 1, 1, 0, 0, 1, 1]  # datos [1,0,1,1]
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        assert data_bits == [1, 0, 1, 1]
        assert corrected_positions == []
    
    def test_scenario_hamming_one_error(self):
        """Escenario Hamming con 1 error: debe corregir y reportar posicion"""
        # Codigo con error en posicion de datos
        code_bits = [0, 1, 0, 0, 0, 1, 1]  # error en d3 (pos 2)
        
        data_bits, corrected_positions = hamming74_decode(code_bits)
        assert data_bits == [1, 0, 1, 1]  # Datos corregidos
        assert len(corrected_positions) == 1
        assert 2 in corrected_positions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])