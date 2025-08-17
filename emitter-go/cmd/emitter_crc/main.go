package main

import (
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/gerco/r-lab2/pkg/frame"
)

func main() {
	var bits string
	flag.StringVar(&bits, "bits", "", "Cadena binaria (ej: '110101')")
	flag.Parse()

	if bits == "" {
		fmt.Fprintf(os.Stderr, "Uso: %s --bits <cadena_binaria>\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Ejemplo: %s --bits 110101\n", os.Args[0])
		os.Exit(1)
	}

	// Validar que solo contiene 0s y 1s
	for i, r := range bits {
		if r != '0' && r != '1' {
			fmt.Fprintf(os.Stderr, "Error: carácter inválido '%c' en posición %d\n", r, i)
			os.Exit(1)
		}
	}

	// Convertir string de bits a []byte de bits
	bitSlice := make([]byte, len(bits))
	for i, r := range bits {
		bit, _ := strconv.Atoi(string(r))
		bitSlice[i] = byte(bit)
	}

	// Convertir bits a bytes
	payload := frame.BitsToBytes(bitSlice)

	// Construir frame con CRC
	frameBytes, err := frame.BuildFrame(payload)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error construyendo frame: %v\n", err)
		os.Exit(1)
	}

	// Mostrar resultado en hexadecimal
	fmt.Printf("Bits de entrada: %s\n", bits)
	fmt.Printf("Payload (hex): %s\n", hex.EncodeToString(payload))
	fmt.Printf("Frame completo (hex): %s\n", hex.EncodeToString(frameBytes))

	// También mostrar en bits para verificación manual
	frameBits := frame.BytesToBits(frameBytes)
	frameBitsStr := ""
	for _, bit := range frameBits {
		frameBitsStr += fmt.Sprintf("%d", bit)
	}
	fmt.Printf("Frame completo (bits): %s\n", frameBitsStr)

	// Desglosar componentes del frame
	if len(frameBytes) >= 7 {
		header := frameBytes[:3]
		payload = frameBytes[3 : len(frameBytes)-4]
		crc := frameBytes[len(frameBytes)-4:]

		fmt.Printf("\nDesglose del frame:\n")
		fmt.Printf("  Header (hex): %s\n", hex.EncodeToString(header))
		fmt.Printf("  Payload (hex): %s\n", hex.EncodeToString(payload))
		fmt.Printf("  CRC-32 (hex): %s\n", hex.EncodeToString(crc))
	}
}