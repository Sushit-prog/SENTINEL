"""
OpenCV-based currency note analyzer.
Orchestrates all feature checks and returns structured results.
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Tuple
from backend.modules.currencyguard.feature_checks import (
    check_aspect_ratio,
    check_color_distribution,
    check_security_thread_region,
    check_serial_number_zone,
    check_watermark_region,
    check_edge_sharpness,
    check_image_quality,
)

logger = logging.getLogger(__name__)


def detect_denomination(image: np.ndarray) -> str:
    """
    Attempt to detect denomination from image dimensions and color.
    Returns best guess or 'unknown'.
    """
    h, w = image.shape[:2]
    ratio = w / h if h > 0 else 0

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mean_hue = float(np.mean(hsv[:, :, 0]))

    if ratio > 2.40:
        return "2000"
    elif mean_hue < 20 or mean_hue > 160:
        return "500"
    elif 35 < mean_hue < 85:
        return "100"
    elif 85 < mean_hue < 130:
        return "200"
    else:
        return "unknown"


def preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Convert uploaded bytes to OpenCV BGR image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image. Ensure it is a valid JPG or PNG.")
    return image


def run_all_checks(image: np.ndarray, denomination: str) -> List[Dict]:
    """
    Run all security feature checks in order.
    Returns list of check result dicts.
    """
    checks = []

    quality = check_image_quality(image)
    checks.append(quality)

    if not quality["passed"]:
        logger.warning("Image quality check failed — skipping deep analysis")
        return checks

    checks.append(check_aspect_ratio(image, denomination))
    checks.append(check_color_distribution(image, denomination))
    checks.append(check_security_thread_region(image))
    checks.append(check_serial_number_zone(image))
    checks.append(check_watermark_region(image))
    checks.append(check_edge_sharpness(image))

    return checks


def compute_overall_score(checks: List[Dict]) -> Tuple[float, str]:
    """
    Compute weighted overall authenticity score from check results.
    Returns (score 0.0-1.0, verdict string).
    """
    WEIGHTS = {
        "Image Quality": 0.05,
        "Aspect Ratio": 0.10,
        "Color Distribution": 0.15,
        "Security Thread Region": 0.25,
        "Serial Number Zone": 0.20,
        "Watermark Region": 0.15,
        "Print Sharpness": 0.10,
    }

    total_weight = 0.0
    weighted_score = 0.0

    for check in checks:
        name = check["feature_name"]
        weight = WEIGHTS.get(name, 0.10)
        score = check["confidence"] if check["passed"] else (check["confidence"] * 0.3)
        weighted_score += weight * score
        total_weight += weight

    final_score = weighted_score / total_weight if total_weight > 0 else 0.0

    if final_score >= 0.72:
        verdict = "GENUINE"
    elif final_score >= 0.50:
        verdict = "SUSPECT"
    elif final_score >= 0.30:
        verdict = "COUNTERFEIT"
    else:
        verdict = "INCONCLUSIVE"

    return round(final_score, 3), verdict


def analyze_currency_image(image_bytes: bytes, denomination: str = "unknown") -> Dict:
    """
    Main entry point for OpenCV currency analysis.
    Returns structured analysis result.
    """
    image = preprocess_image(image_bytes)

    if denomination == "unknown":
        denomination = detect_denomination(image)
        logger.info(f"Auto-detected denomination: {denomination}")

    checks = run_all_checks(image, denomination)
    score, verdict = compute_overall_score(checks)

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)

    return {
        "denomination": denomination,
        "feature_checks": checks,
        "overall_score": score,
        "opencv_verdict": verdict,
        "checks_passed": passed_count,
        "checks_total": total_count,
        "image_shape": f"{image.shape[1]}x{image.shape[0]}px"
    }
