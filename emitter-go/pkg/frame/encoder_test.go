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
    // Longitud total: 3 (header) + 2 (payload) + 4 (CRC) = 9
    if len(frame) != 9 {
        t.Fatalf("Longitud esperada 9, obtenida %d", len(frame))
    }
    // Header
    if frame[0] != MsgTypeData {
        t.Errorf("Byte 0 header: esperado %02x, tuvo %02x", MsgTypeData, frame[0])
    }
    plen := binary.BigEndian.Uint16(frame[1:3])
    if int(plen) != len(data) {
        t.Errorf("Longitud en header: esperado %d, tuvo %d", len(data), plen)
    }
    // CRC
    gotCRC := binary.BigEndian.Uint32(frame[len(frame)-4:])
    wantCRC := crc32.ChecksumIEEE(frame[:len(frame)-4])
    if gotCRC != wantCRC {
        t.Errorf("CRC inválido: esperado %08x, obtuvo %08x", wantCRC, gotCRC)
    }
}

func TestBuildFrameWithHamming_RoundTrip(t *testing.T) {
    payload := []byte{0xFF, 0x00}
    frame, err := BuildFrameWithHamming(payload)
    if err != nil {
        t.Fatalf("error inesperado: %v", err)
    }
    if frame[0] != MsgTypeData {
        t.Errorf("header tipo: esperado %02x, obtuvo %02x", MsgTypeData, frame[0])
    }
    // CRC válido
    gotCRC := binary.BigEndian.Uint32(frame[len(frame)-4:])
    wantCRC := crc32.ChecksumIEEE(frame[:len(frame)-4])
    if gotCRC != wantCRC {
        t.Errorf("CRC inválido tras Hamming: %08x vs %08x", wantCRC, gotCRC)
    }
    // La longitud del header (uint16 BE) debe coincidir con el body real
    plen := int(binary.BigEndian.Uint16(frame[1:3]))
    bodyLen := len(frame) - (3 /*header*/ + 4 /*CRC*/)
    if plen != bodyLen {
        t.Errorf("longitud de payload mal codificada: header dice %d, pero body mide %d", plen, bodyLen)
    }
}
