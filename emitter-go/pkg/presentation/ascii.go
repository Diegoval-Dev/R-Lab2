package presentation

import (
	"fmt"
	"unicode/utf8"
)

// PresentationLayer maneja la codificación/decodificación de mensajes
type PresentationLayer struct{}

// NewPresentationLayer crea una nueva instancia
func NewPresentationLayer() *PresentationLayer {
	return &PresentationLayer{}
}

// CodificarMensaje convierte texto ASCII a bits
func (p *PresentationLayer) CodificarMensaje(texto string) ([]byte, error) {
	if !utf8.ValidString(texto) {
		return nil, fmt.Errorf("el texto contiene caracteres no válidos UTF-8")
	}

	// Validar que solo contiene caracteres ASCII imprimibles
	for i, r := range texto {
		if r > 127 {
			return nil, fmt.Errorf("carácter no-ASCII en posición %d: '%c' (código %d)", i, r, r)
		}
		if r < 32 && r != 9 && r != 10 && r != 13 { // Permitir tab, newline, carriage return
			return nil, fmt.Errorf("carácter de control no permitido en posición %d: código %d", i, r)
		}
	}

	// Convertir cada carácter a 8 bits
	var bits []byte
	for _, char := range []byte(texto) {
		for i := 7; i >= 0; i-- {
			bit := (char >> i) & 1
			bits = append(bits, bit)
		}
	}

	return bits, nil
}

// DecodificarMensaje convierte bits a texto ASCII
func (p *PresentationLayer) DecodificarMensaje(bits []byte) (string, error) {
	if len(bits)%8 != 0 {
		return "", fmt.Errorf("la longitud de bits (%d) no es múltiplo de 8", len(bits))
	}

	// Validar que los bits son solo 0 o 1
	for i, bit := range bits {
		if bit != 0 && bit != 1 {
			return "", fmt.Errorf("bit inválido en posición %d: %d (debe ser 0 o 1)", i, bit)
		}
	}

	var resultado []byte
	for i := 0; i < len(bits); i += 8 {
		var charCode byte
		for j := 0; j < 8; j++ {
			charCode |= bits[i+j] << (7 - j)
		}

		// Validar que es un carácter ASCII válido
		if charCode > 127 {
			return "", fmt.Errorf("código de carácter inválido: %d (mayor que 127)", charCode)
		}

		// Permitir caracteres imprimibles y algunos de control básicos
		if charCode < 32 && charCode != 9 && charCode != 10 && charCode != 13 {
			return "", fmt.Errorf("carácter de control no permitido: código %d", charCode)
		}

		resultado = append(resultado, charCode)
	}

	return string(resultado), nil
}

// ObtenerEstadisticas devuelve información sobre la codificación
func (p *PresentationLayer) ObtenerEstadisticas(texto string) map[string]interface{} {
	stats := make(map[string]interface{})

	stats["caracteres"] = len(texto)
	stats["bytes"] = len([]byte(texto))
	stats["bits"] = len(texto) * 8

	// Contar tipos de caracteres
	letras := 0
	numeros := 0
	espacios := 0
	especiales := 0

	for _, char := range texto {
		switch {
		case char >= 'a' && char <= 'z' || char >= 'A' && char <= 'Z':
			letras++
		case char >= '0' && char <= '9':
			numeros++
		case char == ' ' || char == '\t' || char == '\n' || char == '\r':
			espacios++
		default:
			especiales++
		}
	}

	stats["letras"] = letras
	stats["numeros"] = numeros
	stats["espacios"] = espacios
	stats["especiales"] = especiales

	// Eficiencia de codificación
	stats["eficiencia"] = float64(len(texto)*8) / float64(len(texto)*8) // 100% para ASCII puro

	return stats
}

// MostrarEstadisticas imprime las estadísticas de codificación
func (p *PresentationLayer) MostrarEstadisticas(texto string) {
	stats := p.ObtenerEstadisticas(texto)

	fmt.Println("📝 Estadísticas de Presentación:")
	fmt.Printf("   Caracteres: %d\n", stats["caracteres"])
	fmt.Printf("   Bytes: %d\n", stats["bytes"])
	fmt.Printf("   Bits: %d\n", stats["bits"])
	fmt.Printf("   Composición:\n")
	fmt.Printf("     - Letras: %d\n", stats["letras"])
	fmt.Printf("     - Números: %d\n", stats["numeros"])
	fmt.Printf("     - Espacios: %d\n", stats["espacios"])
	fmt.Printf("     - Especiales: %d\n", stats["especiales"])
	fmt.Println()
}

// ValidarTexto verifica que el texto sea válido para transmisión
func (p *PresentationLayer) ValidarTexto(texto string) error {
	if texto == "" {
		return fmt.Errorf("el texto no puede estar vacío")
	}

	if len(texto) > 65535 { // Límite por el header de 2 bytes para longitud
		return fmt.Errorf("el texto es demasiado largo: %d caracteres (máximo 65535)", len(texto))
	}

	// Validar UTF-8
	if !utf8.ValidString(texto) {
		return fmt.Errorf("el texto contiene caracteres no válidos UTF-8")
	}

	// Validar ASCII
	for i, r := range texto {
		if r > 127 {
			return fmt.Errorf("carácter no-ASCII en posición %d: '%c'", i, r)
		}
	}

	return nil
}

// ConvertirBitsABytes convierte un slice de bits a bytes (para compatibilidad)
func (p *PresentationLayer) ConvertirBitsABytes(bits []byte) []byte {
	if len(bits) == 0 {
		return []byte{}
	}

	// Hacer padding a múltiplo de 8 si es necesario
	paddedBits := make([]byte, len(bits))
	copy(paddedBits, bits)

	for len(paddedBits)%8 != 0 {
		paddedBits = append(paddedBits, 0)
	}

	// Convertir grupos de 8 bits a bytes
	var resultado []byte
	for i := 0; i < len(paddedBits); i += 8 {
		var byteVal byte
		for j := 0; j < 8; j++ {
			byteVal |= paddedBits[i+j] << (7 - j)
		}
		resultado = append(resultado, byteVal)
	}

	return resultado
}

// ConvertirBytesABits convierte bytes a bits (para compatibilidad)
func (p *PresentationLayer) ConvertirBytesABits(data []byte) []byte {
	var bits []byte
	for _, b := range data {
		for i := 7; i >= 0; i-- {
			bit := (b >> i) & 1
			bits = append(bits, bit)
		}
	}
	return bits
}
