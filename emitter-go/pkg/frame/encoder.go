package frame

import (
    "encoding/binary"
    "hash/crc32"
    "fmt"

)

func BytesToBits (data []byte) []byte {
    bits := make([]byte, len(data)*8)
    for i, b := range data {
        for j := 0; j < 8; j++ {
            bits[i*8+j] = (b >> (7 - j)) & 1
        }
    }
    return bits
}

func BitsToBytes(bits []byte) []byte {
    if len(bits) == 0 {
        return []byte{}
    }
    // Asegurarse de que la longitud es múltiplo de 8
    if len(bits)%8 != 0 {
        padding := make([]byte, 8-len(bits)%8)
        bits = append(bits, padding...)
    }
    out := make([]byte, len(bits)/8)
    for i := 0; i < len(bits); i += 8 {
        var b byte
        for j := 0; j < 8; j++ {
            b |= bits[i+j] << (7 - j)
        }
        out[i/8] = b
    }
    return out
}

const (
    MsgTypeData byte = 0x01
)

// BuildFrame construye: [Header(2)] + Payload + [CRC(4)]
func BuildFrame(payload []byte) ([]byte, error) {
    if len(payload) > 255 {
        return nil, fmt.Errorf("payload demasiado grande: %d bytes (límite 255)", len(payload))
    }

    // 1) Header
    header := make([]byte, 3)
    header[0] = MsgTypeData // Tipo de mensaje
    binary.BigEndian.PutUint16(header[1:], uint16(len(payload)))

    // 2) Concat header + payload
    frame := append(header, payload...)

    // 3) Calcular CRC-32 sobre header+payload
    crc := crc32.ChecksumIEEE(frame)
    // 4) Añadir 4 bytes Big-Endian con el CRC
    crcBytes := make([]byte, 4)
    binary.BigEndian.PutUint32(crcBytes, crc)

    // 5) Trama final
    fullFrame := append(frame, crcBytes...)
    return fullFrame, nil
}

func BuildFrameWithHamming(payload []byte) ([]byte, error) {
    // 1) convertir payload en slice de bits (0/1)
    bits := BytesToBits(payload)
    // 2) codificar con Hamming
    codeBits, err := Hamming74Encode(bits)
    if err != nil {
        return nil, err
    }
    // 3) convertir bits de vuelta a bytes (agrupando de 8)
    codedBytes := BitsToBytes(codeBits)
    // 4) llamar a BuildFrame(codedBytes) para añadir header+CRC
    return BuildFrame(codedBytes)
}




