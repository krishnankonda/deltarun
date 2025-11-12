package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "redis:6379"
	}

	redisClient, err := NewRedisClient(redisAddr)
	if err != nil {
		log.Fatalf("Failed to connect to Redis: %v", err)
	}
	defer redisClient.Close()

	hardwareMapResolver := NewHardwareMapResolver(redisClient)
	calculator := NewCalculator(redisClient)
	spotClient := NewSpotClient()

	http.HandleFunc("/analyze", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var req JobRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, fmt.Sprintf("Invalid request: %v", err), http.StatusBadRequest)
			return
		}

		// Validate required fields
		if req.JobName == "" || req.Data.Location == "" || req.Data.SizeGB <= 0 ||
			req.Compute.GPUType == "" || req.Compute.GPUCount <= 0 {
			http.Error(w, "Missing required fields", http.StatusBadRequest)
			return
		}

		response, err := analyzeJob(req, hardwareMapResolver, calculator, spotClient)
		if err != nil {
			http.Error(w, fmt.Sprintf("Analysis failed: %v", err), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		if err := json.NewEncoder(w).Encode(response); err != nil {
			http.Error(w, fmt.Sprintf("Failed to encode response: %v", err), http.StatusInternalServerError)
			return
		}
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Cost Engine listening on :%s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

func analyzeJob(
	req JobRequest,
	hardwareMapResolver *HardwareMapResolver,
	calculator *Calculator,
	spotClient *SpotClient,
) (*AnalysisResponse, error) {
	// Step 1: Resolve hardware map
	instanceKeys, err := hardwareMapResolver.ResolveInstances(
		req.Compute.GPUType,
		req.Compute.GPUCount,
		req.Compute.GPUMemoryGB,
		req.Compute.Interconnect,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to resolve hardware map: %w", err)
	}

	if len(instanceKeys) == 0 {
		return nil, fmt.Errorf("no instances found for GPU type %s with count %d", req.Compute.GPUType, req.Compute.GPUCount)
	}

	// Step 2: Find data-local option
	dataLocalKey, err := hardwareMapResolver.FindDataLocalInstance(req.Data.Location, instanceKeys)
	if err != nil {
		return nil, fmt.Errorf("failed to find data-local instance: %w", err)
	}

	sourceProvider, sourceService, sourceRegion, err := ParseLocation(req.Data.Location)
	if err != nil {
		return nil, fmt.Errorf("invalid data location: %w", err)
	}

	dataLocalProvider, dataLocalRegion, dataLocalInstanceType, err := ParseInstanceKey(dataLocalKey)
	if err != nil {
		return nil, fmt.Errorf("invalid data-local instance key: %w", err)
	}

	// Get data-local compute price
	dataLocalPrice, err := calculator.redis.GetComputePrice(dataLocalProvider, dataLocalRegion, dataLocalInstanceType)
	if err != nil || dataLocalPrice == nil {
		return nil, fmt.Errorf("failed to get data-local compute price")
	}

	localCostPerHour := dataLocalPrice.CostPerHour

	// Build data-local option
	dataLocalOption := AnalysisOption{
		Provider:          dataLocalProvider,
		Region:            dataLocalRegion,
		InstanceType:      dataLocalInstanceType,
		ComputeCostPerHour: localCostPerHour,
		OneTimeEgressCost:  0, // No egress for data-local
		BreakEvenHours:    nil,
		AdvisoryMessage:   "This is your data-local option.",
		IsSpotInstance:    false,
		InterruptionRisk:   nil,
	}

	// Step 3: Analyze remote options
	remoteOptions := make([]AnalysisOption, 0)
	for _, instanceKey := range instanceKeys {
		// Skip data-local option
		if instanceKey == dataLocalKey {
			continue
		}

		option, err := calculator.AnalyzeOption(
			instanceKey,
			sourceProvider,
			sourceService,
			sourceRegion,
			localCostPerHour,
			req.Data.SizeGB,
		)
		if err != nil {
			log.Printf("WARNING: Failed to analyze option %s: %v", instanceKey, err)
			continue
		}
		if option == nil {
			// Silently omitted (missing Redis keys)
			continue
		}

		remoteOptions = append(remoteOptions, *option)
	}

	// Step 4: Analyze AWS spot instances (only for AWS entries)
	for _, instanceKey := range instanceKeys {
		provider, _, _, err := ParseInstanceKey(instanceKey)
		if err != nil || provider != "aws" {
			continue
		}

		// Get on-demand price for fallback
		_, onDemandRegion, onDemandInstanceType, err := ParseInstanceKey(instanceKey)
		if err != nil {
			continue
		}
		onDemandPrice, err := calculator.redis.GetComputePrice(provider, onDemandRegion, onDemandInstanceType)
		if err != nil || onDemandPrice == nil {
			continue
		}

		spotOption, err := spotClient.AnalyzeSpotOption(
			instanceKey,
			sourceProvider,
			sourceService,
			sourceRegion,
			localCostPerHour,
			req.Data.SizeGB,
			onDemandPrice.CostPerHour,
			calculator,
		)
		if err != nil {
			log.Printf("WARNING: Failed to analyze spot option %s: %v", instanceKey, err)
			continue
		}
		if spotOption != nil {
			remoteOptions = append(remoteOptions, *spotOption)
		}
	}

	return &AnalysisResponse{
		DataLocalOption: dataLocalOption,
		RemoteOptions:   remoteOptions,
	}, nil
}

