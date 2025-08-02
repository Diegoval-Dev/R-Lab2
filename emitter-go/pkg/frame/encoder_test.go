package frame

import (
    "testing"
)

func TestBuildFrame_NoError(t *testing.T) {
    data := []byte{0x01, 0x02, 0x03}
    frame, err := BuildFrame(data)
    if err != nil {
        t.Fatalf("BuildFrame devolvió error: %v", err)
    }
    // Por ahora, como stub, debe devolver exactamente el payload
    if len(frame) != len(data) {
        t.Fatalf("Frame esperado longitud %d, obtenido %d", len(data), len(frame))
    }
    for i := range data {
        if frame[i] != data[i] {
            t.Fatalf("Byte en posición %d: esperado 0x%02x, hubo 0x%02x", i, data[i], frame[i])
        }
    }
}
