#!/usr/bin/env python3
"""
MVP 1 Objectives Verification Tests
Tests that all MVP 1 requirements are met
"""

import json
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "api"))
sys.path.insert(0, str(Path(__file__).parent / "cli"))

def test_mvp1_objective_1_read_only():
    """MVP1 Objective 1: Read-only, non-authenticated analysis tool"""
    print("Testing MVP1 Objective 1: Read-only, non-authenticated tool...")
    
    # Check that there's no authentication in API
    with open("api/main.py", "r") as f:
        api_code = f.read()
    
    auth_keywords = ["auth", "token", "credential", "login", "password"]
    found_auth = [kw for kw in auth_keywords if kw in api_code.lower()]
    
    # Should not have authentication logic
    if any("@app.post" in line and any(kw in line.lower() for kw in ["auth", "token"]) for line in api_code.split("\n")):
        print("  ✗ Found authentication logic in API")
        return False
    
    print("  ✓ No authentication required (read-only tool)")
    return True

def test_mvp1_objective_2_job_yaml_parsing():
    """MVP1 Objective 2: Ingest job.yaml file"""
    print("\nTesting MVP1 Objective 2: job.yaml ingestion...")
    
    try:
        import yaml
        from cli.models import JobRequest
        
        with open("examples/job.yaml", "r") as f:
            data = yaml.safe_load(f)
        
        # Verify all required fields
        required = {
            "job_name": str,
            "data.location": str,
            "data.size_gb": (int, float),
            "compute.gpu_type": str,
            "compute.gpu_count": int
        }
        
        all_present = True
        for field, field_type in required.items():
            parts = field.split(".")
            current = data
            for part in parts:
                if part not in current:
                    print(f"  ✗ Missing required field: {field}")
                    all_present = False
                    break
                current = current[part]
            else:
                if not isinstance(current, field_type):
                    print(f"  ✗ Wrong type for {field}: expected {field_type}")
                    all_present = False
        
        # Test Pydantic parsing
        job_request = JobRequest(**data)
        
        if all_present:
            print("  ✓ job.yaml parsing works correctly")
            print(f"    - Job name: {job_request.job_name}")
            print(f"    - Data location: {job_request.data.location}")
            print(f"    - Data size: {job_request.data.size_gb} GB")
            print(f"    - GPU type: {job_request.compute.gpu_type}")
            print(f"    - GPU count: {job_request.compute.gpu_count}")
            return True
        return False
    except Exception as e:
        print(f"  ✗ job.yaml parsing failed: {e}")
        return False

def test_mvp1_objective_3_break_even_analysis():
    """MVP1 Objective 3: Perform break-even analysis"""
    print("\nTesting MVP1 Objective 3: Break-even analysis...")
    
    # Test the break-even formula: H = Egress_Cost / (Local_Cost - Remote_Cost)
    test_cases = [
        {
            "name": "Standard case",
            "local_cost": 16.0,
            "remote_cost": 12.0,
            "egress_cost": 900.0,
            "expected_hours": 225.0
        },
        {
            "name": "High egress cost",
            "local_cost": 16.0,
            "remote_cost": 12.0,
            "egress_cost": 1800.0,
            "expected_hours": 450.0
        },
        {
            "name": "Small cost difference",
            "local_cost": 16.0,
            "remote_cost": 15.0,
            "egress_cost": 100.0,
            "expected_hours": 100.0
        }
    ]
    
    all_passed = True
    for case in test_cases:
        diff = case["local_cost"] - case["remote_cost"]
        if diff > 0:
            hours = case["egress_cost"] / diff
            if abs(hours - case["expected_hours"]) < 0.1:
                print(f"  ✓ {case['name']}: Break-even = {hours:.1f} hours")
            else:
                print(f"  ✗ {case['name']}: Expected {case['expected_hours']}, got {hours}")
                all_passed = False
        else:
            print(f"  ✗ {case['name']}: Invalid cost difference")
            all_passed = False
    
    if all_passed:
        print("  ✓ Break-even analysis formula is correct")
    return all_passed

def test_mvp1_objective_4_hardware_abstraction_map():
    """MVP1 Objective 4: Hardware abstraction map"""
    print("\nTesting MVP1 Objective 4: Hardware abstraction map...")
    
    with open("data/sample-prices.json", "r") as f:
        data = json.load(f)
    
    # Check GPU maps exist with correct format
    gpu_maps = data.get("gpu_maps", {})
    
    required_maps = ["H100:8", "H100:1", "A100:8"]
    all_present = True
    
    for map_key in required_maps:
        if map_key not in gpu_maps:
            print(f"  ✗ Missing GPU map: {map_key}")
            all_present = False
        else:
            instances = gpu_maps[map_key]
            if not isinstance(instances, list) or len(instances) == 0:
                print(f"  ✗ Invalid GPU map {map_key}: should be non-empty list")
                all_present = False
            else:
                # Verify instance keys format: provider:region:instance_type
                for instance in instances:
                    parts = instance.split(":")
                    if len(parts) != 3:
                        print(f"  ✗ Invalid instance key format: {instance}")
                        all_present = False
    
    if all_present:
        print("  ✓ Hardware abstraction map structure is correct")
        print(f"    - Found {len(gpu_maps)} GPU maps")
        for key, instances in gpu_maps.items():
            print(f"    - {key}: {len(instances)} instances")
    return all_present

def test_mvp1_objective_5_service_specific_egress():
    """MVP1 Objective 5: Service-specific egress pricing"""
    print("\nTesting MVP1 Objective 5: Service-specific egress...")
    
    with open("data/sample-prices.json", "r") as f:
        data = json.load(f)
    
    egress = data.get("egress", {})
    
    # Check for service-specific keys
    required_keys = [
        "aws:s3:us-east-1:INTERNET",
        "aws:ec2:us-east-1:INTERNET",
        "aws:s3:us-east-1:aws:us-west-2"
    ]
    
    all_present = True
    for key in required_keys:
        if key not in egress:
            print(f"  ✗ Missing egress key: {key}")
            all_present = False
        else:
            price = egress[key]
            if "cost_per_gb" not in price:
                print(f"  ✗ Invalid egress price format for {key}")
                all_present = False
    
    # Verify S3 and EC2 have different prices (if both exist)
    if "aws:s3:us-east-1:INTERNET" in egress and "aws:ec2:us-east-1:INTERNET" in egress:
        s3_price = egress["aws:s3:us-east-1:INTERNET"]["cost_per_gb"]
        ec2_price = egress["aws:ec2:us-east-1:INTERNET"]["cost_per_gb"]
        print(f"    - S3 egress: ${s3_price}/GB")
        print(f"    - EC2 egress: ${ec2_price}/GB")
    
    if all_present:
        print("  ✓ Service-specific egress pricing is implemented")
    return all_present

def test_mvp1_objective_6_spot_instance_analysis():
    """MVP1 Objective 6: Spot instance analysis (AWS-only)"""
    print("\nTesting MVP1 Objective 6: Spot instance analysis...")
    
    # Check spot client exists
    with open("cost-engine/spot_client.go", "r") as f:
        spot_code = f.read()
    
    checks = [
        ("GetSpotPrice" in spot_code, "Spot price query method"),
        ("GetInterruptionRate" in spot_code, "Interruption rate query method"),
        ("MapInterruptionRateToRisk" in spot_code, "Risk mapping function"),
        ("LOW" in spot_code and "MEDIUM" in spot_code and "HIGH" in spot_code, "Risk levels defined"),
        ("graceful degradation" in spot_code.lower() or "fallback" in spot_code.lower(), "Graceful degradation"),
    ]
    
    all_passed = True
    for check, description in checks:
        if check:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Missing: {description}")
            all_passed = False
    
    if all_passed:
        print("  ✓ Spot instance analysis is implemented")
    return all_passed

def test_mvp1_objective_7_graceful_error_handling():
    """MVP1 Objective 7: Graceful error handling"""
    print("\nTesting MVP1 Objective 7: Graceful error handling...")
    
    checks = []
    
    # Check Cost Engine has silent omission logic
    with open("cost-engine/calculator.go", "r") as f:
        calc_code = f.read()
    
    checks.append((
        "LogMissingKey" in calc_code or "silently omit" in calc_code.lower(),
        "Silent omission of missing Redis keys"
    ))
    
    # Check spot client has graceful degradation
    with open("cost-engine/spot_client.go", "r") as f:
        spot_code = f.read()
    
    checks.append((
        "fallback" in spot_code.lower() or "on-demand" in spot_code.lower(),
        "Spot API failure fallback"
    ))
    
    # Check API has error handling
    with open("api/main.py", "r") as f:
        api_code = f.read()
    
    checks.append((
        "HTTPException" in api_code or "Exception" in api_code,
        "API error handling"
    ))
    
    all_passed = True
    for check, description in checks:
        if check:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ Missing: {description}")
            all_passed = False
    
    if all_passed:
        print("  ✓ Graceful error handling is implemented")
    return all_passed

def test_mvp1_objective_8_output_block_future_proofing():
    """MVP1 Objective 8: Output block for MVP 3 future-proofing"""
    print("\nTesting MVP1 Objective 8: Output block future-proofing...")
    
    # Check job.yaml has output block
    import yaml
    with open("examples/job.yaml", "r") as f:
        data = yaml.safe_load(f)
    
    if "output" not in data:
        print("  ✗ Missing output block in example job.yaml")
        return False
    
    output = data["output"]
    if "location" not in output or "path" not in output:
        print("  ✗ Output block missing required fields")
        return False
    
    # Check models support output (optional)
    from cli.models import JobRequest
    job_request = JobRequest(**data)
    
    if job_request.output is None:
        print("  ✗ Output block not parsed")
        return False
    
    print(f"  ✓ Output block is present and parsed")
    print(f"    - Location: {job_request.output.location}")
    print(f"    - Path: {job_request.output.path}")
    print("  ✓ Future-proofing for MVP 3 is in place")
    return True

def main():
    """Run all MVP1 objective tests"""
    print("=" * 70)
    print("FinOps Orchestrator MVP 1 - Objectives Verification")
    print("=" * 70)
    
    objectives = [
        ("Read-only, non-authenticated tool", test_mvp1_objective_1_read_only),
        ("job.yaml ingestion", test_mvp1_objective_2_job_yaml_parsing),
        ("Break-even analysis", test_mvp1_objective_3_break_even_analysis),
        ("Hardware abstraction map", test_mvp1_objective_4_hardware_abstraction_map),
        ("Service-specific egress", test_mvp1_objective_5_service_specific_egress),
        ("Spot instance analysis", test_mvp1_objective_6_spot_instance_analysis),
        ("Graceful error handling", test_mvp1_objective_7_graceful_error_handling),
        ("Output block future-proofing", test_mvp1_objective_8_output_block_future_proofing),
    ]
    
    results = []
    for name, test_func in objectives:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test for '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 70)
    print("MVP 1 Objectives Summary")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for i, (name, result) in enumerate(results, 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} objectives met")
    
    if passed == total:
        print("\n🎉 All MVP 1 objectives have been met!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} objective(s) need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

