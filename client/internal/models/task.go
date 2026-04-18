package models

import "time"

type Task struct {
	TaskID string `json:"task_id"`
	Type   string `json:"type"`
	Args   string `json:"args,omitempty"`
	Data   string `json:"data,omitempty"`
}

type TaskRequest struct {
	BeaconID uint32 `json:"beacon_id"`
	Task
}

type TaskResult struct {
	TaskID   string    `json:"task_id"`
	BeaconID uint32    `json:"beacon_id"`
	Output   string    `json:"output"`
	Error    string    `json:"error"`
	At       time.Time `json:"at"`
}
