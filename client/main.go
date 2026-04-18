package main

import (
	"flag"
	"fmt"

	"github.com/4w4647/GhostOps/client/internal/repl"
)

func main() {
	host := flag.String("host", "127.0.0.1", "Operator API host")
	port := flag.Int("port", 9090, "Operator API port")
	flag.Parse()

	server := fmt.Sprintf("http://%s:%d", *host, *port)
	repl.New(server).Run()
}
