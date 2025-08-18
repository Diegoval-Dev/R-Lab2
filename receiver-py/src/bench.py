import time
import csv
import argparse
import random
from typing import List, Dict, Any
from pathlib import Path

from presentation import ascii_to_bits, bits_to_ascii
from link import LinkLayer
from noise import inject_noise, calculate_error_stats
from transport import MockTransport
from algorithms import bytes_to_bits, bits_to_bytes


class BenchmarkRunner:
    """Automated benchmark for error detection/correction algorithms"""
    
    def __init__(self):
        self.link = LinkLayer()
        self.transport = MockTransport()
        self.results = []
    
    def generate_test_message(self, length: int) -> str:
        """Generate random ASCII test message of specified length"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 !@#$%^&*()_+-=[]{}|;:,.<>?"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def run_single_test(self, message: str, algorithm: str, ber: float, test_id: int) -> Dict[str, Any]:
        """Run a single transmission test"""
        start_time = time.time()
        
        # Convert message to bits
        original_bits = ascii_to_bits(message)
        original_bytes = len(message)
        
        # Apply algorithm
        if algorithm == 'crc':
            payload_bytes = bits_to_bytes(original_bits)
            frame = self.link.build_frame(payload_bytes, msg_type=0x01)
            transmission_bits = bytes_to_bits(frame)
        else:  # hamming
            encoded_bits = self.link.apply_hamming(original_bits)
            payload_bytes = bits_to_bytes(encoded_bits)
            # Pass both bit lengths to preserve message integrity
            frame = self.link.build_frame(payload_bytes, msg_type=0x02, 
                                        original_bits_len=len(original_bits), 
                                        encoded_bits_len=len(encoded_bits))
            transmission_bits = bytes_to_bits(frame)
        
        # Calculate overhead
        total_bits = len(transmission_bits)
        data_bits = len(original_bits)
        overhead_bits = total_bits - data_bits
        overhead_ratio = overhead_bits / data_bits if data_bits > 0 else 0
        
        # Inject noise
        noisy_bits, error_positions = inject_noise(transmission_bits, ber, seed=test_id)
        
        # Simulate transmission
        noisy_frame = bits_to_bytes(noisy_bits)
        
        # Reception processing
        reception_start = time.time()
        reception_result = self.process_reception(noisy_frame)
        reception_time = time.time() - reception_start
        
        total_time = time.time() - start_time
        
        # Calculate error statistics
        error_stats = calculate_error_stats(transmission_bits, noisy_bits)
        
        # Determine outcome based on algorithm purpose
        successful = reception_result['valid']
        corrected = len(reception_result.get('corrected_positions', []))
        errors_injected = error_stats['error_bits']
        
        # CRC: Success = detection of errors (valid=False when errors present)
        # Hamming: Success = correction of errors (valid=True after correction)
        if algorithm == 'crc':
            crc_detected_correctly = (errors_injected > 0 and not successful) or (errors_injected == 0 and successful)
        else:
            crc_detected_correctly = False  # N/A for Hamming
            
        return {
            'test_id': test_id,
            'algorithm': algorithm,
            'message_length': len(message),
            'original_bytes': original_bytes,
            'original_bits': data_bits,
            'total_bits': total_bits,
            'overhead_bits': overhead_bits,
            'overhead_ratio': overhead_ratio,
            'ber_target': ber,
            'errors_injected': errors_injected,
            'actual_ber': error_stats['error_rate'],
            'errors_corrected': corrected,
            'successful': successful,
            'recovered_correctly': successful and (reception_result['recovered_message'] == message),
            'crc_detected_correctly': crc_detected_correctly,
            'total_time_ms': total_time * 1000,
            'reception_time_ms': reception_time * 1000,
            'message_original': message,
            'message_recovered': reception_result.get('recovered_message', ''),
            'error_type': reception_result.get('error', ''),
        }
    
    def process_reception(self, frame_bytes: bytes) -> Dict[str, Any]:
        """Process received frame (similar to streamlit app)"""
        result = {
            'valid': False,
            'recovered_message': '',
            'corrected_positions': [],
            'error': None
        }
        
        try:
            # First, try to parse frame header (may fail CRC initially)
            try:
                is_valid, msg_type, payload, original_bits_len, encoded_bits_len = self.link.parse_frame(frame_bytes)
            except:
                # If parsing completely fails, try basic header parsing
                if len(frame_bytes) < 7:
                    result['error'] = 'Frame too short'
                    return result
                msg_type = frame_bytes[0]
                is_valid = False
                payload = frame_bytes[3:-4]  # Basic payload extraction
                original_bits_len = 0
                encoded_bits_len = 0
            
            if msg_type == 0x01:  # CRC - must be valid
                if not is_valid:
                    result['error'] = 'CRC validation failed'
                    return result
                
                payload_bits = bytes_to_bits(payload)
                recovered_message = bits_to_ascii(payload_bits)
                result['recovered_message'] = recovered_message
                result['valid'] = True
                
            elif msg_type == 0x02:  # Hamming - try correction even if CRC failed
                if is_valid:
                    # CRC already valid, just decode
                    payload_bits = bytes_to_bits(payload)
                    payload_bits = payload_bits[:encoded_bits_len]
                    decoded_bits, corrected_positions, success = self.link.verify_hamming(payload_bits)
                    
                    if success:
                        result['corrected_positions'] = corrected_positions
                        recovered_message = bits_to_ascii(decoded_bits, original_bits_len)
                        result['recovered_message'] = recovered_message
                        result['valid'] = True
                    else:
                        result['error'] = 'Hamming decoding failed'
                else:
                    # CRC failed, try Hamming correction and re-verify CRC
                    result['error'] = 'CRC validation failed - Hamming correction not implemented'
                    # TODO: Implement full frame Hamming correction with CRC re-verification
            else:
                result['error'] = f'Unknown message type: {msg_type}'
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def run_benchmark(self, 
                     num_tests: int = 10000,
                     message_lengths: List[int] = [5, 10, 20, 50],
                     ber_values: List[float] = [0.0, 0.0001, 0.0005, 0.001, 0.002, 0.005],
                     algorithms: List[str] = ['crc', 'hamming']) -> List[Dict[str, Any]]:
        """
        Run comprehensive benchmark
        
        Args:
            num_tests: Total number of tests to run
            message_lengths: List of message lengths to test
            ber_values: List of BER values to test
            algorithms: List of algorithms to test
            
        Returns:
            List of test results
        """
        print(f"Starting benchmark with {num_tests} tests...")
        print(f"Message lengths: {message_lengths}")
        print(f"BER values: {ber_values}")
        print(f"Algorithms: {algorithms}")
        
        test_combinations = []
        for algorithm in algorithms:
            for length in message_lengths:
                for ber in ber_values:
                    # More tests for key scenarios
                    if ber == 0.0:  # Perfect conditions
                        weight = 3
                    elif ber <= 0.001:  # Low error rates
                        weight = 2
                    else:  # Higher error rates
                        weight = 1
                    test_combinations.append((algorithm, length, ber, weight))
        
        total_weight = sum(combo[3] for combo in test_combinations)
        
        results = []
        test_id = 0
        
        for algorithm, length, ber, weight in test_combinations:
            combination_tests = max(1, (num_tests * weight) // total_weight)
            
            print(f"Running {combination_tests} tests for {algorithm.upper()}, length={length}, BER={ber}")
            
            for j in range(combination_tests):
                message = self.generate_test_message(length)
                result = self.run_single_test(message, algorithm, ber, test_id)
                results.append(result)
                test_id += 1
                
                if (test_id % 1000) == 0:
                    print(f"Completed {test_id}/{num_tests} tests ({test_id/num_tests*100:.1f}%)")
        
        print(f"Benchmark completed! Total tests: {len(results)}")
        return results
    
    def save_results_csv(self, results: List[Dict[str, Any]], filename: str = "benchmark_results.csv"):
        """Save results to CSV file"""
        if not results:
            print("No results to save!")
            return
        
        filepath = Path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = results[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        print(f"Results saved to {filepath} ({len(results)} rows)")
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print benchmark summary statistics"""
        if not results:
            print("No results to summarize!")
            return
        
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        
        total_tests = len(results)
        successful_tests = sum(1 for r in results if r['successful'])
        correct_recoveries = sum(1 for r in results if r['recovered_correctly'])
        
        print(f"Total tests: {total_tests}")
        print(f"Successful receptions: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        print(f"Correct message recovery: {correct_recoveries} ({correct_recoveries/total_tests*100:.1f}%)")
        
        # Algorithm breakdown
        for algorithm in ['crc', 'hamming']:
            algo_results = [r for r in results if r['algorithm'] == algorithm]
            if algo_results:
                successful = sum(1 for r in algo_results if r['successful'])
                corrected = sum(1 for r in algo_results if r['recovered_correctly'])
                avg_overhead = sum(r['overhead_ratio'] for r in algo_results) / len(algo_results)
                avg_time = sum(r['total_time_ms'] for r in algo_results) / len(algo_results)
                
                print(f"\n{algorithm.upper()} Results:")
                print(f"  Tests: {len(algo_results)}")
                print(f"  Success rate: {successful/len(algo_results)*100:.1f}%")
                print(f"  Correct recovery: {corrected/len(algo_results)*100:.1f}%")
                print(f"  Average overhead: {avg_overhead:.2f}")
                print(f"  Average time: {avg_time:.2f}ms")
                
                if algorithm == 'hamming':
                    total_corrections = sum(r['errors_corrected'] for r in algo_results)
                    print(f"  Total corrections made: {total_corrections}")


def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(description='Run benchmark for Lab 2 algorithms')
    parser.add_argument('--tests', type=int, default=10000, help='Number of tests to run')
    parser.add_argument('--output', type=str, default='benchmark_results.csv', help='Output CSV filename')
    parser.add_argument('--lengths', nargs='+', type=int, default=[5, 10, 20, 50], 
                       help='Message lengths to test')
    parser.add_argument('--ber', nargs='+', type=float, default=[0.0, 0.0001, 0.0005, 0.001, 0.002, 0.005],
                       help='BER values to test')
    parser.add_argument('--algorithms', nargs='+', choices=['crc', 'hamming'], 
                       default=['crc', 'hamming'], help='Algorithms to test')
    
    args = parser.parse_args()
    
    # Set random seed for reproducible results
    random.seed(42)
    
    benchmark = BenchmarkRunner()
    
    # Run benchmark
    results = benchmark.run_benchmark(
        num_tests=args.tests,
        message_lengths=args.lengths,
        ber_values=args.ber,
        algorithms=args.algorithms
    )
    
    # Save results
    benchmark.save_results_csv(results, args.output)
    
    # Print summary
    benchmark.print_summary(results)


if __name__ == "__main__":
    main()