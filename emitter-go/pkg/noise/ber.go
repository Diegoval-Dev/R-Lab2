package noise

import (
	"fmt"
	"math/rand"
	"time"
)

// NoiseLayer maneja la inyección de errores en la transmisión
type NoiseLayer struct {
	rng *rand.Rand
}

// NewNoiseLayer crea una nueva instancia con semilla aleatoria
func NewNoiseLayer() *NoiseLayer {
	return &NoiseLayer{
		rng: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// NewNoiseLayerWithSeed crea una instancia con semilla específica (para tests reproducibles)
func NewNoiseLayerWithSeed(seed int64) *NoiseLayer {
	return &NoiseLayer{
		rng: rand.New(rand.NewSource(seed)),
	}
}

// ErrorResult contiene información sobre los errores inyectados
type ErrorResult struct {
	OriginalBits   []byte  // Bits originales
	NoisyBits      []byte  // Bits con ruido aplicado
	ErrorPositions []int   // Posiciones donde se inyectaron errores
	TotalBits      int     // Total de bits procesados
	ErrorsInjected int     // Cantidad de errores inyectados
	ActualBER      float64 // BER real obtenido
}

// AplicarRuido inyecta errores de bit con la probabilidad BER especificada
func (n *NoiseLayer) AplicarRuido(bits []byte, ber float64) (*ErrorResult, error) {
	if ber < 0.0 || ber > 1.0 {
		return nil, fmt.Errorf("BER inválido: %.3f (debe estar entre 0.0 y 1.0)", ber)
	}

	// Validar que los bits son válidos (0 o 1)
	for i, bit := range bits {
		if bit != 0 && bit != 1 {
			return nil, fmt.Errorf("bit inválido en posición %d: %d (debe ser 0 o 1)", i, bit)
		}
	}

	// Crear copia de los bits originales
	noisyBits := make([]byte, len(bits))
	copy(noisyBits, bits)

	var errorPositions []int

	// Aplicar ruido bit por bit
	for i := 0; i < len(noisyBits); i++ {
		if n.rng.Float64() < ber {
			// Inyectar error: flip del bit
			noisyBits[i] = 1 - noisyBits[i]
			errorPositions = append(errorPositions, i)
		}
	}

	// Calcular BER real obtenido
	actualBER := float64(len(errorPositions)) / float64(len(bits))

	result := &ErrorResult{
		OriginalBits:   bits,
		NoisyBits:      noisyBits,
		ErrorPositions: errorPositions,
		TotalBits:      len(bits),
		ErrorsInjected: len(errorPositions),
		ActualBER:      actualBER,
	}

	return result, nil
}

// SimularCanalRuidoso simula múltiples transmisiones para análisis estadístico
func (n *NoiseLayer) SimularCanalRuidoso(bits []byte, ber float64, iteraciones int) (*ChannelStats, error) {
	if iteraciones <= 0 {
		return nil, fmt.Errorf("iteraciones debe ser mayor a 0: %d", iteraciones)
	}

	stats := &ChannelStats{
		TargetBER:         ber,
		Iterations:        iteraciones,
		TotalBits:         len(bits) * iteraciones,
		ErrorDistribution: make(map[int]int),
	}

	var totalErrors int
	var berValues []float64

	for i := 0; i < iteraciones; i++ {
		result, err := n.AplicarRuido(bits, ber)
		if err != nil {
			return nil, fmt.Errorf("error en iteración %d: %v", i, err)
		}

		totalErrors += result.ErrorsInjected
		berValues = append(berValues, result.ActualBER)

		// Actualizar distribución de errores
		stats.ErrorDistribution[result.ErrorsInjected]++

		// Trackear máximos y mínimos
		if i == 0 || result.ErrorsInjected > stats.MaxErrors {
			stats.MaxErrors = result.ErrorsInjected
		}
		if i == 0 || result.ErrorsInjected < stats.MinErrors {
			stats.MinErrors = result.ErrorsInjected
		}
	}

	stats.TotalErrors = totalErrors
	stats.AverageBER = float64(totalErrors) / float64(stats.TotalBits)
	stats.AverageErrorsPerTransmission = float64(totalErrors) / float64(iteraciones)

	// Calcular varianza y desviación estándar del BER
	var berVariance float64
	for _, berVal := range berValues {
		diff := berVal - stats.AverageBER
		berVariance += diff * diff
	}
	berVariance /= float64(len(berValues))
	stats.BERVariance = berVariance
	stats.BERStdDev = sqrt(berVariance)

	return stats, nil
}

// ChannelStats contiene estadísticas del canal ruidoso
type ChannelStats struct {
	TargetBER                    float64
	AverageBER                   float64
	BERVariance                  float64
	BERStdDev                    float64
	Iterations                   int
	TotalBits                    int
	TotalErrors                  int
	AverageErrorsPerTransmission float64
	MaxErrors                    int
	MinErrors                    int
	ErrorDistribution            map[int]int // cantidad_errores -> frecuencia
}

// MostrarEstadisticas imprime las estadísticas del canal
func (stats *ChannelStats) MostrarEstadisticas() {
	fmt.Println("📡 Estadísticas del Canal Ruidoso:")
	fmt.Printf("   BER objetivo: %.4f (%.2f%%)\n", stats.TargetBER, stats.TargetBER*100)
	fmt.Printf("   BER promedio: %.4f (%.2f%%)\n", stats.AverageBER, stats.AverageBER*100)
	fmt.Printf("   Desviación std BER: %.4f\n", stats.BERStdDev)
	fmt.Printf("   Iteraciones: %d\n", stats.Iterations)
	fmt.Printf("   Total de bits: %d\n", stats.TotalBits)
	fmt.Printf("   Total de errores: %d\n", stats.TotalErrors)
	fmt.Printf("   Errores promedio por transmisión: %.1f\n", stats.AverageErrorsPerTransmission)
	fmt.Printf("   Rango de errores: %d - %d\n", stats.MinErrors, stats.MaxErrors)

	// Mostrar distribución de errores (top 5)
	fmt.Println("   Distribución de errores (top 5):")
	type errorCount struct {
		errors int
		count  int
	}
	var distribution []errorCount
	for errors, count := range stats.ErrorDistribution {
		distribution = append(distribution, errorCount{errors, count})
	}

	// Ordenar por frecuencia (simple bubble sort para pocos elementos)
	for i := 0; i < len(distribution); i++ {
		for j := i + 1; j < len(distribution); j++ {
			if distribution[i].count < distribution[j].count {
				distribution[i], distribution[j] = distribution[j], distribution[i]
			}
		}
	}

	limit := 5
	if len(distribution) < limit {
		limit = len(distribution)
	}

	for i := 0; i < limit; i++ {
		percentage := float64(distribution[i].count) / float64(stats.Iterations) * 100
		fmt.Printf("     %d errores: %d veces (%.1f%%)\n",
			distribution[i].errors, distribution[i].count, percentage)
	}
	fmt.Println()
}

// ValidarConfiguracion valida los parámetros de ruido
func (n *NoiseLayer) ValidarConfiguracion(ber float64, bits []byte) error {
	if ber < 0.0 || ber > 1.0 {
		return fmt.Errorf("BER inválido: %.3f (debe estar entre 0.0 y 1.0)", ber)
	}

	if len(bits) == 0 {
		return fmt.Errorf("no hay bits para procesar")
	}

	// Validar bits
	for i, bit := range bits {
		if bit != 0 && bit != 1 {
			return fmt.Errorf("bit inválido en posición %d: %d", i, bit)
		}
	}

	return nil
}

// ObtenerSemilla devuelve una nueva semilla basada en el tiempo actual
func ObtenerSemilla() int64 {
	return time.Now().UnixNano()
}

// Función auxiliar para calcular raíz cuadrada (aproximación simple)
func sqrt(x float64) float64 {
	if x == 0 {
		return 0
	}

	// Método de Newton-Raphson para aproximar sqrt
	guess := x / 2
	for i := 0; i < 10; i++ { // 10 iteraciones son suficientes para precisión
		guess = (guess + x/guess) / 2
	}
	return guess
}

// EstimarImpacto estima el impacto del ruido en diferentes BER
func (n *NoiseLayer) EstimarImpacto(longitud int, berValues []float64) map[float64]float64 {
	estimaciones := make(map[float64]float64)

	for _, ber := range berValues {
		erroresEsperados := float64(longitud) * ber
		estimaciones[ber] = erroresEsperados
	}

	return estimaciones
}
