package main

import (
	"fmt"
	"log"
)

// HardwareMapResolver handles hardware abstraction map queries and filtering
type HardwareMapResolver struct {
	redis *RedisClient
}

func NewHardwareMapResolver(redis *RedisClient) *HardwareMapResolver {
	return &HardwareMapResolver{redis: redis}
}

// ResolveInstances resolves instance types for a given GPU type and count, with optional filtering
func (h *HardwareMapResolver) ResolveInstances(gpuType string, gpuCount int, gpuMemoryGB *int, interconnect *string) ([]string, error) {
	// Get pre-filtered list from Redis (already filtered by GPU count)
	instanceKeys, err := h.redis.GetGPUMap(gpuType, gpuCount)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve GPU map: %w", err)
	}

	if len(instanceKeys) == 0 {
		return []string{}, nil
	}

	// If no optional filters, return all instances
	if gpuMemoryGB == nil && interconnect == nil {
		return instanceKeys, nil
	}

	// Filter by optional attributes
	filtered := make([]string, 0)
	for _, key := range instanceKeys {
		provider, region, instanceType, err := ParseInstanceKey(key)
		if err != nil {
			log.Printf("WARNING: Failed to parse instance key %s: %v", key, err)
			continue
		}

		// Fetch compute price to check metadata
		computePrice, err := h.redis.GetComputePrice(provider, region, instanceType)
		if err != nil {
			log.Printf("WARNING: Failed to get compute price for %s: %v", key, err)
			continue
		}
		if computePrice == nil {
			log.Printf("WARNING: Compute price not found for %s", key)
			continue
		}

		// Check GPU memory filter
		if gpuMemoryGB != nil {
			if computePrice.GPUMemoryGB == nil || *computePrice.GPUMemoryGB != *gpuMemoryGB {
				continue // Filtered out
			}
		}

		// Check interconnect filter
		if interconnect != nil {
			if computePrice.Interconnect == nil || *computePrice.Interconnect != *interconnect {
				continue // Filtered out
			}
		}

		filtered = append(filtered, key)
	}

	return filtered, nil
}

// FindDataLocalInstance finds the data-local instance from the hardware map
func (h *HardwareMapResolver) FindDataLocalInstance(dataLocation string, instanceKeys []string) (string, error) {
	sourceProvider, _, sourceRegion, err := ParseLocation(dataLocation)
	if err != nil {
		return "", fmt.Errorf("invalid data location: %w", err)
	}

	// Find matching instance in the same provider and region
	for _, key := range instanceKeys {
		provider, region, _, err := ParseInstanceKey(key)
		if err != nil {
			continue
		}

		if provider == sourceProvider && region == sourceRegion {
			return key, nil
		}
	}

	return "", fmt.Errorf("no matching instance found for data location %s", dataLocation)
}

