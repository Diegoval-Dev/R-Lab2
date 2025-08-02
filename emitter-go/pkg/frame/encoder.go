package frame

// BuildFrame recibe un payload (datos útiles) y devuelve la trama completa
// con header + payload + CRC-32 + (futura) Hamming.
func BuildFrame(payload []byte) ([]byte, error) {
    // TODO: más adelante implementaremos:
    // 1. Header
    // 2. Payload
    // 3. CRC-32
    // 4. Hamming
    return payload, nil
}
