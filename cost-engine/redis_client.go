package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"github.com/redis/go-redis/v9"
)

type RedisClient struct {
	client *redis.Client
	ctx    context.Context
}

func NewRedisClient(addr string) (*RedisClient, error) {
	rdb := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: "",
		DB:       0,
	})

	ctx := context.Background()

	// Test connection
	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &RedisClient{
		client: rdb,
		ctx:    ctx,
	}, nil
}

func (r *RedisClient) Close() error {
	return r.client.Close()
}

// GetGPUMap retrieves the list of instance types for a given GPU type and count
func (r *RedisClient) GetGPUMap(gpuType string, gpuCount int) ([]string, error) {
	key := fmt.Sprintf("gpu_map:%s:%d", gpuType, gpuCount)
	result, err := r.client.SMembers(r.ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return []string{}, nil // Empty set, not an error
		}
		return nil, fmt.Errorf("failed to get GPU map for %s:%d: %w", gpuType, gpuCount, err)
	}
	return result, nil
}

// GetComputePrice retrieves compute price for a specific instance
func (r *RedisClient) GetComputePrice(provider, region, instanceType string) (*ComputePrice, error) {
	key := fmt.Sprintf("compute:%s:%s:%s", provider, region, instanceType)
	val, err := r.client.Get(r.ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil // Key doesn't exist
		}
		return nil, fmt.Errorf("failed to get compute price for %s:%s:%s: %w", provider, region, instanceType, err)
	}

	var price ComputePrice
	if err := json.Unmarshal([]byte(val), &price); err != nil {
		return nil, fmt.Errorf("failed to unmarshal compute price: %w", err)
	}

	return &price, nil
}

// GetEgressPrice retrieves egress price
func (r *RedisClient) GetEgressPrice(key string) (*EgressPrice, error) {
	val, err := r.client.Get(r.ctx, key).Result()
	if err != nil {
		if err == redis.Nil {
			return nil, nil // Key doesn't exist
		}
		return nil, fmt.Errorf("failed to get egress price for %s: %w", key, err)
	}

	var price EgressPrice
	if err := json.Unmarshal([]byte(val), &price); err != nil {
		return nil, fmt.Errorf("failed to unmarshal egress price: %w", err)
	}

	return &price, nil
}

// BuildEgressKey constructs the egress key based on source and destination
func BuildEgressKey(sourceProvider, sourceService, sourceRegion, destProvider, destRegion string) string {
	if sourceProvider == destProvider {
		// Intra-cloud
		return fmt.Sprintf("egress:%s:%s:%s:%s:%s", sourceProvider, sourceService, sourceRegion, destProvider, destRegion)
	}
	// Inter-cloud
	return fmt.Sprintf("egress:%s:%s:%s:INTERNET", sourceProvider, sourceService, sourceRegion)
}

// ParseLocation parses a location string (provider:service:region) into components
func ParseLocation(location string) (provider, service, region string, err error) {
	parts := make([]string, 0, 3)
	current := ""
	for _, char := range location {
		if char == ':' {
			if current != "" {
				parts = append(parts, current)
				current = ""
			}
		} else {
			current += string(char)
		}
	}
	if current != "" {
		parts = append(parts, current)
	}

	if len(parts) != 3 {
		return "", "", "", fmt.Errorf("invalid location format: expected provider:service:region, got %s", location)
	}

	return parts[0], parts[1], parts[2], nil
}

// ParseInstanceKey parses an instance key (provider:region:instance_type) into components
func ParseInstanceKey(key string) (provider, region, instanceType string, err error) {
	parts := make([]string, 0, 3)
	current := ""
	for _, char := range key {
		if char == ':' {
			if current != "" {
				parts = append(parts, current)
				current = ""
			}
		} else {
			current += string(char)
		}
	}
	if current != "" {
		parts = append(parts, current)
	}

	if len(parts) != 3 {
		return "", "", "", fmt.Errorf("invalid instance key format: expected provider:region:instance_type, got %s", key)
	}

	return parts[0], parts[1], parts[2], nil
}

// LogMissingKey logs a missing Redis key (for debugging, but doesn't fail)
func (r *RedisClient) LogMissingKey(keyType, key string) {
	log.Printf("WARNING: Missing %s key: %s (silently omitting from results)", keyType, key)
}

