"""
FRAUDGraph Timing Test Script
Measures processing time for fraud network analysis
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.fraud_agent import run_fraud_analysis
from backend.models.fraud_models import FraudAnalysisRequest

def run_timing_test():
    print("=" * 70)
    print("FRAUDGraph TIMING TEST")
    print("=" * 70)
    print()

    test_cases = [
        {
            "name": "Simple (2 phones, 1 account)",
            "phones": ["9876543210", "8765432109"],
            "accounts": ["HDFC0000123456"],
            "devices": [],
            "statement": ""
        },
        {
            "name": "Medium (3 phones, 2 accounts, 1 device)",
            "phones": ["9876543210", "8765432109", "7654321098"],
            "accounts": ["HDFC0000123456", "SBI99887766"],
            "devices": ["IMEI:359847101234567"],
            "statement": "I received a call from 9876543210 claiming to be from CBI."
        },
        {
            "name": "Complex (4 phones, 3 accounts, 2 devices, statement)",
            "phones": ["9876543210", "8765432109", "7654321098", "6543210987"],
            "accounts": ["HDFC0000123456", "SBI99887766", "ICICI11223344"],
            "devices": ["IMEI:359847101234567", "MAC:AA:BB:CC:DD:EE:FF"],
            "statement": "I received calls from 9876543210 and 8765432109 claiming to be from CBI. They forced me to transfer money to accounts HDFC0000123456 and SBI99887766."
        }
    ]

    results = []

    for test in test_cases:
        print(f"Testing: {test['name']}")
        start_time = time.time()

        request = FraudAnalysisRequest(
            phones=test["phones"],
            accounts=test["accounts"],
            devices=test["devices"],
            victim_statement=test["statement"]
        )

        result = run_fraud_analysis(request)
        elapsed = time.time() - start_time

        results.append({
            "name": test["name"],
            "entities": len(result.entities),
            "relationships": len(result.relationships),
            "clusters": len(result.clusters),
            "risk_level": result.risk_level.value,
            "processing_time": elapsed,
            "entities_per_second": len(result.entities) / elapsed if elapsed > 0 else 0,
        })

        print(f"  Entities: {len(result.entities)}, Relationships: {len(result.relationships)}, "
              f"Clusters: {len(result.clusters)}, Time: {elapsed:.2f}s")
        print()

    # Print summary table
    print("=" * 70)
    print("TIMING SUMMARY")
    print("=" * 70)
    print(f"{'Test Case':<35} {'Entities':<10} {'Time (s)':<10} {'Ent/sec':<10}")
    print("-" * 70)
    for r in results:
        print(f"{r['name']:<35} {r['entities']:<10} {r['processing_time']:<10.2f} {r['entities_per_second']:<10.1f}")

    total_time = sum(r["processing_time"] for r in results)
    avg_time = total_time / len(results) if results else 0
    print("-" * 70)
    print(f"{'Average':<35} {'':10} {avg_time:<10.2f}")

    print()
    print("=" * 70)
    print("METRICS")
    print("=" * 70)
    print(f"Average processing time: {avg_time:.2f} seconds")
    print(f"Lead time before mass victimisation: <{avg_time:.0f} seconds (analysis to insight)")
    print(f"Entity extraction rate: {sum(r['entities_per_second'] for r in results) / len(results):.1f} entities/second")
    print("=" * 70)

    return avg_time

if __name__ == "__main__":
    run_timing_test()
