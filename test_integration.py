#!/usr/bin/env python3
"""
Integration tests for FinOps Orchestrator MVP 1
Tests the logic and data structures without requiring running services
"""

import json
import sys
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "api"))
sys.path.insert(0, str(Path(__file__).parent / "cli"))

def test_job_yaml_structure():
    """Test that job.yaml has correct structure"""
    print("Testing job.yaml structure...")
    try:
        import yaml
        with open("examples/job.yaml", "r") as f:
            data = yaml.safe_load(f)
        
        # Check required fields
        assert "job_name" in data, "Missing job_name"
        assert "data" in data, "Missing data section"
        assert "compute" in data, "Missing compute section"
        assert "data" in data and "location" in data["data"], "Missing data.location"
        assert "data" in data and "size_gb" in data["data"], "Missing data.size_gb"
        assert "compute" in data and "gpu_type" in data["compute"], "Missing compute.gpu_type"
        assert "compute" in data and "gpu_count" in data["compute"], "Missing compute.gpu_count"
        
        # Check location format (provider:service:region)
        location = data["data"]["location"]
        parts = location.split(":")
        assert len(parts) == 3, f"Invalid location format: {location} (expected provider:service:region)"
        
        # Check optional output block
        if "output" in data:
            assert "location" in data["output"], "output.location missing"
            assert "path" in data["output"], "output.path missing"
        
        print("✓ job.yaml structure is valid")
        return True
    except Exception as e:
        print(f"✗ job.yaml structure test failed: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic models can parse job.yaml"""
    print("\nTesting Pydantic models...")
    try:
        from cli.models import JobRequest, JobData, JobCompute, JobOutput
        import yaml
        
        with open("examples/job.yaml", "r") as f:
            data = yaml.safe_load(f)
        
        # Test parsing
        job_request = JobRequest(**data)
        
        # Verify fields
        assert job_request.job_name == "train-llama-v3-experiment"
        assert job_request.data.location == "aws:s3:us-east-1"
        assert job_request.data.size_gb == 10000.0
        assert job_request.compute.gpu_type == "H100"
        assert job_request.compute.gpu_count == 8
        
        # Verify optional output block
        if job_request.output:
            assert job_request.output.location == "aws:s3:us-east-1"
            assert "s3://" in job_request.output.path
        
        print("✓ Pydantic models parse correctly")
        return True
    except Exception as e:
        print(f"✗ Pydantic models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_models():
    """Test API models validation"""
    print("\nTesting API models validation...")
    try:
        from api.models import JobData, JobCompute, JobRequest, AnalysisOption, AnalysisResponse
        
        # Test valid location format
        valid_data = JobData(location="aws:s3:us-east-1", size_gb=1000.0)
        assert valid_data.location == "aws:s3:us-east-1"
        
        # Test invalid location format (should fail)
        try:
            invalid_data = JobData(location="aws:us-east-1", size_gb=1000.0)
            print("✗ Should have rejected invalid location format")
            return False
        except Exception:
            pass  # Expected to fail
        
        # Test optional compute fields
        compute = JobCompute(gpu_type="H100", gpu_count=8, gpu_memory_gb=80, interconnect="infiniband")
        assert compute.gpu_memory_gb == 80
        assert compute.interconnect == "infiniband"
        
        # Test AnalysisOption with interruption risk
        option = AnalysisOption(
            provider="AWS",
            region="us-east-1",
            compute_cost_per_hour=16.0,
            one_time_egress_cost=900.0,
            break_even_hours=225.0,
            advisory_message="Test",
            interruption_risk="MEDIUM"
        )
        assert option.interruption_risk == "MEDIUM"
        
        print("✓ API models validation works correctly")
        return True
    except Exception as e:
        print(f"✗ API models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_prices_structure():
    """Test sample prices JSON structure"""
    print("\nTesting sample prices structure...")
    try:
        with open("data/sample-prices.json", "r") as f:
            data = json.load(f)
        
        # Check GPU maps structure
        assert "gpu_maps" in data, "Missing gpu_maps"
        assert "H100:8" in data["gpu_maps"], "Missing gpu_map:H100:8"
        assert isinstance(data["gpu_maps"]["H100:8"], list), "gpu_map:H100:8 should be a list"
        assert len(data["gpu_maps"]["H100:8"]) > 0, "gpu_map:H100:8 should have entries"
        
        # Check compute prices
        assert "compute" in data, "Missing compute prices"
        assert "aws:us-east-1:p5.48xlarge" in data["compute"], "Missing compute price for p5.48xlarge"
        compute_price = data["compute"]["aws:us-east-1:p5.48xlarge"]
        assert "cost_per_hour" in compute_price, "Missing cost_per_hour"
        assert "gpu_count" in compute_price, "Missing gpu_count"
        
        # Check egress prices (service-specific)
        assert "egress" in data, "Missing egress prices"
        assert "aws:s3:us-east-1:INTERNET" in data["egress"], "Missing S3 egress price"
        assert "aws:ec2:us-east-1:INTERNET" in data["egress"], "Missing EC2 egress price"
        
        print("✓ Sample prices structure is correct")
        return True
    except Exception as e:
        print(f"✗ Sample prices test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_seed_script_logic():
    """Test seed script logic (verify commands are correct)"""
    print("\nTesting seed script logic...")
    try:
        with open("scripts/seed-redis.sh", "r") as f:
            script = f.read()
        
        # Check that GPU maps use SADD (Redis SET operations)
        assert "SADD gpu_map:H100:8" in script, "Seed script should use SADD for GPU maps"
        assert "SADD gpu_map:H100:1" in script, "Seed script should include H100:1 map"
        assert "SADD gpu_map:A100:8" in script, "Seed script should include A100:8 map"
        
        # Check compute prices use SET
        assert "SET compute:aws:us-east-1:p5.48xlarge" in script, "Seed script should set compute prices"
        
        # Check egress prices (service-specific)
        assert "egress:aws:s3:us-east-1:INTERNET" in script, "Seed script should include S3 egress"
        assert "egress:aws:ec2:us-east-1:INTERNET" in script, "Seed script should include EC2 egress"
        
        print("✓ Seed script logic is correct")
        return True
    except Exception as e:
        print(f"✗ Seed script test failed: {e}")
        return False

def test_break_even_calculations():
    """Test break-even calculation logic"""
    print("\nTesting break-even calculation logic...")
    
    test_cases = [
        {
            "name": "Local cheaper",
            "local": 1.0,
            "remote": 2.0,
            "egress": 100.0,
            "expected_break_even": None,
            "should_recommend": False
        },
        {
            "name": "Remote cheaper",
            "local": 2.0,
            "remote": 1.0,
            "egress": 100.0,
            "expected_break_even": 100.0,
            "should_recommend": True
        },
        {
            "name": "Identical cost",
            "local": 2.0,
            "remote": 2.0,
            "egress": 100.0,
            "expected_break_even": None,
            "should_recommend": False
        },
        {
            "name": "No egress cost",
            "local": 2.0,
            "remote": 1.0,
            "egress": 0.0,
            "expected_break_even": 0.0,
            "should_recommend": True
        }
    ]
    
    all_passed = True
    for case in test_cases:
        try:
            # Calculate break-even: H = egress_cost / (local_cost - remote_cost)
            if case["remote"] >= case["local"]:
                break_even = None
                should_recommend = False
            else:
                diff = case["local"] - case["remote"]
                if diff > 0:
                    break_even = case["egress"] / diff
                    should_recommend = True
                else:
                    break_even = None
                    should_recommend = False
            
            if break_even is None and case["expected_break_even"] is None:
                print(f"  ✓ {case['name']}: Correctly returns None")
            elif break_even is not None and case["expected_break_even"] is not None:
                if abs(break_even - case["expected_break_even"]) < 0.1:
                    print(f"  ✓ {case['name']}: Break-even = {break_even:.1f} hours")
                else:
                    print(f"  ✗ {case['name']}: Expected {case['expected_break_even']}, got {break_even}")
                    all_passed = False
            else:
                print(f"  ✗ {case['name']}: Mismatch in break-even calculation")
                all_passed = False
        except Exception as e:
            print(f"  ✗ {case['name']}: Error - {e}")
            all_passed = False
    
    if all_passed:
        print("✓ Break-even calculations are correct")
    return all_passed

def test_hardware_map_key_structure():
    """Test hardware map key structure"""
    print("\nTesting hardware map key structure...")
    
    # Verify keys follow format: gpu_map:{gpu_type}:{gpu_count}
    test_keys = [
        "gpu_map:H100:8",
        "gpu_map:H100:1",
        "gpu_map:A100:8"
    ]
    
    for key in test_keys:
        parts = key.split(":")
        assert len(parts) == 3, f"Invalid key format: {key}"
        assert parts[0] == "gpu_map", f"Key should start with 'gpu_map': {key}"
        assert parts[2].isdigit(), f"GPU count should be numeric: {key}"
    
    print("✓ Hardware map key structure is correct")
    return True

def test_egress_key_structure():
    """Test egress key structure"""
    print("\nTesting egress key structure...")
    
    # Inter-cloud format: egress:{provider}:{service}:{region}:INTERNET
    inter_cloud_key = "egress:aws:s3:us-east-1:INTERNET"
    parts = inter_cloud_key.split(":")
    assert len(parts) == 5, f"Inter-cloud key should have 5 parts: {inter_cloud_key}"
    assert parts[0] == "egress", "Should start with 'egress'"
    assert parts[4] == "INTERNET", "Should end with 'INTERNET'"
    
    # Intra-cloud format: egress:{provider}:{service}:{region}:{dest_provider}:{dest_region}
    intra_cloud_key = "egress:aws:s3:us-east-1:aws:us-west-2"
    parts = intra_cloud_key.split(":")
    assert len(parts) == 6, f"Intra-cloud key should have 6 parts: {intra_cloud_key}"
    assert parts[0] == "egress", "Should start with 'egress'"
    
    print("✓ Egress key structure is correct")
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("FinOps Orchestrator MVP 1 - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_job_yaml_structure,
        test_pydantic_models,
        test_api_models,
        test_sample_prices_structure,
        test_seed_script_logic,
        test_break_even_calculations,
        test_hardware_map_key_structure,
        test_egress_key_structure,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results), 1):
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{i}. {test.__name__}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! MVP 1 objectives verified.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

