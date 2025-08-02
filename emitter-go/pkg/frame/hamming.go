package frame
import "fmt"

// Hamming74Encode aplica el código Hamming (7,4) a un slice de bits (0 o 1).
// Si la longitud no es múltiplo de 4, hace padding con ceros.
// Devuelve un slice de bits codificados en bloques de 7 bits.
func Hamming74Encode(dataBits []byte) ([]byte, error) {
    // Validación básica: bits solo 0 o 1
    for i, b := range dataBits {
        if b != 0 && b != 1 {
            return nil, fmt.Errorf("bit inválido en posición %d: %d (debe ser 0 o 1)", i, b)
        }
    }

    n := len(dataBits)
    numBlocks := (n + 3) / 4

    // Padding a múltiplo de 4
    padded := make([]byte, numBlocks*4)
    copy(padded, dataBits)

    // Resultado: 7 bits por bloque
    result := make([]byte, numBlocks*7)

    for i := 0; i < numBlocks; i++ {
        d3 := padded[i*4+0]
        d2 := padded[i*4+1]
        d1 := padded[i*4+2]
        d0 := padded[i*4+3]

        // Cálculo de bits de paridad
        p0 := d3 ^ d2 ^ d0           // paridad sobre posiciones 3,2,0
        p1 := d3 ^ d1 ^ d0           // paridad sobre posiciones 3,1,0
        p2 := d2 ^ d1 ^ d0           // paridad sobre posiciones 2,1,0

        // Bloque: [p2 p1 d3 p0 d2 d1 d0]
        out := []byte{p2, p1, d3, p0, d2, d1, d0}
        copy(result[i*7:(i+1)*7], out)
    }

    return result, nil
}
