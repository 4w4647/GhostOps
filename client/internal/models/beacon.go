package models

import "time"

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
