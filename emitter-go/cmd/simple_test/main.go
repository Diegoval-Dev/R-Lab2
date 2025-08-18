package main

import (
	"fmt"
	"log"
	"os"

	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/frame"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/noise"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/presentation"
	"github.com/Diegoval-Dev/R-Lab2/emitter-go/pkg/wsclient"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Println("Usage: simple_test <message> <algorithm> <ber> [ws_url]")
		fmt.Println("Example: simple_test 'Hello World' crc 0.01 ws://localhost:8765")
		os.Exit(1)
	}

	message := os.Args[1]
	algorithm := os.Args[2] 
	ber := 0.01
	wsURL := "ws://localhost:8765"

	if len(os.Args) > 3 {
		fmt.Sscanf(os.Args[3], "%f", &ber)
	}
	if len(os.Args) > 4 {
		wsURL = os.Args[4]
	}

	fmt.Printf("Testing transmission:\n")
	fmt.Printf("Message: %s\n", message)
	fmt.Printf("Algorithm: %s\n", algorithm)
	fmt.Printf("BER: %.3f\n", ber)
	fmt.Printf("WebSocket URL: %s\n\n", wsURL)

	// Initialize layers
	presentation := presentation.NewPresentationLayer()
	noiseLayer := noise.NewNoiseLayer()

	// Step 1: Convert message to bits
	textBits, err := presentation.CodificarMensaje(message)
	if err != nil {
		log.Fatal("Error encoding message:", err)
	}
	fmt.Printf("Text bits: %d bits\n", len(textBits))

	// Step 2: Build frame based on algorithm
	var frameBytes []byte
	switch algorithm {
	case "crc":
		payloadBytes := presentation.ConvertirBitsABytes(textBits)
		frameBytes, err = frame.BuildFrame(payloadBytes)
		if err != nil {
			log.Fatal("Error building CRC frame:", err)
		}
		fmt.Printf("CRC frame built: %d bytes\n", len(frameBytes))

	case "hamming":
		payloadBytes := presentation.ConvertirBitsABytes(textBits)
		frameBytes, err = frame.BuildFrameWithHamming(payloadBytes)
		if err != nil {
			log.Fatal("Error building Hamming frame:", err)
		}
		fmt.Printf("Hamming frame built: %d bytes\n", len(frameBytes))

	default:
		log.Fatal("Invalid algorithm:", algorithm)
	}

	// Step 3: Apply noise
	frameBits := presentation.ConvertirBytesABits(frameBytes)
	noiseResult, err := noiseLayer.AplicarRuido(frameBits, ber)
	if err != nil {
		log.Fatal("Error applying noise:", err)
	}
	fmt.Printf("Errors injected: %d/%d bits (BER: %.4f)\n", noiseResult.ErrorsInjected, len(frameBits), noiseResult.ActualBER)

	// Step 4: Send frame
	noisyFrameBytes := presentation.ConvertirBitsABytes(noiseResult.NoisyBits)
	fmt.Printf("Sending frame (%d bytes) to %s...\n", len(noisyFrameBytes), wsURL)
	
	err = wsclient.SendFrame(wsURL, noisyFrameBytes)
	if err != nil {
		log.Fatal("Error sending frame:", err)
	}

	fmt.Println("✅ Frame sent successfully!")
}