package main

// JobData represents the data location and size
type JobData struct {
	Location string  `json:"location"` // Format: provider:service:region (e.g., "aws:s3:us-east-1")
	SizeGB   float64 `json:"size_gb"`
}

// JobCompute represents compute requirements
type JobCompute struct {
	GPUType       string  `json:"gpu_type"`        // Required: e.g., "H100"
	GPUCount      int     `json:"gpu_count"`        // Required: e.g., 8
	GPUMemoryGB   *int    `json:"gpu_memory_gb"`    // Optional: e.g., 80
	Interconnect  *string `json:"interconnect"`     // Optional: e.g., "infiniband"
}

// JobOutput represents output location (for MVP 3, ignored in MVP 1)
type JobOutput struct {
	Location string `json:"location"` // Format: provider:service:region
	Path     string `json:"path"`     // Storage path (e.g., "s3://bucket/path/")
}

// JobRequest represents the incoming analysis request
type JobRequest struct {
	JobName string      `json:"job_name"`
	Data    JobData     `json:"data"`
	Compute JobCompute  `json:"compute"`
	Output  *JobOutput  `json:"output,omitempty"` // Optional, ignored in MVP 1
}

// AnalysisOption represents a single compute option analysis
type AnalysisOption struct {
	Provider          string   `json:"provider"`
	Region            string   `json:"region"`
	InstanceType      string   `json:"instance_type,omitempty"`
	ComputeCostPerHour float64 `json:"compute_cost_per_hour"`
	OneTimeEgressCost float64  `json:"one_time_egress_cost"`
	BreakEvenHours    *float64 `json:"break_even_hours"` // nil if not applicable
	AdvisoryMessage   string   `json:"advisory_message"`
	IsSpotInstance    bool     `json:"is_spot_instance"`
	InterruptionRisk   *string  `json:"interruption_risk,omitempty"` // "LOW", "MEDIUM", "HIGH", or nil
}

// AnalysisResponse represents the complete analysis result
type AnalysisResponse struct {
	DataLocalOption AnalysisOption   `json:"data_local_option"`
	RemoteOptions   []AnalysisOption `json:"remote_options"`
}

// ComputePrice represents a compute price entry from Redis
type ComputePrice struct {
	Provider      string  `json:"provider"`
	Region        string  `json:"region"`
	InstanceType  string  `json:"instance_type"`
	CostPerHour   float64 `json:"cost_per_hour"`
	GPUCount      int     `json:"gpu_count"`
	GPUMemoryGB   *int    `json:"gpu_memory_gb,omitempty"`
	Interconnect  *string `json:"interconnect,omitempty"`
}

// EgressPrice represents an egress price entry from Redis
type EgressPrice struct {
	CostPerGB float64 `json:"cost_per_gb"`
}

