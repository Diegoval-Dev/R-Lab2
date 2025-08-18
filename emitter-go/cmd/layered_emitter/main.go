package main

import (
	"flag"
	"fmt"
	"os"
	"time"

	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/application"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/frame"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/noise"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/presentation"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/wsclient"
)

// LayeredEmitter implementa la arquitectura de capas completa
type LayeredEmitter struct {
	app          *application.ApplicationLayer
	presentation *presentation.PresentationLayer
	noise        *noise.NoiseLayer
	wsURL        string
}

// NewLayeredEmitter crea una nueva instancia
func NewLayeredEmitter(wsURL string) *LayeredEmitter {
	return &LayeredEmitter{
		app:          application.NewApplicationLayer(),
		presentation: presentation.NewPresentationLayer(),
		noise:        noise.NewNoiseLayer(),
		wsURL:        wsURL,
	}
}

// ProcessMessage procesa un mensaje a través de todas las capas
func (le *LayeredEmitter) ProcessMessage(config *application.MessageConfig) (*TransmissionResult, error) {
	result := &TransmissionResult{
		Config:    config,
		StartTime: time.Now(),
	}

	fmt.Printf("🚀 Iniciando transmisión de: \"%s\"\n", config.Text)
	fmt.Printf("   Algoritmo: %s, BER: %.3f\n\n", config.Algorithm, config.BER)

	// CAPA 1: APLICACIÓN (ya procesada)
	result.OriginalMessage = config.Text

	// CAPA 2: PRESENTACIÓN - ASCII → bits
	fmt.Println("📝 Capa de Presentación - Codificando mensaje...")
	textBits, err := le.presentation.CodificarMensaje(config.Text)
	if err != nil {
		return nil, fmt.Errorf("error en presentación: %v", err)
	}
	result.TextBits = textBits
	fmt.Printf("   Texto → %d bits\n", len(textBits))

	// CAPA 3: ENLACE - Aplicar detección/corrección
	fmt.Println("🔗 Capa de Enlace - Aplicando algoritmo...")
	var frameBytes []byte

	switch config.Algorithm {
	case "crc":
		// Para CRC: bits → bytes → frame con CRC
		payloadBytes := le.presentation.ConvertirBitsABytes(textBits)
		frameBytes, err = frame.BuildFrame(payloadBytes)
		if err != nil {
			return nil, fmt.Errorf("error construyendo frame CRC: %v", err)
		}
		fmt.Printf("   CRC-32 aplicado, frame de %d bytes\n", len(frameBytes))

	case "hamming":
		// Para Hamming: bits → hamming encode → bytes → frame con CRC
		frameBytes, err = frame.BuildFrameWithHamming(le.presentation.ConvertirBitsABytes(textBits))
		if err != nil {
			return nil, fmt.Errorf("error construyendo frame Hamming: %v", err)
		}
		fmt.Printf("   Hamming(7,4) + CRC-32 aplicado, frame de %d bytes\n", len(frameBytes))

	default:
		return nil, fmt.Errorf("algoritmo no soportado: %s", config.Algorithm)
	}

	result.FrameBytes = frameBytes

	// CAPA 4: RUIDO - Inyectar errores
	fmt.Println("📡 Capa de Ruido - Simulando canal ruidoso...")
	frameBits := le.presentation.ConvertirBytesABits(frameBytes)
	noiseResult, err := le.noise.AplicarRuido(frameBits, config.BER)
	if err != nil {
		return nil, fmt.Errorf("error aplicando ruido: %v", err)
	}

	result.OriginalFrameBits = noiseResult.OriginalBits
	result.NoisyFrameBits = noiseResult.NoisyBits
	result.ErrorPositions = noiseResult.ErrorPositions
	result.ErrorsInjected = noiseResult.ErrorsInjected
	result.ActualBER = noiseResult.ActualBER

	fmt.Printf("   %d errores inyectados en %d bits (BER real: %.4f)\n",
		noiseResult.ErrorsInjected, len(frameBits), noiseResult.ActualBER)

	// CAPA 5: TRANSMISIÓN - Enviar por WebSocket
	fmt.Println("🌐 Capa de Transmisión - Enviando por WebSocket...")
	noisyFrameBytes := le.presentation.ConvertirBitsABytes(noiseResult.NoisyBits)

	transmissionStart := time.Now()
	err = wsclient.SendFrame(le.wsURL, noisyFrameBytes)
	transmissionDuration := time.Since(transmissionStart)

	if err != nil {
		result.Success = false
		result.Error = err.Error()
		fmt.Printf("   ❌ Error de transmisión: %v\n", err)
	} else {
		result.Success = true
		fmt.Printf("   ✅ Transmisión exitosa (%v)\n", transmissionDuration)
	}

	result.TransmissionTime = transmissionDuration
	result.EndTime = time.Now()
	result.TotalTime = result.EndTime.Sub(result.StartTime)

	return result, nil
}

// RunBenchmark ejecuta múltiples transmisiones para análisis
func (le *LayeredEmitter) RunBenchmark(config *application.MessageConfig) (*BenchmarkResult, error) {
	fmt.Printf("🎯 Iniciando benchmark: %d iteraciones\n", config.Count)
	fmt.Printf("   Mensaje: \"%s\"\n", config.Text)
	fmt.Printf("   Algoritmo: %s, BER: %.3f\n\n", config.Algorithm, config.BER)

	benchmark := &BenchmarkResult{
		Config:    config,
		StartTime: time.Now(),
		Results:   make([]*TransmissionResult, 0, config.Count),
	}

	var successful, failed int
	var totalTransmissionTime time.Duration

	for i := 0; i < config.Count; i++ {
		if i%100 == 0 && i > 0 {
			fmt.Printf("   Progreso: %d/%d (%.1f%%)\n", i, config.Count, float64(i)/float64(config.Count)*100)
		}

		result, err := le.ProcessMessage(config)
		if err != nil {
			failed++
			// Crear resultado de error
			result = &TransmissionResult{
				Config:    config,
				Success:   false,
				Error:     err.Error(),
				StartTime: time.Now(),
				EndTime:   time.Now(),
			}
		} else if result.Success {
			successful++
			totalTransmissionTime += result.TransmissionTime
		} else {
			failed++
		}

		benchmark.Results = append(benchmark.Results, result)
	}

	benchmark.EndTime = time.Now()
	benchmark.TotalTime = benchmark.EndTime.Sub(benchmark.StartTime)
	benchmark.Successful = successful
	benchmark.Failed = failed
	benchmark.SuccessRate = float64(successful) / float64(config.Count)

	if successful > 0 {
		benchmark.AverageTransmissionTime = totalTransmissionTime / time.Duration(successful)
	}

	// Mostrar resumen
	fmt.Printf("\n📊 Resumen del Benchmark:\n")
	fmt.Printf("   Total: %d transmisiones\n", config.Count)
	fmt.Printf("   Exitosas: %d (%.1f%%)\n", successful, benchmark.SuccessRate*100)
	fmt.Printf("   Fallidas: %d (%.1f%%)\n", failed, float64(failed)/float64(config.Count)*100)
	fmt.Printf("   Tiempo total: %v\n", benchmark.TotalTime)
	fmt.Printf("   Tiempo promedio por transmisión: %v\n", benchmark.AverageTransmissionTime)
	fmt.Println()

	return benchmark, nil
}

// TransmissionResult contiene el resultado de una transmisión
type TransmissionResult struct {
	Config            *application.MessageConfig
	OriginalMessage   string
	TextBits          []byte
	FrameBytes        []byte
	OriginalFrameBits []byte
	NoisyFrameBits    []byte
	ErrorPositions    []int
	ErrorsInjected    int
	ActualBER         float64
	Success           bool
	Error             string
	StartTime         time.Time
	EndTime           time.Time
	TotalTime         time.Duration
	TransmissionTime  time.Duration
}

// BenchmarkResult contiene resultados de múltiples transmisiones
type BenchmarkResult struct {
	Config                  *application.MessageConfig
	Results                 []*TransmissionResult
	StartTime               time.Time
	EndTime                 time.Time
	TotalTime               time.Duration
	Successful              int
	Failed                  int
	SuccessRate             float64
	AverageTransmissionTime time.Duration
}

func main() {
	// Flags de línea de comandos
	var (
		mode  = flag.String("mode", "manual", "Modo de operación: manual o benchmark")
		wsURL = flag.String("ws-url", "ws://localhost:9000", "URL del servidor WebSocket receptor")
		help  = flag.Bool("help", false, "Mostrar ayuda")
	)
	flag.Parse()

	if *help {
		mostrarAyuda()
		return
	}

	fmt.Println("🚀 Emisor por Capas - Lab 2")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Printf("Modo: %s\n", *mode)
	fmt.Printf("Receptor: %s\n\n", *wsURL)

	// Crear emisor
	emitter := NewLayeredEmitter(*wsURL)

	// Solicitar configuración
	config, err := emitter.app.SolicitarMensaje(*mode)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Error en configuración: %v\n", err)
		os.Exit(1)
	}

	// Validar configuración
	err = emitter.app.ValidarConfiguracion(config)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ Configuración inválida: %v\n", err)
		os.Exit(1)
	}

	// Mostrar configuración
	emitter.app.MostrarConfiguracion(config)

	// Ejecutar según el modo
	switch *mode {
	case "manual":
		result, err := emitter.ProcessMessage(config)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Error en transmisión: %v\n", err)
			os.Exit(1)
		}

		// Mostrar resultado detallado
		mostrarResultadoDetallado(result)

	case "benchmark":
		benchmark, err := emitter.RunBenchmark(config)
		if err != nil {
			fmt.Fprintf(os.Stderr, "❌ Error en benchmark: %v\n", err)
			os.Exit(1)
		}

		// Analizar y mostrar estadísticas
		analizarBenchmark(benchmark)

	default:
		fmt.Fprintf(os.Stderr, "❌ Modo inválido: %s (usar 'manual' o 'benchmark')\n", *mode)
		os.Exit(1)
	}
}

func mostrarAyuda() {
	fmt.Println("🚀 Emisor por Capas - Lab 2")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Println("Implementa arquitectura de 5 capas para transmisión con detección/corrección de errores.")
	fmt.Println()
	fmt.Println("Uso:")
	fmt.Printf("  %s [flags]\n\n", os.Args[0])
	fmt.Println("Flags:")
	fmt.Println("  --mode string     Modo de operación: 'manual' o 'benchmark' (default: manual)")
	fmt.Println("  --ws-url string   URL del receptor WebSocket (default: ws://localhost:9000)")
	fmt.Println("  --help           Mostrar esta ayuda")
	fmt.Println()
	fmt.Println("Modos:")
	fmt.Println("  manual    - Transmisión interactiva de un mensaje")
	fmt.Println("  benchmark - Múltiples transmisiones para análisis estadístico")
	fmt.Println()
	fmt.Println("Capas implementadas:")
	fmt.Println("  1. Aplicación    - Input del usuario")
	fmt.Println("  2. Presentación  - ASCII ↔ bits")
	fmt.Println("  3. Enlace        - CRC-32 / Hamming(7,4)")
	fmt.Println("  4. Ruido         - Inyección de errores (BER)")
	fmt.Println("  5. Transmisión   - WebSocket")
}

func mostrarResultadoDetallado(result *TransmissionResult) {
	fmt.Println("📋 Resultado Detallado:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
	fmt.Printf("Mensaje original: \"%s\"\n", result.OriginalMessage)
	fmt.Printf("Bits de texto: %d\n", len(result.TextBits))
	fmt.Printf("Tamaño de frame: %d bytes\n", len(result.FrameBytes))
	fmt.Printf("Errores inyectados: %d\n", result.ErrorsInjected)
	fmt.Printf("BER real: %.4f\n", result.ActualBER)
	fmt.Printf("Tiempo total: %v\n", result.TotalTime)
	fmt.Printf("Tiempo transmisión: %v\n", result.TransmissionTime)

	if result.Success {
		fmt.Println("✅ Estado: EXITOSA")
	} else {
		fmt.Printf("❌ Estado: FALLIDA - %s\n", result.Error)
	}
	fmt.Println()
}

func analizarBenchmark(benchmark *BenchmarkResult) {
	fmt.Println("📊 Análisis del Benchmark:")
	fmt.Println("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

	// Estadísticas básicas
	fmt.Printf("Configuración: %s, BER=%.3f, %d iteraciones\n",
		benchmark.Config.Algorithm, benchmark.Config.BER, benchmark.Config.Count)
	fmt.Printf("Tasa de éxito: %.2f%% (%d/%d)\n",
		benchmark.SuccessRate*100, benchmark.Successful, benchmark.Config.Count)
	fmt.Printf("Tiempo total: %v (promedio: %v por transmisión)\n",
		benchmark.TotalTime, benchmark.AverageTransmissionTime)

	// Análisis de errores
	if len(benchmark.Results) > 0 {
		var totalErrors int
		var totalBER float64
		successful := 0

		for _, result := range benchmark.Results {
			if result.Success {
				totalErrors += result.ErrorsInjected
				totalBER += result.ActualBER
				successful++
			}
		}

		if successful > 0 {
			avgErrors := float64(totalErrors) / float64(successful)
			avgBER := totalBER / float64(successful)

			fmt.Printf("Errores promedio por transmisión: %.1f\n", avgErrors)
			fmt.Printf("BER promedio: %.4f (objetivo: %.4f)\n", avgBER, benchmark.Config.BER)
		}
	}

	fmt.Println()
	fmt.Println("💡 Para análisis más detallado, implementar exportación a CSV")
}
