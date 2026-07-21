"""
SCAMWatch Accuracy Test Script
Runs 20 sample texts through the SCAMWatch pipeline and prints results.
Usage: python -m backend.scripts.accuracy_test
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.agents.scam_agent import run_scam_analysis

# Test cases: (text, expected_type, is_scam)
TEST_CASES = [
    # SCAM TESTS (15 total)
    ("Sir, I am calling from CBI headquarters. Your Aadhaar number has been used to open illegal bank accounts. You are under digital arrest. Transfer Rs 5 lakh immediately.", "digital_arrest", True),
    ("URGENT: Your SBI account KYC is expired. Account will be blocked. Click here: http://sbi-kyc-update.xyz", "fake_kyc", True),
    ("Hello! I am from WealthGrow Investment Group. Our members are earning 40% monthly returns. Guaranteed returns. Join today!", "fake_investment", True),
    ("Work from home opportunity. Earn Rs 5000 daily. Registration fee Rs 500. Send Aadhaar copy to apply.", "fake_job", True),
    ("Congratulations! You have won Rs 25 lakh in KBC Lucky Draw. Pay processing fee Rs 5000 to claim.", "fake_lottery", True),
    ("I am calling from SBI bank. Your account will be blocked. Share your OTP to verify.", "impersonation", True),
    ("I met you online and I am stuck at airport. Send money urgently for customs clearance.", "romance_scam", True),
    ("CBI officer here. Your PAN card is involved in money laundering. You must transfer Rs 2 lakh to prove innocence.", "digital_arrest", True),
    ("Your Aadhaar is linked to terrorist activity. This is Rajesh Kumar from ED. Do not disconnect.", "digital_arrest", True),
    ("URGENT: Update your Aadhaar KYC or account will be suspended. Click link: http://uidai-kyc.in", "fake_kyc", True),
    ("Exclusive crypto investment. Double your money in 30 days. Minimum Rs 10,000. Limited slots.", "fake_investment", True),
    ("Part time job available. Earn Rs 1000 daily. No experience needed. Pay Rs 200 registration fee.", "fake_job", True),
    ("You have been selected for Rs 50 lakh prize. Send Rs 1000 processing fee to claim.", "fake_lottery", True),
    ("Calling from RBI. Your account is frozen. Share OTP to unfreeze. Do not tell anyone.", "impersonation", True),
    ("I am a foreign doctor stuck in Syria. Please send $500 for flight ticket. I love you.", "romance_scam", True),
    
    # BENIGN TESTS (5 total)
    ("Hello, how are you? Hope you are doing well.", "legitimate", False),
    ("Meeting scheduled for tomorrow at 10 AM. Please confirm attendance.", "legitimate", False),
    ("Your order has been shipped. Track your package at amazon.in/track", "legitimate", False),
    ("Happy birthday! Wishing you a wonderful year ahead.", "legitimate", False),
    ("Please review the quarterly report attached. Let me know if you have questions.", "legitimate", False),
]

def run_accuracy_test():
    print("=" * 80)
    print("SENTINEL SCAMWatch ACCURACY TEST")
    print("=" * 80)
    print()
    
    results = []
    correct = 0
    false_positives = 0
    false_negatives = 0
    
    for i, (text, expected_type, is_scam) in enumerate(TEST_CASES, 1):
        try:
            result = run_scam_analysis(text=text, channel="test")
            detected_type = result.scam_type or "legitimate"
            risk_level = result.risk_level.value
            
            # Determine if detection was correct
            if is_scam:
                detected_scam = detected_type != "legitimate" and risk_level in ["HIGH", "CRITICAL"]
                is_correct = detected_scam
                if not detected_scam:
                    false_negatives += 1
            else:
                detected_scam = detected_type != "legitimate" and risk_level in ["HIGH", "CRITICAL"]
                is_correct = not detected_scam
                if detected_scam:
                    false_positives += 1
            
            if is_correct:
                correct += 1
            
            status = "✓" if is_correct else "✗"
            results.append({
                "num": i,
                "text_preview": text[:50] + "..." if len(text) > 50 else text,
                "expected": expected_type,
                "detected": detected_type,
                "risk": risk_level,
                "correct": is_correct,
                "status": status,
            })
            
        except Exception as e:
            results.append({
                "num": i,
                "text_preview": text[:50] + "...",
                "expected": expected_type,
                "detected": "ERROR",
                "risk": "N/A",
                "correct": False,
                "status": "✗",
            })
            false_negatives += 1
    
    # Print results table
    print(f"{'#':<4} {'Status':<8} {'Expected':<15} {'Detected':<15} {'Risk':<10} {'Text Preview'}")
    print("-" * 80)
    for r in results:
        print(f"{r['num']:<4} {r['status']:<8} {r['expected']:<15} {r['detected']:<15} {r['risk']:<10} {r['text_preview']}")
    
    # Print summary
    total = len(TEST_CASES)
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests:       {total}")
    print(f"Correct:           {correct}")
    print(f"Accuracy:          {accuracy:.1f}%")
    print(f"False positives:   {false_positives} (benign detected as scam)")
    print(f"False negatives:   {false_negatives} (scam detected as benign)")
    print("=" * 80)
    
    return accuracy, false_positives, false_negatives

if __name__ == "__main__":
    run_accuracy_test()
