package main

import (
	"context"
	"fmt"
	"log"

	"github.com/redis/go-redis/v9"
)

// HardwareMapBuilder builds and updates GPU map Redis SETs
type HardwareMapBuilder struct {
	redis *redis.Client
	ctx   context.Context
}

func NewHardwareMapBuilder(redisAddr string) (*HardwareMapBuilder, error) {
	rdb := redis.NewClient(&redis.Options{
		Addr:     redisAddr,
		Password: "",
		DB:       0,
	})

	ctx := context.Background()

	if err := rdb.Ping(ctx).Err(); err != nil {
		return nil, fmt.Errorf("failed to connect to Redis: %w", err)
	}

	return &HardwareMapBuilder{
		redis: rdb,
		ctx:   ctx,
	}, nil
}

// AddInstanceToGPUMap adds an instance to the appropriate GPU map
func (h *HardwareMapBuilder) AddInstanceToGPUMap(gpuType string, gpuCount int, instanceKey string) error {
	mapKey := fmt.Sprintf("gpu_map:%s:%d", gpuType, gpuCount)
	err := h.redis.SAdd(h.ctx, mapKey, instanceKey).Err()
	if err != nil {
		return fmt.Errorf("failed to add instance to GPU map: %w", err)
	}
	log.Printf("Added %s to %s", instanceKey, mapKey)
	return nil
}

// SetComputePrice sets the compute price for an instance
func (h *HardwareMapBuilder) SetComputePrice(key string, priceJSON string) error {
	err := h.redis.Set(h.ctx, key, priceJSON, 0).Err()
	if err != nil {
		return fmt.Errorf("failed to set compute price: %w", err)
	}
	log.Printf("Set compute price for %s", key)
	return nil
}

// SetEgressPrice sets the egress price
func (h *HardwareMapBuilder) SetEgressPrice(key string, priceJSON string) error {
	err := h.redis.Set(h.ctx, key, priceJSON, 0).Err()
	if err != nil {
		return fmt.Errorf("failed to set egress price: %w", err)
	}
	log.Printf("Set egress price for %s", key)
	return nil
}

func (h *HardwareMapBuilder) Close() error {
	return h.redis.Close()
}

