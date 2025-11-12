#!/bin/sh

set -e

echo "Waiting for Redis to be ready..."
until redis-cli -h redis ping > /dev/null 2>&1; do
  sleep 1
done

echo "Redis is ready. Seeding data..."

# Read JSON file and populate Redis
# Using jq-like parsing with a simple approach
# For production, consider using a proper JSON parser

# Load GPU maps (Redis SETs)
echo "Loading GPU maps..."
redis-cli -h redis SADD gpu_map:H100:8 "aws:us-east-1:p5.48xlarge" "aws:us-west-2:p5.48xlarge" "gcp:us-central1:a3-highgpu-8g" "coreweave:lva:HGX_H100_80G" > /dev/null
redis-cli -h redis SADD gpu_map:H100:1 "aws:us-east-1:p5.xlarge" > /dev/null
redis-cli -h redis SADD gpu_map:A100:8 "aws:us-east-1:p4d.24xlarge" "gcp:us-central1:a2-highgpu-8g" > /dev/null

# Load compute prices
echo "Loading compute prices..."
redis-cli -h redis SET compute:aws:us-east-1:p5.48xlarge '{"provider":"AWS","region":"us-east-1","instance_type":"p5.48xlarge","cost_per_hour":16.00,"gpu_count":8,"gpu_memory_gb":80,"interconnect":"ethernet"}' > /dev/null
redis-cli -h redis SET compute:aws:us-west-2:p5.48xlarge '{"provider":"AWS","region":"us-west-2","instance_type":"p5.48xlarge","cost_per_hour":16.00,"gpu_count":8,"gpu_memory_gb":80,"interconnect":"ethernet"}' > /dev/null
redis-cli -h redis SET compute:gcp:us-central1:a3-highgpu-8g '{"provider":"GCP","region":"us-central1","instance_type":"a3-highgpu-8g","cost_per_hour":17.00,"gpu_count":8,"gpu_memory_gb":80,"interconnect":"ethernet"}' > /dev/null
redis-cli -h redis SET compute:coreweave:lva:HGX_H100_80G '{"provider":"CoreWeave","region":"lva","instance_type":"HGX_H100_80G","cost_per_hour":12.00,"gpu_count":8,"gpu_memory_gb":80,"interconnect":"infiniband"}' > /dev/null
redis-cli -h redis SET compute:aws:us-east-1:p5.xlarge '{"provider":"AWS","region":"us-east-1","instance_type":"p5.xlarge","cost_per_hour":2.00,"gpu_count":1,"gpu_memory_gb":80,"interconnect":"ethernet"}' > /dev/null
redis-cli -h redis SET compute:aws:us-east-1:p4d.24xlarge '{"provider":"AWS","region":"us-east-1","instance_type":"p4d.24xlarge","cost_per_hour":14.00,"gpu_count":8,"gpu_memory_gb":40,"interconnect":"ethernet"}' > /dev/null
redis-cli -h redis SET compute:gcp:us-central1:a2-highgpu-8g '{"provider":"GCP","region":"us-central1","instance_type":"a2-highgpu-8g","cost_per_hour":15.00,"gpu_count":8,"gpu_memory_gb":40,"interconnect":"ethernet"}' > /dev/null

# Load egress prices
echo "Loading egress prices..."
redis-cli -h redis SET egress:aws:s3:us-east-1:INTERNET '{"cost_per_gb":0.09}' > /dev/null
redis-cli -h redis SET egress:aws:ec2:us-east-1:INTERNET '{"cost_per_gb":0.10}' > /dev/null
redis-cli -h redis SET egress:aws:s3:us-east-1:aws:us-west-2 '{"cost_per_gb":0.02}' > /dev/null
redis-cli -h redis SET egress:aws:s3:us-west-2:INTERNET '{"cost_per_gb":0.09}' > /dev/null
redis-cli -h redis SET egress:gcp:gcs:us-central1:INTERNET '{"cost_per_gb":0.12}' > /dev/null
redis-cli -h redis SET egress:coreweave:storage:lva:INTERNET '{"cost_per_gb":0.05}' > /dev/null

# Load spot API info
echo "Loading spot API info..."
redis-cli -h redis SET spot_api:aws '{"endpoint":"https://ec2.amazonaws.com","instance_key_format":"{instance_type}"}' > /dev/null

echo "Redis seeding complete!"

