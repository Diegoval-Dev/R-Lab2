package main

import (
    "fmt"
    "os"

    "github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/frame"
    "github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/wsclient"
)

func main() {
    // Payload de ejemplo
    payload := []byte("¡Hola mundo!")

    // Construir trama
    fullFrame, err := frame.BuildFrame(payload)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error construyendo la trama: %v\n", err)
        os.Exit(1)
    }

    // Enviar al receptor
    wsURL := "ws://localhost:9000"
    if err := wsclient.SendFrame(wsURL, fullFrame); err != nil {
        fmt.Fprintf(os.Stderr, "Error enviando la trama: %v\n", err)
        os.Exit(1)
    }

    fmt.Println("Trama enviada con éxito")
}
