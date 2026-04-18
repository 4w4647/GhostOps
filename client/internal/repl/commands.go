package repl

import (
	"encoding/base64"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/4w4647/GhostOps/client/internal/display"
	"github.com/4w4647/GhostOps/client/internal/models"
)

func cmdHelp() {
	fmt.Printf(`%sCommands:%s
  %-30s list all checked-in beacons
  %-30s select a beacon by ID
  %-30s show full details of selected beacon
  %-30s run a shell command on the active beacon
  %-30s change beacon sleep interval
  %-30s terminate the active beacon
  %-30s download a file from the beacon
  %-30s upload a local file to the beacon
  %-30s show new task results  (-a = show all)
  %-30s deselect current beacon
  %-30s show this help
  %-30s exit

`,
		display.Bold, display.Reset,
		"beacons",
		"use <id>",
		"info",
		"shell <cmd>",
		"sleep <ms> [jitter%]",
		"kill",
		"download <remote> [local]",
		"upload <local> <remote>",
		"tasks [-a]",
		"back",
		"help",
		"exit",
	)
}

func (r *REPL) cmdBeacons() {
	var beacons []models.BeaconInfo
	if err := r.Fetch("/beacons", &beacons); err != nil {
		fmt.Printf("%s[-]%s %v\n", display.Red, display.Reset, err)
		return
	}
	if len(beacons) == 0 {
		fmt.Printf("%s[*]%s no beacons\n", display.Yellow, display.Reset)
		return
	}
	r.markSeen(beacons)

	headers := []string{"ID", "USER", "HOSTNAME", "PID", "PROCESS", "ARCH", "INTEGRITY", "EXTERNAL IP", "LAST SEEN", "OS", "STATUS"}

	rows := make([][]string, len(beacons))
	meta := make([]struct {
		elevated, stale bool
		integLevel      uint32
	}, len(beacons))

	for i, b := range beacons {
		user := b.Domain + `\` + b.Username
		if b.IsElevated {
			user = "*" + user
		}
		status := "alive"
		if b.Stale {
			status = "dead"
		}
		rows[i] = []string{
			fmt.Sprintf("%d", b.BeaconID),
			user,
			b.Hostname,
			fmt.Sprintf("%d", b.PID),
			b.ProcessName,
			b.Arch,
			display.IntegrityText(b.IntegrityLevel),
			b.EIP,
			display.Since(b.LastSeen),
			display.ShortOS(b.OsBuild),
			status,
		}
		meta[i] = struct {
			elevated, stale bool
			integLevel      uint32
		}{b.IsElevated, b.Stale, b.IntegrityLevel}
	}

	widths := make([]int, len(headers))
	for i, h := range headers {
		widths[i] = len(h)
	}
	for _, row := range rows {
		for i, cell := range row {
			widths[i] = display.MaxLen(widths[i], len(cell))
		}
	}

	sep := "  "
	total := 0
	for _, w := range widths {
		total += w
	}
	total += len(sep) * (len(widths) - 1)

	fmt.Println()
	fmt.Print(display.Bold)
	for i, h := range headers {
		fmt.Printf("%-*s", widths[i], h)
		if i < len(headers)-1 {
			fmt.Print(sep)
		}
	}
	fmt.Printf("%s\n", display.Reset)
	fmt.Println(strings.Repeat("─", total))

	for i, row := range rows {
		m := meta[i]
		for j, cell := range row {
			colored := cell
			extra := 0
			switch j {
			case 1:
				if m.elevated {
					colored = display.Yellow + cell + display.Reset
					extra = display.ColorWidth()
				}
			case 6:
				colored = display.IntegrityColor(m.integLevel)
				extra = display.ColorWidth()
			case 8:
				if m.stale {
					colored = display.Red + cell + display.Reset
					extra = display.ColorWidth()
				}
			case 10:
				if m.stale {
					colored = display.Red + cell + display.Reset
				} else {
					colored = display.Green + cell + display.Reset
				}
				extra = display.ColorWidth()
			}
			fmt.Printf("%-*s", widths[j]+extra, colored)
			if j < len(row)-1 {
				fmt.Print(sep)
			}
		}
		fmt.Println()
	}
	fmt.Println()
}

func (r *REPL) cmdUse(args []string) {
	if len(args) == 0 {
		fmt.Printf("%s[-]%s usage: use <beacon_id>\n", display.Red, display.Reset)
		return
	}
	id64, err := strconv.ParseUint(args[0], 10, 32)
	if err != nil {
		fmt.Printf("%s[-]%s invalid id\n", display.Red, display.Reset)
		return
	}
	var b models.BeaconInfo
	if err := r.Fetch(fmt.Sprintf("/beacons/%d", id64), &b); err != nil {
		fmt.Printf("%s[-]%s beacon not found\n", display.Red, display.Reset)
		return
	}
	r.Active = &b
	fmt.Printf("%s[*]%s selected %s%s%s (%s)\n",
		display.Green, display.Reset, display.Bold, b.Hostname, display.Reset, b.EIP)
}

func (r *REPL) cmdInfo() {
	if r.Active == nil {
		fmt.Printf("%s[-]%s no beacon selected — use: use <id>\n", display.Red, display.Reset)
		return
	}

	var b models.BeaconInfo
	if err := r.Fetch(fmt.Sprintf("/beacons/%d", r.Active.BeaconID), &b); err == nil {
		r.Active = &b
	}
	b = *r.Active

	kv := func(label, value string) {
		fmt.Printf("  %s%-14s%s %s\n", display.Bold, label, display.Reset, value)
	}
	section := func(name string) {
		fmt.Printf("\n  %s%s── %s%s\n", display.Bold, display.Cyan, name, display.Reset)
	}

	staleWarn := ""
	if b.Stale {
		staleWarn = "  " + display.Red + display.Bold + "[DEAD - missed 3+ check-ins]" + display.Reset
	}

	fmt.Println()
	fmt.Printf("  %s%s── Beacon%s%s\n", display.Bold, display.Cyan, display.Reset, staleWarn)
	kv("ID", fmt.Sprintf("%d", b.BeaconID))
	kv("First Seen", b.FirstSeen.Format(time.RFC1123))
	kv("Last Seen", fmt.Sprintf("%s (%s)", b.LastSeen.Format(time.RFC1123), display.Since(b.LastSeen)))
	kv("Sleep", fmt.Sprintf("%dms  jitter: %d%%", b.SleepMs, b.JitterPct))

	section("Identity")
	kv("User", fmt.Sprintf("%s\\%s", b.Domain, b.Username))
	kv("Hostname", b.Hostname)
	kv("Domain", fmt.Sprintf("%s  joined: %s", b.Domain, display.BoolColor(b.IsDomainJoined, "yes", "no")))

	section("System")
	kv("OS", fmt.Sprintf("%s  (build %d)", display.ShortOS(b.OsBuild), b.OsBuild))
	kv("Arch", fmt.Sprintf("%s  64-bit proc: %s", b.Arch, display.BoolColor(b.Is64BitProc, "yes", "no")))

	section("Process")
	kv("Name", b.ProcessName)
	kv("PID", fmt.Sprintf("%d  ppid: %d", b.PID, b.PPID))
	kv("Integrity", display.IntegrityColor(b.IntegrityLevel))
	kv("Elevated", display.BoolColor(b.IsElevated, "yes", "no"))
	kv("Session", fmt.Sprintf("%d", b.SessionID))

	section("Network")
	kv("External", b.EIP)

	if len(b.Adapters) > 0 {
		wName, wIP, wMAC := len("ADAPTER"), len("IP"), len("MAC")
		for _, a := range b.Adapters {
			wName = display.MaxLen(wName, len(a.Name))
			wIP = display.MaxLen(wIP, len(a.IP))
			wMAC = display.MaxLen(wMAC, len(a.MAC))
		}
		total := 4 + 2 + wName + 2 + wIP + 2 + wMAC
		fmt.Println()
		fmt.Printf("  %s%-4s  %-*s  %-*s  %-*s%s\n",
			display.Bold, "#", wName, "ADAPTER", wIP, "IP", wMAC, "MAC", display.Reset)
		fmt.Printf("  %s\n", strings.Repeat("─", total))
		for i, a := range b.Adapters {
			fmt.Printf("  %-4d  %-*s  %-*s  %-*s\n", i+1, wName, a.Name, wIP, a.IP, wMAC, a.MAC)
		}
	}
	fmt.Println()
}

func (r *REPL) requireActive() bool {
	if r.Active == nil {
		fmt.Printf("%s[-]%s no beacon selected — use: use <id>\n", display.Red, display.Reset)
		return false
	}
	return true
}

func (r *REPL) waitAndGet(taskID string) *models.TaskResult {
	timeout := time.Duration(r.Active.SleepMs)*4*time.Millisecond + 15*time.Second
	deadline := time.Now().Add(timeout)

	fmt.Printf("%s[*]%s waiting", display.Yellow, display.Reset)
	for time.Now().Before(deadline) {
		time.Sleep(500 * time.Millisecond)
		fmt.Print(".")

		var results []models.TaskResult
		if err := r.Fetch(fmt.Sprintf("/results/%d", r.Active.BeaconID), &results); err != nil {
			continue
		}
		for idx, res := range results {
			if res.TaskID != taskID {
				continue
			}
			fmt.Println()
			if idx+1 > r.taskCursor[r.Active.BeaconID] {
				r.taskCursor[r.Active.BeaconID] = idx + 1
			}
			return &results[idx]
		}
	}
	fmt.Printf("\n%s[-]%s timed out — check tasks manually\n", display.Red, display.Reset)
	return nil
}

func (r *REPL) waitForResult(taskID string) bool {
	res := r.waitAndGet(taskID)
	if res == nil {
		return false
	}
	if res.Error != "" {
		fmt.Printf("%s[err]%s %s\n", display.Red, display.Reset, res.Error)
	}
	if res.Output != "" {
		fmt.Println(res.Output)
	}
	return true
}

func (r *REPL) queueTask(t models.Task) (string, bool) {
	req := models.TaskRequest{BeaconID: r.Active.BeaconID, Task: t}
	var resp map[string]string
	if err := r.Post("/task", req, &resp); err != nil {
		fmt.Printf("%s[-]%s %v\n", display.Red, display.Reset, err)
		return "", false
	}
	return resp["task_id"], true
}

func (r *REPL) cmdShell(args []string) {
	if !r.requireActive() {
		return
	}
	if len(args) == 0 {
		fmt.Printf("%s[-]%s usage: shell <command>\n", display.Red, display.Reset)
		return
	}
	taskID, ok := r.queueTask(models.Task{Type: "shell", Args: strings.Join(args, " ")})
	if !ok {
		return
	}
	r.waitForResult(taskID)
}

func (r *REPL) cmdSleep(args []string) {
	if !r.requireActive() {
		return
	}
	if len(args) == 0 {
		fmt.Printf("%s[-]%s usage: sleep <ms> [jitter%%]\n", display.Red, display.Reset)
		return
	}
	ms, err := strconv.ParseUint(args[0], 10, 32)
	if err != nil {
		fmt.Printf("%s[-]%s invalid ms value\n", display.Red, display.Reset)
		return
	}
	jitter := uint64(r.Active.JitterPct)
	if len(args) > 1 {
		jitter, err = strconv.ParseUint(args[1], 10, 32)
		if err != nil {
			fmt.Printf("%s[-]%s invalid jitter value\n", display.Red, display.Reset)
			return
		}
	}
	taskID, ok := r.queueTask(models.Task{
		Type: "sleep",
		Args: fmt.Sprintf("%d %d", ms, jitter),
	})
	if !ok {
		return
	}
	r.waitForResult(taskID)
}

func (r *REPL) cmdKill() {
	if !r.requireActive() {
		return
	}
	taskID, ok := r.queueTask(models.Task{Type: "exit"})
	if !ok {
		return
	}
	fmt.Printf("%s[*]%s kill tasked (%s) — beacon will exit on next check-in\n",
		display.Yellow, display.Reset, taskID)
}

func (r *REPL) cmdDownload(args []string) {
	if !r.requireActive() {
		return
	}
	if len(args) == 0 {
		fmt.Printf("%s[-]%s usage: download <remote_path> [local_path]\n", display.Red, display.Reset)
		return
	}
	remotePath := args[0]
	localPath := filepath.Base(remotePath)
	if len(args) > 1 {
		localPath = args[1]
	}

	taskID, ok := r.queueTask(models.Task{Type: "download", Args: remotePath})
	if !ok {
		return
	}

	res := r.waitAndGet(taskID)
	if res == nil {
		return
	}
	if res.Error != "" {
		fmt.Printf("%s[err]%s %s\n", display.Red, display.Reset, res.Error)
		return
	}
	if res.Output == "" {
		fmt.Printf("%s[-]%s empty response\n", display.Red, display.Reset)
		return
	}

	data, err := base64.StdEncoding.DecodeString(res.Output)
	if err != nil {
		fmt.Printf("%s[-]%s base64 decode failed: %v\n", display.Red, display.Reset, err)
		return
	}
	if err := os.WriteFile(localPath, data, 0600); err != nil {
		fmt.Printf("%s[-]%s write failed: %v\n", display.Red, display.Reset, err)
		return
	}
	fmt.Printf("%s[+]%s saved %d bytes → %s\n", display.Green, display.Reset, len(data), localPath)
}

func (r *REPL) cmdUpload(args []string) {
	if !r.requireActive() {
		return
	}
	if len(args) < 2 {
		fmt.Printf("%s[-]%s usage: upload <local_path> <remote_path>\n", display.Red, display.Reset)
		return
	}
	localPath := args[0]
	remotePath := args[1]

	data, err := os.ReadFile(localPath)
	if err != nil {
		fmt.Printf("%s[-]%s cannot read file: %v\n", display.Red, display.Reset, err)
		return
	}

	encoded := base64.StdEncoding.EncodeToString(data)
	taskID, ok := r.queueTask(models.Task{
		Type: "upload",
		Args: remotePath,
		Data: encoded,
	})
	if !ok {
		return
	}
	fmt.Printf("%s[*]%s sending %d bytes\n", display.Yellow, display.Reset, len(data))
	r.waitForResult(taskID)
}

func (r *REPL) cmdTasks(args []string) {
	if !r.requireActive() {
		return
	}

	showAll := len(args) > 0 && args[0] == "-a"

	var results []models.TaskResult
	if err := r.Fetch(fmt.Sprintf("/results/%d", r.Active.BeaconID), &results); err != nil {
		fmt.Printf("%s[-]%s %v\n", display.Red, display.Reset, err)
		return
	}

	var unseen []models.TaskResult
	if showAll {
		unseen = results
	} else {
		cursor := r.taskCursor[r.Active.BeaconID]
		unseen = results[cursor:]
	}

	if len(unseen) == 0 {
		fmt.Printf("%s[*]%s no new results\n", display.Yellow, display.Reset)
		return
	}

	for _, res := range unseen {
		fmt.Printf("\n%s── task %s%s  [%s]\n",
			display.Bold+display.Cyan, res.TaskID, display.Reset,
			res.At.Format(time.RFC3339))
		if res.Error != "" {
			fmt.Printf("%s[err]%s %s\n", display.Red, display.Reset, res.Error)
		}
		if res.Output != "" {
			fmt.Println(res.Output)
		}
	}
	fmt.Println()

	if !showAll {
		r.taskCursor[r.Active.BeaconID] = len(results)
	}
}
