package frame

import (
    "testing"
		"encoding/binary"
		"hash/crc32"
)

func TestBuildFrame_CRCAndHeader(t *testing.T) {
    data := []byte{0x0A, 0x0B}
    frame, err := BuildFrame(data)
    if err != nil {
        t.Fatal(err)
    }
    // Longitud: 2 + 2 + 4 = 8
    if len(frame) != 8 {
        t.Fatalf("Longitud esperada 8, obtenida %d", len(frame))
    }
    // Header
    if frame[0] != MsgTypeData {
        t.Errorf("Byte 0 header: esperado %02x, tuvo %02x", MsgTypeData, frame[0])
    }
    if frame[1] != byte(len(data)) {
        t.Errorf("Byte 1 header (longitud): esperado %d, tuvo %d", len(data), frame[1])
    }
    // CRC
    gotCRC := binary.BigEndian.Uint32(frame[len(frame)-4:])
    wantCRC := crc32.ChecksumIEEE(frame[:len(frame)-4])
    if gotCRC != wantCRC {
        t.Errorf("CRC inválido: esperado %08x, obtuvo %08x", wantCRC, gotCRC)
    }
}

func TestBuildFrameWithHamming_RoundTrip(t *testing.T) {
    // payload pequeño
    payload := []byte{0xFF, 0x00}
    frame, err := BuildFrameWithHamming(payload)
    if err != nil {
        t.Fatalf("error inesperado: %v", err)
    }
    // Compruebo que BuildFrame (header+CRC) aceptó el código Hamming
    // Header: tipo + longitud
    if frame[0] != MsgTypeData {
        t.Errorf("header tipo: esperado %02x, obtuvo %02x", MsgTypeData, frame[0])
    }
    // CRC válido?
    gotCRC := binary.BigEndian.Uint32(frame[len(frame)-4:])
    wantCRC := crc32.ChecksumIEEE(frame[:len(frame)-4])
    if gotCRC != wantCRC {
        t.Errorf("CRC inválido tras Hamming: %08x vs %08x", wantCRC, gotCRC)
    }
    // Y la longitud del header debe coincidir con len(frame)-6 (header+CRC)
    if int(frame[1]) != len(frame)-6 {
        t.Errorf("longitud de payload mal codificada: header dice %d, pero body mide %d",
            frame[1], len(frame)-6)
    }
}
