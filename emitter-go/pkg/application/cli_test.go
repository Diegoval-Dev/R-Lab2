package application

import (
	"strings"
	"testing"
)

func TestMessageConfig_Validation(t *testing.T) {
	app := NewApplicationLayer()

	tests := []struct {
		name    string
		config  *MessageConfig
		wantErr bool
	}{
		{
			name: "valid manual config",
			config: &MessageConfig{
				Text:      "Hello",
				Algorithm: "crc",
				BER:       0.01,
				Mode:      "manual",
				Count:     1,
			},
			wantErr: false,
		},
		{
			name: "valid benchmark config",
			config: &MessageConfig{
				Text:      "Test message",
				Algorithm: "hamming",
				BER:       0.05,
				Mode:      "benchmark",
				Count:     1000,
			},
			wantErr: false,
		},
		{
			name: "empty text",
			config: &MessageConfig{
				Text:      "",
				Algorithm: "crc",
				BER:       0.01,
				Mode:      "manual",
			},
			wantErr: true,
		},
		{
			name: "invalid algorithm",
			config: &MessageConfig{
				Text:      "Hello",
				Algorithm: "invalid",
				BER:       0.01,
				Mode:      "manual",
			},
			wantErr: true,
		},
		{
			name: "invalid BER - negative",
			config: &MessageConfig{
				Text:      "Hello",
				Algorithm: "crc",
				BER:       -0.1,
				Mode:      "manual",
			},
			wantErr: true,
		},
		{
			name: "invalid BER - too high",
			config: &MessageConfig{
				Text:      "Hello",
				Algorithm: "crc",
				BER:       1.5,
				Mode:      "manual",
			},
			wantErr: true,
		},
		{
			name: "benchmark with zero count",
			config: &MessageConfig{
				Text:      "Hello",
				Algorithm: "crc",
				BER:       0.01,
				Mode:      "benchmark",
				Count:     0,
			},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := app.ValidarConfiguracion(tt.config)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidarConfiguracion() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

// pkg/presentation/ascii_test.go
package presentation

import (
	"reflect"
	"testing"
)

func TestPresentationLayer_CodificarMensaje(t *testing.T) {
	p := NewPresentationLayer()

	tests := []struct {
		name    string
		input   string
		want    []byte
		wantErr bool
	}{
		{
			name:  "single character A",
			input: "A",
			want:  []byte{0, 1, 0, 0, 0, 0, 0, 1}, // ASCII 65 = 01000001
		},
		{
			name:  "simple text Hi",
			input: "Hi",
			want: []byte{
				0, 1, 0, 0, 1, 0, 0, 0, // H = 72 = 01001000
				0, 1, 1, 0, 1, 0, 0, 1, // i = 105 = 01101001
			},
		},
		{
			name:    "empty string",
			input:   "",
			wantErr: true,
		},
		{
			name:    "non-ASCII character",
			input:   "Hölá",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := p.CodificarMensaje(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("CodificarMensaje() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && !reflect.DeepEqual(got, tt.want) {
				t.Errorf("CodificarMensaje() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestPresentationLayer_DecodificarMensaje(t *testing.T) {
	p := NewPresentationLayer()

	tests := []struct {
		name    string
		input   []byte
		want    string
		wantErr bool
	}{
		{
			name:  "single character A",
			input: []byte{0, 1, 0, 0, 0, 0, 0, 1}, // ASCII 65
			want:  "A",
		},
		{
			name: "simple text Hi",
			input: []byte{
				0, 1, 0, 0, 1, 0, 0, 0, // H = 72
				0, 1, 1, 0, 1, 0, 0, 1, // i = 105
			},
			want: "Hi",
		},
		{
			name:    "invalid length",
			input:   []byte{0, 1, 0}, // Not multiple of 8
			wantErr: true,
		},
		{
			name:    "invalid bit value",
			input:   []byte{0, 1, 0, 2, 0, 0, 0, 1}, // Contains '2'
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, err := p.DecodificarMensaje(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("DecodificarMensaje() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && got != tt.want {
				t.Errorf("DecodificarMensaje() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestPresentationLayer_RoundTrip(t *testing.T) {
	p := NewPresentationLayer()
	
	testMessages := []string{
		"Hello World!",
		"Test123",
		"ASCII only text",
		"Special chars: !@#$%^&*()",
	}

	for _, original := range testMessages {
		t.Run(original, func(t *testing.T) {
			// Encode
			bits, err := p.CodificarMensaje(original)
			if err != nil {
				t.Fatalf("CodificarMensaje() failed: %v", err)
			}

			// Decode
			decoded, err := p.DecodificarMensaje(bits)
			if err != nil {
				t.Fatalf("DecodificarMensaje() failed: %v", err)
			}

			if decoded != original {
				t.Errorf("Round trip failed: got %q, want %q", decoded, original)
			}
		})
	}
}

// pkg/noise/ber_test.go
package noise

import (
	"testing"
)

func TestNoiseLayer_AplicarRuido(t *testing.T) {
	n := NewNoiseLayerWithSeed(12345) // Semilla fija para tests reproducibles

	tests := []struct {
		name    string
		bits    []byte
		ber     float64
		wantErr bool
	}{
		{
			name: "zero BER",
			bits: []byte{0, 1, 0, 1, 1, 0, 1, 0},
			ber:  0.0,
		},
		{
			name: "low BER",
			bits: []byte{0, 1, 0, 1, 1, 0, 1, 0},
			ber:  0.01,
		},
		{
			name: "high BER",
			bits: []byte{0, 1, 0, 1},
			ber:  0.5,
		},
		{
			name:    "invalid BER - negative",
			bits:    []byte{0, 1},
			ber:     -0.1,
			wantErr: true,
		},
		{
			name:    "invalid BER - too high",
			bits:    []byte{0, 1},
			ber:     1.5,
			wantErr: true,
		},
		{
			name:    "invalid bits",
			bits:    []byte{0, 1, 2, 1}, // Contains '2'
			ber:     0.01,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := n.AplicarRuido(tt.bits, tt.ber)
			if (err != nil) != tt.wantErr {
				t.Errorf("AplicarRuido() error = %v, wantErr %v", err, tt.wantErr)
				return
			}

			if !tt.wantErr {
				// Verificar que el resultado tiene la estructura correcta
				if len(result.OriginalBits) != len(tt.bits) {
					t.Errorf("OriginalBits length = %d, want %d", len(result.OriginalBits), len(tt.bits))
				}
				if len(result.NoisyBits) != len(tt.bits) {
					t.Errorf("NoisyBits length = %d, want %d", len(result.NoisyBits), len(tt.bits))
				}
				if result.TotalBits != len(tt.bits) {
					t.Errorf("TotalBits = %d, want %d", result.TotalBits, len(tt.bits))
				}
				if result.ErrorsInjected != len(result.ErrorPositions) {
					t.Errorf("ErrorsInjected = %d, but ErrorPositions length = %d", 
						result.ErrorsInjected, len(result.ErrorPositions))
				}

				// Para BER=0, no debe haber errores
				if tt.ber == 0.0 && result.ErrorsInjected != 0 {
					t.Errorf("With BER=0, expected 0 errors, got %d", result.ErrorsInjected)
				}

				// Verificar que los bits son válidos
				for i, bit := range result.NoisyBits {
					if bit != 0 && bit != 1 {
						t.Errorf("Invalid bit at position %d: %d", i, bit)
					}
				}
			}
		})
	}
}

func TestNoiseLayer_ValidarConfiguracion(t *testing.T) {
	n := NewNoiseLayer()

	tests := []struct {
		name    string
		ber     float64
		bits    []byte
		wantErr bool
	}{
		{
			name: "valid config",
			ber:  0.01,
			bits: []byte{0, 1, 0, 1},
		},
		{
			name:    "invalid BER",
			ber:     -0.1,
			bits:    []byte{0, 1},
			wantErr: true,
		},
		{
			name:    "empty bits",
			ber:     0.01,
			bits:    []byte{},
			wantErr: true,
		},
		{
			name:    "invalid bits",
			ber:     0.01,
			bits:    []byte{0, 1, 3},
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := n.ValidarConfiguracion(tt.ber, tt.bits)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidarConfiguracion() error = %v, wantErr %v", err, tt.wantErr)
			}
		})
	}
}

func TestNoiseLayer_ConsistentSeed(t *testing.T) {
	seed := int64(12345)
	bits := []byte{0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1}
	ber := 0.2

	// Crear dos instancias con la misma semilla
	n1 := NewNoiseLayerWithSeed(seed)
	n2 := NewNoiseLayerWithSeed(seed)

	// Aplicar ruido con ambas instancias
	result1, err1 := n1.AplicarRuido(bits, ber)
	if err1 != nil {
		t.Fatalf("First AplicarRuido failed: %v", err1)
	}

	result2, err2 := n2.AplicarRuido(bits, ber)
	if err2 != nil {
		t.Fatalf("Second AplicarRuido failed: %v", err2)
	}

	// Los resultados deben ser idénticos
	if result1.ErrorsInjected != result2.ErrorsInjected {
		t.Errorf("ErrorsInjected differ: %d vs %d", result1.ErrorsInjected, result2.ErrorsInjected)
	}

	if len(result1.ErrorPositions) != len(result2.ErrorPositions) {
		t.Errorf("ErrorPositions length differ: %d vs %d", 
			len(result1.ErrorPositions), len(result2.ErrorPositions))
	}

	for i, pos := range result1.ErrorPositions {
		if pos != result2.ErrorPositions[i] {
			t.Errorf("ErrorPosition[%d] differ: %d vs %d", i, pos, result2.ErrorPositions[i])
		}
	}
}

// Benchmark para evaluar performance
func BenchmarkNoiseLayer_AplicarRuido(b *testing.B) {
	n := NewNoiseLayer()
	bits := make([]byte, 1000) // 1KB de bits
	for i := range bits {
		bits[i] = byte(i % 2) // Patrón alternante
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := n.AplicarRuido(bits, 0.01)
		if err != nil {
			b.Fatalf("AplicarRuido failed: %v", err)
		}
	}
}

func BenchmarkPresentationLayer_CodificarMensaje(b *testing.B) {
	p := NewPresentationLayer()
	mensaje := strings.Repeat("Hello World! ", 100) // ~1.3KB texto

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, err := p.CodificarMensaje(mensaje)
		if err != nil {
			b.Fatalf("CodificarMensaje failed: %v", err)
		}
	}
}