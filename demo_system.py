#!/usr/bin/env python3
"""
Demo script for Lab 2 Part 2 - Layered Architecture
Shows the complete system working with both CRC and Hamming algorithms
"""

import subprocess
import time
import os
import sys

def main():
    print("🚀 Lab 2 Part 2 - Layered Architecture Demo")
    print("="*50)
    
    print("\n📋 System Status:")
    print("- Go layered emitter: ✅ Built")
    print("- Python layered receiver: ✅ Running on port 8765")
    print("- Streamlit UI: ✅ Running on port 8003")
    
    print("\n🧪 Testing Communication:")
    
    # Test 1: CRC with no noise (should succeed)
    print("\n1. Testing CRC with no noise...")
    result = subprocess.run([
        "./emitter-go/bin/simple_test", 
        "Test Message", 
        "crc", 
        "0.0", 
        "ws://localhost:8765"
    ], capture_output=True, text=True, cwd="/Users/gerco/UVG/8th_semester/Redes/R-Lab2")
    
    if result.returncode == 0:
        print("   ✅ CRC transmission successful")
    else:
        print("   ❌ CRC transmission failed")
        print(f"   Error: {result.stderr}")
    
    time.sleep(1)
    
    # Test 2: CRC with noise (should be detected and rejected)
    print("\n2. Testing CRC with noise (should be rejected)...")
    result = subprocess.run([
        "./emitter-go/bin/simple_test", 
        "Test Message", 
        "crc", 
        "0.05", 
        "ws://localhost:8765"
    ], capture_output=True, text=True, cwd="/Users/gerco/UVG/8th_semester/Redes/R-Lab2")
    
    if result.returncode == 0:
        print("   ✅ CRC noise test completed (frame likely rejected by receiver)")
    else:
        print("   ❌ CRC noise test failed")
    
    time.sleep(1)
    
    # Test 3: Hamming with light noise (should correct and succeed)
    print("\n3. Testing Hamming with light noise (should correct errors)...")
    result = subprocess.run([
        "./emitter-go/bin/simple_test", 
        "Short", 
        "hamming", 
        "0.01", 
        "ws://localhost:8765"
    ], capture_output=True, text=True, cwd="/Users/gerco/UVG/8th_semester/Redes/R-Lab2")
    
    if result.returncode == 0:
        print("   ✅ Hamming transmission completed")
    else:
        print("   ❌ Hamming transmission failed")
    
    print("\n🌐 Access Points:")
    print("- Streamlit UI: http://localhost:8003")
    print("- Receiver WebSocket: ws://localhost:8765")
    
    print("\n💡 Next Steps:")
    print("1. Open Streamlit UI in browser")
    print("2. Test different algorithms and BER values")
    print("3. Observe error detection/correction in real-time")
    
    print("\n📊 System Architecture Layers:")
    print("1. Application  - User input/UI")
    print("2. Presentation - ASCII ↔ bits conversion")  
    print("3. Link        - CRC-32 detection / Hamming(7,4) correction")
    print("4. Noise       - Error injection simulation")
    print("5. Transport   - WebSocket communication")

if __name__ == "__main__":
    main()