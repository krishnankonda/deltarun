#!/usr/bin/env python3
"""
Code Structure Verification Tests
Verifies that all required files and components exist
"""

import os
from pathlib import Path

def test_file_structure():
    """Test that all required files exist"""
    print("Testing file structure...")
    
    required_files = {
        "Root": [
            "docker-compose.yml",
            "README.md",
            "SETUP.md",
            "Makefile",
            ".gitignore",
        ],
        "CLI": [
            "cli/main.py",
            "cli/models.py",
            "cli/api_client.py",
            "cli/formatter.py",
            "cli/pyproject.toml",
            "cli/requirements.txt",
        ],
        "API": [
            "api/main.py",
            "api/models.py",
            "api/cost_engine_client.py",
            "api/pyproject.toml",
            "api/requirements.txt",
            "api/Dockerfile",
        ],
        "Cost Engine": [
            "cost-engine/main.go",
            "cost-engine/models.go",
            "cost-engine/redis_client.go",
            "cost-engine/hardware_map.go",
            "cost-engine/calculator.go",
            "cost-engine/spot_client.go",
            "cost-engine/calculator_test.go",
            "cost-engine/go.mod",
            "cost-engine/Dockerfile",
        ],
        "Scraper": [
            "scraper/main.go",
            "scraper/hardware_map_builder.go",
            "scraper/go.mod",
            "scraper/Dockerfile",
        ],
        "Scripts": [
            "scripts/seed-redis.sh",
            "scripts/manual-redis-update.sh",
        ],
        "Data": [
            "data/sample-prices.json",
        ],
        "Examples": [
            "examples/job.yaml",
        ],
    }
    
    all_present = True
    for category, files in required_files.items():
        print(f"\n  {category}:")
        for file_path in files:
            if os.path.exists(file_path):
                print(f"    ✓ {file_path}")
            else:
                print(f"    ✗ {file_path} (MISSING)")
                all_present = False
    
    return all_present

def test_docker_compose_services():
    """Test Docker Compose configuration"""
    print("\nTesting Docker Compose configuration...")
    
    with open("docker-compose.yml", "r") as f:
        content = f.read()
    
    required_services = ["redis", "cost-engine", "api", "seed-redis"]
    all_present = True
    
    for service in required_services:
        if f"{service}:" in content:
            print(f"  ✓ Service '{service}' configured")
        else:
            print(f"  ✗ Service '{service}' missing")
            all_present = False
    
    # Check network configuration
    if "finops-network" in content:
        print("  ✓ Network configuration present")
    else:
        print("  ✗ Network configuration missing")
        all_present = False
    
    return all_present

def test_go_code_structure():
    """Test Go code structure"""
    print("\nTesting Go code structure...")
    
    # Check Cost Engine main.go has required functions
    with open("cost-engine/main.go", "r") as f:
        main_code = f.read()
    
    required_functions = [
        "analyzeJob",
        "NewRedisClient",
        "NewHardwareMapResolver",
        "NewCalculator",
        "NewSpotClient",
    ]
    
    all_present = True
    for func in required_functions:
        if func in main_code:
            print(f"  ✓ Function '{func}' exists")
        else:
            print(f"  ✗ Function '{func}' missing")
            all_present = False
    
    # Check calculator has break-even logic
    with open("cost-engine/calculator.go", "r") as f:
        calc_code = f.read()
    
    if "CalculateBreakEven" in calc_code:
        print("  ✓ Break-even calculation function exists")
    else:
        print("  ✗ Break-even calculation function missing")
        all_present = False
    
    return all_present

def test_api_endpoints():
    """Test API endpoints"""
    print("\nTesting API endpoints...")
    
    with open("api/main.py", "r") as f:
        api_code = f.read()
    
    # Check for required endpoint
    if "/api/v1/analyze" in api_code:
        print("  ✓ POST /api/v1/analyze endpoint exists")
    else:
        print("  ✗ POST /api/v1/analyze endpoint missing")
        return False
    
    # Check for health endpoint
    if "/health" in api_code:
        print("  ✓ GET /health endpoint exists")
    else:
        print("  ⚠ Health endpoint missing (optional)")
    
    return True

def test_cli_commands():
    """Test CLI commands"""
    print("\nTesting CLI commands...")
    
    with open("cli/main.py", "r") as f:
        cli_code = f.read()
    
    # Check for analyze command
    if "@app.command" in cli_code and "analyze" in cli_code:
        print("  ✓ 'analyze' command exists")
    else:
        print("  ✗ 'analyze' command missing")
        return False
    
    # Check for file flag
    if "--file" in cli_code or "-f" in cli_code:
        print("  ✓ File flag (--file/-f) exists")
    else:
        print("  ✗ File flag missing")
        return False
    
    return True

def main():
    """Run all structure tests"""
    print("=" * 70)
    print("Code Structure Verification")
    print("=" * 70)
    
    tests = [
        ("File structure", test_file_structure),
        ("Docker Compose", test_docker_compose_services),
        ("Go code structure", test_go_code_structure),
        ("API endpoints", test_api_endpoints),
        ("CLI commands", test_cli_commands),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("Structure Test Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nTotal: {passed}/{total} structure tests passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    exit(main())

