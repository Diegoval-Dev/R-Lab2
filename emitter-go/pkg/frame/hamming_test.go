package frame

import "testing"

func TestHamming74Encode_SingleBlock(t *testing.T) {
    // Datos de prueba: 4 bits
    data := []byte{1, 0, 1, 1} // d3=1,d2=0,d1=1,d0=1
    // p0 = 1^0^1 = 0; p1 = 1^1^1 = 1; p2 = 0^1^1 = 0
    want := []byte{0, 1, 1, 0, 0, 1, 1}

    got, err := Hamming74Encode(data)
    if err != nil {
        t.Fatalf("Error inesperado: %v", err)
    }
    if len(got) != 7 {
        t.Fatalf("Longitud esperada 7, obtuvo %d", len(got))
    }
    for i := range want {
        if got[i] != want[i] {
            t.Errorf("Byte %d: esperado %d, obtuvo %d", i, want[i], got[i])
        }
    }
}

func TestHamming74Encode_Padding(t *testing.T) {
    // 6 bits → 2 bloques (padding a 8 bits)
    data := []byte{1, 1, 0, 1, 0, 1} // 6 bits
    got, err := Hamming74Encode(data)
    if err != nil {
        t.Fatalf("Error inesperado: %v", err)
    }
    // Debe codificar 2 bloques → 14 bits
    if len(got) != 14 {
        t.Errorf("Para 6 bits esperados 14 bits codificados, obtuvo %d", len(got))
    }
}
