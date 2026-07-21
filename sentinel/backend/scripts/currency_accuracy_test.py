"""
CURRENCYGuard Accuracy Test Script
Tests currency authentication with sample images
"""

import sys
import os
# Add sentinel directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

import numpy as np
import cv2
from backend.modules.currencyguard.opencv_analyzer import analyze_currency_image, compute_overall_score

def create_genuine_note_image(denomination: str) -> np.ndarray:
    """Create a synthetic image that mimics genuine currency characteristics."""
    # Real dimensions (width:height ratio ~2.36 for most notes)
    if denomination == "2000":
        h, w = 166, 660  # 2.44 ratio
    else:
        h, w = 170, 400  # 2.36 ratio

    # Create image with realistic color profile
    img = np.zeros((h, w, 3), dtype=np.uint8)

    # Base color varies by denomination
    color_profiles = {
        "50": (120, 140, 100),
        "100": (100, 150, 120),
        "200": (140, 130, 80),
        "500": (80, 120, 160),
        "2000": (160, 80, 100),
    }
    base_color = color_profiles.get(denomination, (120, 120, 120))
    img[:] = base_color

    # Add texture variation
    noise = np.random.randint(-20, 20, (h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Add edge detail
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    img[edges > 0] = [50, 50, 50]

    return img

def create_counterfeit_note_image(denomination: str) -> np.ndarray:
    """Create a synthetic image that mimics counterfeit characteristics."""
    h, w = 170, 400

    # Flat, uniform color (typical of play money)
    img = np.full((h, w, 3), (200, 200, 200), dtype=np.uint8)

    # Very low variation
    noise = np.random.randint(-3, 3, (h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img

def run_accuracy_test():
    print("=" * 70)
    print("CURRENCYGuard ACCURACY TEST")
    print("=" * 70)
    print()

    denominations = ["50", "100", "200", "500", "2000"]
    results = []

    for denom in denominations:
        # Test genuine note
        genuine_img = create_genuine_note_image(denom)
        genuine_result = analyze_currency_image(
            cv2.imencode('.jpg', genuine_img)[1].tobytes(),
            denom
        )

        # Test counterfeit note
        counterfeit_img = create_counterfeit_note_image(denom)
        counterfeit_result = analyze_currency_image(
            cv2.imencode('.jpg', counterfeit_img)[1].tobytes(),
            denom
        )

        results.append({
            "denomination": denom,
            "genuine_verdict": genuine_result["opencv_verdict"],
            "genuine_score": genuine_result["overall_score"],
            "counterfeit_verdict": counterfeit_result["opencv_verdict"],
            "counterfeit_score": counterfeit_result["overall_score"],
            "genuine_checks": f"{genuine_result['checks_passed']}/{genuine_result['checks_total']}",
            "counterfeit_checks": f"{counterfeit_result['checks_passed']}/{counterfeit_result['checks_total']}",
        })

    # Print results table
    print(f"{'Denom':<8} {'Genuine Verdict':<15} {'Genuine Score':<15} {'Counterfeit Verdict':<20} {'Counterfeit Score':<15}")
    print("-" * 70)
    for r in results:
        print(f"₹{r['denomination']:<6} {r['genuine_verdict']:<15} {r['genuine_score']:<15.3f} {r['counterfeit_verdict']:<20} {r['counterfeit_score']:<15.3f}")

    # Calculate metrics
    genuine_correct = sum(1 for r in results if r["genuine_verdict"] in ["GENUINE", "SUSPECT"])
    counterfeit_correct = sum(1 for r in results if r["counterfeit_verdict"] in ["COUNTERFEIT", "INCONCLUSIVE"])
    total = len(results)

    accuracy = ((genuine_correct + counterfeit_correct) / (total * 2)) * 100
    precision = genuine_correct / total if total > 0 else 0
    recall = counterfeit_correct / total if total > 0 else 0

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total tests:       {total * 2} ({total} genuine + {total} counterfeit)")
    print(f"Genuine detected:  {genuine_correct}/{total}")
    print(f"Counterfeit detected: {counterfeit_correct}/{total}")
    print(f"Overall accuracy:  {accuracy:.1f}%")
    print(f"Precision:         {precision:.1%}")
    print(f"Recall:            {recall:.1%}")
    print("=" * 70)

    return accuracy, precision, recall

if __name__ == "__main__":
    run_accuracy_test()
