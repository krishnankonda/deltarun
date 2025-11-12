package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"time"
)

// SpotClient handles AWS Spot Price API queries
type SpotClient struct {
	httpClient *http.Client
}

func NewSpotClient() *SpotClient {
	return &SpotClient{
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

// SpotPriceResponse represents AWS Spot Price API response
type SpotPriceResponse struct {
	SpotPriceHistory []struct {
		InstanceType string  `json:"InstanceType"`
		SpotPrice    string  `json:"SpotPrice"`
		AvailabilityZone string `json:"AvailabilityZone"`
	} `json:"SpotPriceHistory"`
}

// SpotAdvisorResponse represents interruption rate (simplified - actual API may differ)
type SpotAdvisorResponse struct {
	InterruptionRate float64 `json:"interruption_rate"` // Percentage (0-100)
}

// GetSpotPrice gets the current spot price for an instance type in a region
func (s *SpotClient) GetSpotPrice(instanceType, region string) (*float64, error) {
	// For MVP 1, we'll use a mock/simplified approach
	// In production, this would call: https://ec2.amazonaws.com/?Action=DescribeSpotPriceHistory
	
	// Mock implementation: Return a price that's 50% of on-demand (typical spot discount)
	// This is a placeholder - actual implementation would query AWS API
	log.Printf("INFO: Spot price query for %s in %s (mock implementation)", instanceType, region)
	
	// Return nil to indicate graceful degradation should occur
	// In real implementation, this would make HTTP request to AWS API
	return nil, fmt.Errorf("spot price API not implemented in MVP 1 (mock)")
}

// GetInterruptionRate gets the interruption rate for an instance type
func (s *SpotClient) GetInterruptionRate(instanceType, region string) (*float64, error) {
	// Mock implementation - actual would query Spot Instance Advisor API
	log.Printf("INFO: Interruption rate query for %s in %s (mock implementation)", instanceType, region)
	
	// Return nil to indicate graceful degradation
	return nil, fmt.Errorf("interruption rate API not implemented in MVP 1 (mock)")
}

// MapInterruptionRateToRisk maps a percentage to risk level
func MapInterruptionRateToRisk(rate float64) string {
	if rate < 5 {
		return "LOW"
	} else if rate <= 15 {
		return "MEDIUM"
	}
	return "HIGH"
}

// AnalyzeSpotOption analyzes a spot instance option with graceful degradation
func (s *SpotClient) AnalyzeSpotOption(
	instanceKey string,
	sourceProvider, sourceService, sourceRegion string,
	localCostPerHour float64,
	dataSizeGB float64,
	onDemandCostPerHour float64,
	calculator *Calculator,
) (*AnalysisOption, error) {
	provider, region, instanceType, err := ParseInstanceKey(instanceKey)
	if err != nil {
		return nil, fmt.Errorf("invalid instance key: %w", err)
	}

	// Only support AWS spot instances for MVP 1
	if provider != "aws" {
		return nil, nil // Skip non-AWS instances
	}

	// Try to get spot price
	spotPrice, err := s.GetSpotPrice(instanceType, region)
	if err != nil {
		// Graceful degradation: fall back to on-demand
		log.Printf("WARNING: Spot price unavailable for %s, using on-demand price", instanceKey)
		spotPrice = &onDemandCostPerHour
	}

	// Try to get interruption rate
	interruptionRate, err := s.GetInterruptionRate(instanceType, region)
	var interruptionRisk *string
	if err == nil && interruptionRate != nil {
		risk := MapInterruptionRateToRisk(*interruptionRate)
		interruptionRisk = &risk
	}

	// Get egress price
	egressKey := BuildEgressKey(sourceProvider, sourceService, sourceRegion, provider, region)
	egressPrice, err := calculator.redis.GetEgressPrice(egressKey)
	if err != nil || egressPrice == nil {
		return nil, nil // Silently omit
	}

	oneTimeEgressCost := egressPrice.CostPerGB * dataSizeGB

	// Calculate break-even
	breakEvenHours, advisory := calculator.CalculateBreakEven(localCostPerHour, *spotPrice, oneTimeEgressCost)
	
	// Update advisory if using on-demand fallback
	if spotPrice != nil && *spotPrice == onDemandCostPerHour {
		advisory = "(Spot price unavailable; using on-demand. Spot may be cheaper.) " + advisory
	}

	option := &AnalysisOption{
		Provider:          provider,
		Region:            region,
		InstanceType:      instanceType + " (SPOT INSTANCE)",
		ComputeCostPerHour: *spotPrice,
		OneTimeEgressCost:  oneTimeEgressCost,
		BreakEvenHours:    breakEvenHours,
		AdvisoryMessage:   advisory,
		IsSpotInstance:    true,
		InterruptionRisk:   interruptionRisk,
	}

	return option, nil
}

// Helper function to parse JSON response (for future use)
func parseJSONResponse(body io.Reader, v interface{}) error {
	return json.NewDecoder(body).Decode(v)
}

