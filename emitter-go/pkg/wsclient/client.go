package wsclient

import (
    "github.com/gorilla/websocket"
    "time"
)

// SendFrame se conecta al servidor WebSocket en url y envía la trama bytes.
func SendFrame(url string, frame []byte) error {
    // 1) Conexión
    conn, _, err := websocket.DefaultDialer.Dial(url, nil)
    if err != nil {
        return err
    }
    defer conn.Close()

    // 2) Establecer un deadline para la escritura
    conn.SetWriteDeadline(time.Now().Add(5 * time.Second))

    // 3) Enviar trama como mensaje binario
    if err := conn.WriteMessage(websocket.BinaryMessage, frame); err != nil {
        return err
    }
    return nil
}
