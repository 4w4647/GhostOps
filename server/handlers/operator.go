package handlers

import (
	"encoding/json"
	"log"
	"net/http"
	"strconv"
	"strings"

	"github.com/4w4647/GhostOps/server/store"
)

type Operator struct {
	Store *store.Store
	Log   *log.Logger
}

func (h *Operator) log() *log.Logger {
	if h.Log != nil {
		return h.Log
	}
	return log.Default()
}

func (h *Operator) List(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	list := h.Store.List()
	for _, b := range list {
		b.ComputeStale()
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(list)
}

func (h *Operator) Get(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	parts := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
	if len(parts) < 2 || parts[1] == "" {
		h.List(w, r)
		return
	}
	id64, err := strconv.ParseUint(parts[1], 10, 32)
	if err != nil {
		http.Error(w, "invalid id", http.StatusBadRequest)
		return
	}
	b, ok := h.Store.Get(uint32(id64))
	if !ok {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	b.ComputeStale()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(b)
}

func (h *Operator) Task(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, 128<<20) // 128 MB (upload payloads)
	var req struct {
		BeaconID uint32 `json:"beacon_id"`
		store.Task
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "bad request", http.StatusBadRequest)
		return
	}
	if _, ok := h.Store.Get(req.BeaconID); !ok {
		http.Error(w, "beacon not found", http.StatusNotFound)
		return
	}
	task := req.Task
	h.Store.QueueTask(req.BeaconID, &task)
	h.log().Printf("[OP] task queued  id=%-10d  type=%-10s  task=%s",
		req.BeaconID, task.Type, task.TaskID)
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"task_id": task.TaskID})
}

func (h *Operator) Results(w http.ResponseWriter, r *http.Request) {
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
	results := h.Store.GetResults(uint32(id64))
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}
