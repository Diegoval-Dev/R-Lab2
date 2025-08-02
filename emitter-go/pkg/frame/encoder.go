package frame

import (
    "encoding/binary"
    "hash/crc32"
    "fmt"
)

const (
    MsgTypeData byte = 0x01
)

// BuildFrame construye: [Header(2)] + Payload + [CRC(4)]
func BuildFrame(payload []byte) ([]byte, error) {
    if len(payload) > 255 {
        return nil, fmt.Errorf("payload demasiado grande: %d bytes (límite 255)", len(payload))
    }

    // 1) Header
    header := []byte{ MsgTypeData, byte(len(payload)) }

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
