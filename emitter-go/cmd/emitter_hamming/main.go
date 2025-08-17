package main

import (
	"flag"
	"fmt"
	"os"
	"strconv"

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

	// Aplicar codificación Hamming (7,4)
	encodedBits, err := frame.Hamming74Encode(bitSlice)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error en codificación Hamming: %v\n", err)
		os.Exit(1)
	}

	// Convertir resultado a string para mostrar
	encodedBitsStr := ""
	for _, bit := range encodedBits {
		encodedBitsStr += fmt.Sprintf("%d", bit)
	}

	fmt.Printf("Bits de entrada: %s (longitud: %d)\n", bits, len(bits))
	fmt.Printf("Bits codificados: %s (longitud: %d)\n", encodedBitsStr, len(encodedBits))

	// Mostrar desglose por bloques
	fmt.Printf("\nDesglose por bloques de 7 bits:\n")
	numBlocks := len(encodedBits) / 7
	for i := 0; i < numBlocks; i++ {
		start := i * 7
		block := encodedBits[start : start+7]
		blockStr := ""
		for _, bit := range block {
			blockStr += fmt.Sprintf("%d", bit)
		}

		// Mostrar estructura del bloque: [p2, p1, d3, p0, d2, d1, d0]
		fmt.Printf("  Bloque %d: %s [p2=%d, p1=%d, d3=%d, p0=%d, d2=%d, d1=%d, d0=%d]\n",
			i+1, blockStr, block[0], block[1], block[2], block[3], block[4], block[5], block[6])
		
		// Mostrar datos originales del bloque
		originalData := fmt.Sprintf("%d%d%d%d", block[2], block[4], block[5], block[6])
		fmt.Printf("    Datos orig.: %s\n", originalData)
	}

	// Mostrar información de padding si aplica
	originalPadded := (len(bits) + 3) / 4 * 4  // redondear hacia arriba a múltiplo de 4
	if originalPadded > len(bits) {
		paddingBits := originalPadded - len(bits)
		fmt.Printf("\nPadding aplicado: %d bits (de %d a %d bits)\n", paddingBits, len(bits), originalPadded)
	}
}