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

	"github.com/4w4647/GhostOps/client/internal/banner"
	"github.com/4w4647/GhostOps/client/internal/display"
	"github.com/4w4647/GhostOps/client/internal/models"
)

type REPL struct {
	Server     string
	APIKey     string
	Active     *models.BeaconInfo
	client     *http.Client
	scanner    *bufio.Scanner
	taskCursor map[uint32]int
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
		scanner:    bufio.NewScanner(os.Stdin),
		taskCursor: make(map[uint32]int),
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

func (r *REPL) Run() {
	banner.Print()
	cmdHelp()

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
