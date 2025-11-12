#!/bin/bash

# Manual Redis update script for HITL intervention
# Usage: ./scripts/manual-redis-update.sh <key> '<json_value>'
# Example: ./scripts/manual-redis-update.sh compute:coreweave:lva:HGX_H100_80G '{"cost_per_hour":12.00,"gpu_count":8}'

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <redis_key> '<json_value>'"
    echo "Example: $0 compute:coreweave:lva:HGX_H100_80G '{\"cost_per_hour\":12.00}'"
    exit 1
fi

REDIS_KEY=$1
JSON_VALUE=$2

# Check if Redis is accessible
if ! redis-cli -h localhost ping > /dev/null 2>&1; then
    echo "Error: Cannot connect to Redis. Is it running?"
    exit 1
fi

# Update the key
echo "Updating Redis key: $REDIS_KEY"
redis-cli -h localhost SET "$REDIS_KEY" "$JSON_VALUE"

echo "Successfully updated $REDIS_KEY"
echo "New value:"
redis-cli -h localhost GET "$REDIS_KEY"

