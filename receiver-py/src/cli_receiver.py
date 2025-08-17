#!/usr/bin/env python3

import argparse
import sys
from typing import List
from algorithms import verify_crc, hamming74_decode, bytes_to_bits, bits_to_bytes


def parse_hex_input(hex_str: str) -> bytes:
    """Convierte string hexadecimal a bytes"""
    try:
        # Remover espacios y prefijos opcionales
        hex_str = hex_str.replace(" ", "").replace("0x", "")
        return bytes.fromhex(hex_str)
    except ValueError as e:
        raise ValueError(f"Formato hexadecimal inválido: {e}")


def parse_bits_input(bits_str: str) -> List[int]:
    """Convierte string de bits a lista de enteros"""
    bits_str = bits_str.replace(" ", "")
    if not all(c in '01' for c in bits_str):
        raise ValueError("Solo se permiten caracteres '0' y '1'")
    return [int(c) for c in bits_str]


def format_bits_output(bits: List[int]) -> str:
    """Convierte lista de bits a string"""
    return ''.join(str(b) for b in bits)


def main():
    parser = argparse.ArgumentParser(description='Receptor manual para algoritmos de detección y corrección')
    parser.add_argument('--algo', choices=['crc', 'hamming'], required=True,
                       help='Algoritmo a usar (crc para detección, hamming para corrección)')
    parser.add_argument('--input', required=True,
                       help='Datos de entrada (hex para CRC, bits para Hamming)')
    
    args = parser.parse_args()

    try:
        if args.algo == 'crc':
            # Modo detección CRC
            frame_bytes = parse_hex_input(args.input)
            is_valid, payload = verify_crc(frame_bytes)
            
            if is_valid:
                # Convertir payload a texto si es posible
                try:
                    message = payload.decode('utf-8')
                    print(f"MENSAJE VÁLIDO: {message}")
                except UnicodeDecodeError:
                    # Si no es texto válido, mostrar en hex
                    print(f"MENSAJE VÁLIDO (hex): {payload.hex()}")
            else:
                print("DESCARTAR - CRC inválido")
                
        elif args.algo == 'hamming':
            # Modo corrección Hamming
            code_bits = parse_bits_input(args.input)
            
            try:
                data_bits, corrected_positions = hamming74_decode(code_bits)
                
                if corrected_positions:
                    print(f"ERROR CORREGIDO en posición(es): {corrected_positions}")
                    
                # Convertir bits de datos a mensaje
                data_bytes = bits_to_bytes(data_bits)
                
                # Intentar decodificar como texto
                try:
                    message = data_bytes.decode('utf-8').rstrip('\x00')  # remover padding nulls
                    print(f"MENSAJE CORREGIDO: {message}")
                except UnicodeDecodeError:
                    # Si no es texto válido, mostrar bits
                    print(f"DATOS CORREGIDOS (bits): {format_bits_output(data_bits)}")
                    print(f"DATOS CORREGIDOS (hex): {data_bytes.hex()}")
                    
            except ValueError as e:
                print(f"DESCARTAR - Error en decodificación: {e}")
                
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR INESPERADO: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()