package store

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"os"
	"sync"
	"time"
)

type AdapterInfo struct {
	Name string `json:"name"`
	IP   string `json:"ip"`
	MAC  string `json:"mac"`
}

type BeaconInfo struct {
	BeaconID       uint32        `json:"beacon_id"`
	SleepMs        uint32        `json:"sleep_ms"`
	JitterPct      uint32        `json:"jitter_pct"`
	EIP            string        `json:"eip"`
	Adapters       []AdapterInfo `json:"adapters"`
	OsVersion      string        `json:"os_version"`
	OsBuild        uint32        `json:"os_build"`
	Arch           string        `json:"arch"`
	ProcessName    string        `json:"process_name"`
	PID            uint32        `json:"pid"`
	PPID           uint32        `json:"ppid"`
	Is64BitProc    bool          `json:"is_64bit_proc"`
	IntegrityLevel uint32        `json:"integrity_level"`
	IsElevated     bool          `json:"is_elevated"`
	Username       string        `json:"username"`
	Hostname       string        `json:"hostname"`
	Domain         string        `json:"domain"`
	IsDomainJoined bool          `json:"is_domain_joined"`
	SessionID      uint32        `json:"session_id"`
	LastSeen       time.Time     `json:"last_seen"`
	FirstSeen      time.Time     `json:"first_seen"`
	Stale          bool          `json:"stale"`
}

func (b *BeaconInfo) ComputeStale() {
	b.Stale = time.Since(b.LastSeen) > time.Duration(b.SleepMs*3)*time.Millisecond
}

type Task struct {
	TaskID string `json:"task_id"`
	Type   string `json:"type"`
	Args   string `json:"args,omitempty"`
	Data   string `json:"data,omitempty"`
}

type TaskResult struct {
	TaskID   string    `json:"task_id"`
	BeaconID uint32    `json:"beacon_id"`
	Output   string    `json:"output"`
	Error    string    `json:"error"`
	At       time.Time `json:"at"`
}

type Store struct {
	mu      sync.RWMutex
	beacons map[uint32]*BeaconInfo
	pending map[uint32][]*Task
	results map[uint32][]*TaskResult
	path    string
}

type persistedState struct {
	Beacons map[uint32]*BeaconInfo   `json:"beacons"`
	Results map[uint32][]*TaskResult `json:"results"`
}

func New() *Store {
	return &Store{
		beacons: make(map[uint32]*BeaconInfo),
		pending: make(map[uint32][]*Task),
		results: make(map[uint32][]*TaskResult),
	}
}

func Load(path string) (*Store, error) {
	s := New()
	s.path = path

	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return s, nil
	}
	if err != nil {
		return nil, err
	}

	var state persistedState
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, err
	}
	if state.Beacons != nil {
		s.beacons = state.Beacons
	}
	if state.Results != nil {
		s.results = state.Results
	}
	return s, nil
}

func (s *Store) save() {
	if s.path == "" {
		return
	}
	state := persistedState{
		Beacons: s.beacons,
		Results: s.results,
	}
	data, err := json.Marshal(state)
	if err != nil {
		return
	}
	os.WriteFile(s.path, data, 0600)
}

func newTaskID() string {
	b := make([]byte, 8)
	rand.Read(b)
	return hex.EncodeToString(b)
}

func (s *Store) Upsert(b *BeaconInfo) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if existing, ok := s.beacons[b.BeaconID]; ok {
		b.FirstSeen = existing.FirstSeen
	} else {
		b.FirstSeen = b.LastSeen
	}
	s.beacons[b.BeaconID] = b
	s.save()
}

func (s *Store) List() []*BeaconInfo {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]*BeaconInfo, 0, len(s.beacons))
	for _, b := range s.beacons {
		out = append(out, b)
	}
	return out
}

func (s *Store) Get(id uint32) (*BeaconInfo, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	b, ok := s.beacons[id]
	return b, ok
}

func (s *Store) QueueTask(beaconID uint32, t *Task) {
	if t.TaskID == "" {
		t.TaskID = newTaskID()
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.pending[beaconID] = append(s.pending[beaconID], t)
}

func (s *Store) PollTasks(beaconID uint32) []*Task {
	s.mu.Lock()
	defer s.mu.Unlock()
	tasks := s.pending[beaconID]
	s.pending[beaconID] = nil
	if tasks == nil {
		return []*Task{}
	}
	return tasks
}

func (s *Store) SubmitResult(r *TaskResult) {
	r.At = time.Now()
	s.mu.Lock()
	defer s.mu.Unlock()
	s.results[r.BeaconID] = append(s.results[r.BeaconID], r)
	s.save()
}

func (s *Store) GetResults(beaconID uint32) []*TaskResult {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := s.results[beaconID]
	if out == nil {
		return []*TaskResult{}
	}
	return out
}
