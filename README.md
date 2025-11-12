# DeltaRun

Working on a CLI tool that helps developers manage the cost of training models across multiple cloud providers. The motivation to create this project came from a desire to help mitigate the looming data gravity problem, where the location and size of data increasingly limit cost-effective choices for compute. With this tool, developers can ideally make informed decisions about where to train their models given constraints. MVP 1 is a read-only, non-authenticated analysis tool that performs break-even analysis for cloud compute costs versus data egress fees.

Put simply:\
When training ML models, you face a trade-off:
 - Run locally (where your data is): no data transfer fees, but compute may be expensive
 - Run remotely (cheaper compute): lower compute cost, but you pay to transfer data (egress fees)

This tool hopes to fix this issue by calculating the break-even point: how long your job must run before a remote option becomes cheaper.

## Current Status

The tool analyzes whether it's cheaper to run your training job on a remote cloud provider (with lower compute costs) or keep it local to your data (avoiding egress fees). It calculates the **break-even point**: how many hours your job must run before the remote option becomes cheaper.

**Example:** If your data is in AWS S3 (us-east-1) and you're considering CoreWeave:
- **Local (AWS):** $16/hr compute
- **Remote (CoreWeave):** $12/hr compute + $900 one-time egress fee
- **Break-even:** 225 hours (if your job runs longer, CoreWeave is cheaper)

## Architecture

The system consists of 5 main components:

1. **CLI** (`/cli`) - Python CLI using Typer for user interaction
2. **Backend API** (`/api`) - Python FastAPI server that proxies requests
3. **Cost Engine** (`/cost-engine`) - Go microservice that performs calculations
4. **Price Database** (`/docker-compose.yml`) - Redis cache for pricing data
5. **Price Scraper** (`/scraper`) - Go service that populates pricing data (background)

## Prerequisites

- **Docker and Docker Compose** (for running services)
- **Python 3.9+** (for CLI and API)
- **Go 1.21+** (optional, for local Cost Engine development)

## Quick Start Guide (Coming Soon)

## License

MIT
