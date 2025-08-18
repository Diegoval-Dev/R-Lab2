package application

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
)

// MessageConfig contiene la configuración del mensaje a enviar
type MessageConfig struct {
	Text      string  // Mensaje de texto a enviar
	Algorithm string  // "crc" o "hamming"
	BER       float64 // Bit Error Rate (0.0 to 1.0)
	Mode      string  // "manual" o "benchmark"
	Count     int     // Número de iteraciones para benchmark
}

// ApplicationLayer maneja la interacción con el usuario
type ApplicationLayer struct {
	scanner *bufio.Scanner
}

// NewApplicationLayer crea una nueva instancia
func NewApplicationLayer() *ApplicationLayer {
	return &ApplicationLayer{
		scanner: bufio.NewScanner(os.Stdin),
	}
}

// SolicitarMensaje solicita entrada del usuario según el modo
func (app *ApplicationLayer) SolicitarMensaje(mode string) (*MessageConfig, error) {
	switch mode {
	case "manual":
		return app.solicitarMensajeManual()
	case "benchmark":
		return app.solicitarMensajeBenchmark()
	default:
		return nil, fmt.Errorf("modo inválido: %s (usar 'manual' o 'benchmark')", mode)
	}
}

// solicitarMensajeManual solicita configuración manual del usuario
func (app *ApplicationLayer) solicitarMensajeManual() (*MessageConfig, error) {
	config := &MessageConfig{Mode: "manual", Count: 1}

	// Solicitar mensaje
	fmt.Print("Ingrese el mensaje a transmitir: ")
	if !app.scanner.Scan() {
		return nil, fmt.Errorf("error leyendo mensaje")
	}
	config.Text = strings.TrimSpace(app.scanner.Text())
	if config.Text == "" {
		return nil, fmt.Errorf("el mensaje no puede estar vacío")
	}

	// Solicitar algoritmo
	for {
		fmt.Print("Seleccione algoritmo (1=CRC-32, 2=Hamming(7,4)): ")
		if !app.scanner.Scan() {
			return nil, fmt.Errorf("error leyendo algoritmo")
		}

		choice := strings.TrimSpace(app.scanner.Text())
		switch choice {
		case "1", "crc":
			config.Algorithm = "crc"
		case "2", "hamming":
			config.Algorithm = "hamming"
		default:
			fmt.Println("❌ Opción inválida. Ingrese 1 para CRC-32 o 2 para Hamming(7,4)")
			continue
		}
		break
	}

	// Solicitar BER
	for {
		fmt.Print("Ingrese BER (0.0-0.1, ej: 0.01): ")
		if !app.scanner.Scan() {
			return nil, fmt.Errorf("error leyendo BER")
		}

		berStr := strings.TrimSpace(app.scanner.Text())
		ber, err := strconv.ParseFloat(berStr, 64)
		if err != nil {
			fmt.Println("❌ BER inválido. Ingrese un número decimal (ej: 0.01)")
			continue
		}
		if ber < 0.0 || ber > 1.0 {
			fmt.Println("❌ BER debe estar entre 0.0 y 1.0")
			continue
		}
		config.BER = ber
		break
	}

	return config, nil
}

// solicitarMensajeBenchmark solicita configuración para pruebas automatizadas
func (app *ApplicationLayer) solicitarMensajeBenchmark() (*MessageConfig, error) {
	config := &MessageConfig{Mode: "benchmark"}

	// Solicitar configuración de benchmark
	fmt.Print("Mensaje base para benchmark [Hello World]: ")
	if !app.scanner.Scan() {
		return nil, fmt.Errorf("error leyendo mensaje")
	}
	config.Text = strings.TrimSpace(app.scanner.Text())
	if config.Text == "" {
		config.Text = "Hello World" // Valor por defecto
	}

	// Algoritmo para benchmark
	for {
		fmt.Print("Algoritmo para benchmark (1=CRC-32, 2=Hamming(7,4), 3=Ambos): ")
		if !app.scanner.Scan() {
			return nil, fmt.Errorf("error leyendo algoritmo")
		}

		choice := strings.TrimSpace(app.scanner.Text())
		switch choice {
		case "1":
			config.Algorithm = "crc"
		case "2":
			config.Algorithm = "hamming"
		case "3":
			config.Algorithm = "both"
		default:
			fmt.Println("❌ Opción inválida")
			continue
		}
		break
	}

	// BER para benchmark
	for {
		fmt.Print("BER para benchmark [0.01]: ")
		if !app.scanner.Scan() {
			return nil, fmt.Errorf("error leyendo BER")
		}

		berStr := strings.TrimSpace(app.scanner.Text())
		if berStr == "" {
			config.BER = 0.01 // Valor por defecto
			break
		}

		ber, err := strconv.ParseFloat(berStr, 64)
		if err != nil {
			fmt.Println("❌ BER inválido")
			continue
		}
		if ber < 0.0 || ber > 1.0 {
			fmt.Println("❌ BER debe estar entre 0.0 y 1.0")
			continue
		}
		config.BER = ber
		break
	}

	// Cantidad de iteraciones
	for {
		fmt.Print("Número de iteraciones [1000]: ")
		if !app.scanner.Scan() {
			return nil, fmt.Errorf("error leyendo cantidad")
		}

		countStr := strings.TrimSpace(app.scanner.Text())
		if countStr == "" {
			config.Count = 1000 // Valor por defecto
			break
		}

		count, err := strconv.Atoi(countStr)
		if err != nil {
			fmt.Println("❌ Cantidad inválida")
			continue
		}
		if count <= 0 {
			fmt.Println("❌ La cantidad debe ser mayor a 0")
			continue
		}
		config.Count = count
		break
	}

	return config, nil
}

// MostrarConfiguracion muestra la configuración seleccionada
func (app *ApplicationLayer) MostrarConfiguracion(config *MessageConfig) {
	fmt.Println("\n📋 Configuración:")
	fmt.Printf("   Mensaje: \"%s\"\n", config.Text)
	fmt.Printf("   Algoritmo: %s\n", strings.ToUpper(config.Algorithm))
	fmt.Printf("   BER: %.3f (%.1f%%)\n", config.BER, config.BER*100)
	fmt.Printf("   Modo: %s\n", config.Mode)
	if config.Mode == "benchmark" {
		fmt.Printf("   Iteraciones: %d\n", config.Count)
	}
	fmt.Println()
}

// MostrarResultado muestra el resultado de la transmisión
func (app *ApplicationLayer) MostrarResultado(success bool, details string) {
	if success {
		fmt.Printf("✅ Transmisión exitosa: %s\n", details)
	} else {
		fmt.Printf("❌ Error en transmisión: %s\n", details)
	}
}

// MostrarEstadisticas muestra estadísticas de benchmark
func (app *ApplicationLayer) MostrarEstadisticas(stats map[string]interface{}) {
	fmt.Println("\n📊 Estadísticas de Benchmark:")
	fmt.Println("─────────────────────────────")

	if total, ok := stats["total"].(int); ok {
		fmt.Printf("Total de mensajes: %d\n", total)
	}
	if successful, ok := stats["successful"].(int); ok {
		fmt.Printf("Exitosos: %d\n", successful)
	}
	if failed, ok := stats["failed"].(int); ok {
		fmt.Printf("Fallidos: %d\n", failed)
	}
	if successRate, ok := stats["success_rate"].(float64); ok {
		fmt.Printf("Tasa de éxito: %.2f%%\n", successRate*100)
	}
	if avgTime, ok := stats["avg_time"].(float64); ok {
		fmt.Printf("Tiempo promedio: %.2fms\n", avgTime*1000)
	}

	fmt.Println()
}

// ValidarConfiguracion valida que la configuración sea válida
func (app *ApplicationLayer) ValidarConfiguracion(config *MessageConfig) error {
	if config == nil {
		return fmt.Errorf("configuración es nil")
	}

	if config.Text == "" {
		return fmt.Errorf("el mensaje no puede estar vacío")
	}

	if config.Algorithm != "crc" && config.Algorithm != "hamming" && config.Algorithm != "both" {
		return fmt.Errorf("algoritmo inválido: %s", config.Algorithm)
	}

	if config.BER < 0.0 || config.BER > 1.0 {
		return fmt.Errorf("BER inválido: %.3f (debe estar entre 0.0 y 1.0)", config.BER)
	}

	if config.Mode == "benchmark" && config.Count <= 0 {
		return fmt.Errorf("cantidad de iteraciones inválida: %d", config.Count)
	}

	return nil
}
