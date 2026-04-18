package main

import (
	"flag"
	"fmt"

	"github.com/4w4647/GhostOps/client/internal/repl"
)

func main() {
	host   := flag.String("host", "127.0.0.1", "Operator API host")
	port   := flag.Int("port", 9090, "Operator API port")
	apiKey := flag.String("key", "", "Operator API key")
	flag.Parse()

	if *apiKey == "" {
		fmt.Println("[-] -key is required")
		return
	}

	server := fmt.Sprintf("https://%s:%d", *host, *port)
	repl.New(server, *apiKey).Run()
}
