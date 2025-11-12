package main

import (
	"testing"
)

func TestBreakEven_LocalCheaper(t *testing.T) {
	calc := &Calculator{}
	breakEven, advisory := calc.CalculateBreakEven(1.0, 2.0, 100.0)
	
	if breakEven != nil {
		t.Errorf("Expected nil break_even_hours, got %v", breakEven)
	}
	if advisory == "" {
		t.Error("Expected advisory message")
	}
	if breakEven != nil {
		t.Error("Should return nil when local is cheaper")
	}
}

func TestBreakEven_RemoteCheaper(t *testing.T) {
	calc := &Calculator{}
	breakEven, advisory := calc.CalculateBreakEven(2.0, 1.0, 100.0)
	
	if breakEven == nil {
		t.Error("Expected break_even_hours to be calculated")
	}
	if *breakEven != 100.0 {
		t.Errorf("Expected break_even_hours 100.0, got %v", *breakEven)
	}
	if advisory == "" {
		t.Error("Expected advisory message")
	}
}

func TestBreakEven_IdenticalComputeCost(t *testing.T) {
	calc := &Calculator{}
	breakEven, advisory := calc.CalculateBreakEven(2.0, 2.0, 100.0)
	
	if breakEven != nil {
		t.Errorf("Expected nil break_even_hours (division by zero prevention), got %v", breakEven)
	}
	if advisory == "" {
		t.Error("Expected advisory message")
	}
}

func TestBreakEven_NoEgressCost(t *testing.T) {
	calc := &Calculator{}
	breakEven, advisory := calc.CalculateBreakEven(2.0, 1.0, 0.0)
	
	if breakEven == nil {
		t.Error("Expected break_even_hours to be 0.0 when no egress cost")
	}
	if breakEven != nil && *breakEven != 0.0 {
		t.Errorf("Expected break_even_hours 0.0, got %v", *breakEven)
	}
	if advisory == "" {
		t.Error("Expected advisory message")
	}
}

func TestParseLocation(t *testing.T) {
	tests := []struct {
		input    string
		provider string
		service  string
		region   string
		wantErr  bool
	}{
		{"aws:s3:us-east-1", "aws", "s3", "us-east-1", false},
		{"gcp:gcs:us-central1", "gcp", "gcs", "us-central1", false},
		{"invalid", "", "", "", true},
		{"aws:s3", "", "", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			provider, service, region, err := ParseLocation(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseLocation() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if provider != tt.provider || service != tt.service || region != tt.region {
					t.Errorf("ParseLocation() = (%s, %s, %s), want (%s, %s, %s)",
						provider, service, region, tt.provider, tt.service, tt.region)
				}
			}
		})
	}
}

func TestParseInstanceKey(t *testing.T) {
	tests := []struct {
		input        string
		provider     string
		region       string
		instanceType string
		wantErr      bool
	}{
		{"aws:us-east-1:p5.48xlarge", "aws", "us-east-1", "p5.48xlarge", false},
		{"gcp:us-central1:a3-highgpu-8g", "gcp", "us-central1", "a3-highgpu-8g", false},
		{"invalid", "", "", "", true},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			provider, region, instanceType, err := ParseInstanceKey(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseInstanceKey() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr {
				if provider != tt.provider || region != tt.region || instanceType != tt.instanceType {
					t.Errorf("ParseInstanceKey() = (%s, %s, %s), want (%s, %s, %s)",
						provider, region, instanceType, tt.provider, tt.region, tt.instanceType)
				}
			}
		})
	}
}

func TestBuildEgressKey(t *testing.T) {
	tests := []struct {
		name           string
		sourceProvider string
		sourceService  string
		sourceRegion   string
		destProvider   string
		destRegion     string
		want           string
	}{
		{
			"Inter-cloud",
			"aws", "s3", "us-east-1",
			"gcp", "us-central1",
			"egress:aws:s3:us-east-1:INTERNET",
		},
		{
			"Intra-cloud",
			"aws", "s3", "us-east-1",
			"aws", "us-west-2",
			"egress:aws:s3:us-east-1:aws:us-west-2",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := BuildEgressKey(tt.sourceProvider, tt.sourceService, tt.sourceRegion, tt.destProvider, tt.destRegion)
			if got != tt.want {
				t.Errorf("BuildEgressKey() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestMapInterruptionRateToRisk(t *testing.T) {
	tests := []struct {
		rate float64
		want string
	}{
		{0.0, "LOW"},
		{4.9, "LOW"},
		{5.0, "MEDIUM"},
		{10.0, "MEDIUM"},
		{15.0, "MEDIUM"},
		{15.1, "HIGH"},
		{50.0, "HIGH"},
	}

	for _, tt := range tests {
		t.Run(tt.want, func(t *testing.T) {
			got := MapInterruptionRateToRisk(tt.rate)
			if got != tt.want {
				t.Errorf("MapInterruptionRateToRisk(%v) = %v, want %v", tt.rate, got, tt.want)
			}
		})
	}
}

