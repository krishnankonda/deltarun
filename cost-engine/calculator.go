package main

import (
	"fmt"
	"math"
)

// Calculator performs break-even calculations
type Calculator struct {
	redis *RedisClient
}

func NewCalculator(redis *RedisClient) *Calculator {
	return &Calculator{redis: redis}
}

// CalculateBreakEven calculates break-even hours for a remote option
func (c *Calculator) CalculateBreakEven(localCost, remoteCost, egressCost float64) (*float64, string) {
	// Edge case: Remote compute cost is higher or equal to local
	if remoteCost >= localCost {
		advisory := fmt.Sprintf("Not recommended. Compute cost is higher than the data-local option.")
		if remoteCost == localCost {
			advisory = "Compute cost is identical. This option is always more expensive."
		}
		return nil, advisory
	}

	// Calculate break-even hours: H = egress_cost / (local_cost - remote_cost)
	diff := localCost - remoteCost
	if diff <= 0 {
		return nil, "Not recommended. Compute cost is higher than the data-local option."
	}

	breakEvenHours := egressCost / diff

	// Round to 1 decimal place
	breakEvenHours = math.Round(breakEvenHours*10) / 10

	advisory := fmt.Sprintf("Cheaper than %s if your job runs for MORE than %.1f hours.", "data-local provider", breakEvenHours)
	return &breakEvenHours, advisory
}

// AnalyzeOption analyzes a single remote option
func (c *Calculator) AnalyzeOption(
	instanceKey string,
	sourceProvider, sourceService, sourceRegion string,
	localCostPerHour float64,
	dataSizeGB float64,
) (*AnalysisOption, error) {
	provider, region, instanceType, err := ParseInstanceKey(instanceKey)
	if err != nil {
		return nil, fmt.Errorf("invalid instance key: %w", err)
	}

	// Get compute price
	computePrice, err := c.redis.GetComputePrice(provider, region, instanceType)
	if err != nil {
		return nil, fmt.Errorf("failed to get compute price: %w", err)
	}
	if computePrice == nil {
		c.redis.LogMissingKey("compute", fmt.Sprintf("compute:%s:%s:%s", provider, region, instanceType))
		return nil, nil // Silently omit
	}

	remoteCostPerHour := computePrice.CostPerHour

	// Get egress price
	egressKey := BuildEgressKey(sourceProvider, sourceService, sourceRegion, provider, region)
	egressPrice, err := c.redis.GetEgressPrice(egressKey)
	if err != nil {
		return nil, fmt.Errorf("failed to get egress price: %w", err)
	}
	if egressPrice == nil {
		c.redis.LogMissingKey("egress", egressKey)
		return nil, nil // Silently omit
	}

	oneTimeEgressCost := egressPrice.CostPerGB * dataSizeGB

	// Calculate break-even
	breakEvenHours, advisory := c.CalculateBreakEven(localCostPerHour, remoteCostPerHour, oneTimeEgressCost)

	option := &AnalysisOption{
		Provider:          provider,
		Region:            region,
		InstanceType:      instanceType,
		ComputeCostPerHour: remoteCostPerHour,
		OneTimeEgressCost:  oneTimeEgressCost,
		BreakEvenHours:    breakEvenHours,
		AdvisoryMessage:   advisory,
		IsSpotInstance:    false,
		InterruptionRisk:   nil,
	}

	return option, nil
}

