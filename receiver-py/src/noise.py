"""
Noise Layer: Error injection with probability p (BER)
Simulates transmission errors by flipping bits
"""

import random
from typing import List


def inject_noise(bits: List[int], ber: float, seed: int = None) -> tuple[List[int], List[int]]:
    """
    Injects random bit errors with given Bit Error Rate (BER).
    
    Args:
        bits: Original bits to add noise to
        ber: Bit Error Rate (probability of error per bit, 0.0 to 1.0)
        seed: Random seed for reproducible results
        
    Returns:
        Tuple of (noisy_bits, error_positions)
    """
    if seed is not None:
        random.seed(seed)
    
    noisy_bits = bits.copy()
    error_positions = []
    
    for i in range(len(bits)):
        if random.random() < ber:
            noisy_bits[i] = 1 - noisy_bits[i]  # Flip bit
            error_positions.append(i)
    
    return noisy_bits, error_positions


def calculate_error_stats(original_bits: List[int], received_bits: List[int]) -> dict:
    """
    Calculates error statistics between original and received bits.
    
    Args:
        original_bits: Original transmitted bits
        received_bits: Received bits (potentially with errors)
        
    Returns:
        Dictionary with error statistics
    """
    if len(original_bits) != len(received_bits):
        raise ValueError("Bit sequences must have the same length")
    
    total_bits = len(original_bits)
    errors = sum(1 for orig, recv in zip(original_bits, received_bits) if orig != recv)
    
    return {
        'total_bits': total_bits,
        'error_bits': errors,
        'error_rate': errors / total_bits if total_bits > 0 else 0.0,
        'correct_bits': total_bits - errors
    }