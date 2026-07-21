"""
Individual security feature checks for Indian currency notes.
Each check returns a FeatureCheckResult-compatible dict.
All checks use OpenCV and numpy only — no ML model required.
"""

import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


def check_aspect_ratio(image: np.ndarray, denomination: str) -> dict:
    """
    Check if note dimensions match RBI standard aspect ratios.
    Indian currency notes have fixed width:height ratios per denomination.
    """
    EXPECTED_RATIOS = {
        "50":   2.36,
        "100":  2.36,
        "200":  2.36,
        "500":  2.36,
        "2000": 2.44,
        "unknown": 2.36
    }

    h, w = image.shape[:2]
    actual_ratio = w / h if h > 0 else 0
    expected = EXPECTED_RATIOS.get(denomination, 2.36)
    deviation = abs(actual_ratio - expected) / expected

    passed = deviation < 0.15
    confidence = max(0.0, 1.0 - (deviation / 0.15)) if not passed else 0.85

    return {
        "feature_name": "Aspect Ratio",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Detected ratio {actual_ratio:.2f}, expected ~{expected:.2f} "
                   f"(deviation: {deviation*100:.1f}%)"
    }


def check_color_distribution(image: np.ndarray, denomination: str) -> dict:
    """
    Analyze color channel distribution.
    Genuine notes have consistent ink saturation patterns.
    Counterfeits often show oversaturation or color bleeding.
    """
    COLOR_PROFILES = {
        "500":  {"dominant": "b", "min_saturation": 40, "max_saturation": 180},
        "2000": {"dominant": "r", "min_saturation": 35, "max_saturation": 175},
        "100":  {"dominant": "g", "min_saturation": 40, "max_saturation": 170},
        "200":  {"dominant": "y", "min_saturation": 38, "max_saturation": 172},
        "50":   {"dominant": "g", "min_saturation": 35, "max_saturation": 168},
    }

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    mean_sat = float(np.mean(saturation))
    std_sat = float(np.std(saturation))

    profile = COLOR_PROFILES.get(denomination, {"min_saturation": 30, "max_saturation": 190})
    in_range = profile["min_saturation"] <= mean_sat <= profile["max_saturation"]
    low_variance = std_sat < 80

    passed = in_range and low_variance
    confidence = 0.75 if passed else 0.40

    return {
        "feature_name": "Color Distribution",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Mean saturation: {mean_sat:.1f}, Std dev: {std_sat:.1f}. "
                   f"{'Within' if in_range else 'Outside'} expected range. "
                   f"Variance {'acceptable' if low_variance else 'too high'}."
    }


def check_security_thread_region(image: np.ndarray) -> dict:
    """
    Detect security thread region.
    Genuine Indian notes have a windowed security thread ~1/3 from left edge.
    Detected by looking for a vertical band with distinct intensity pattern.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    thread_start = int(w * 0.28)
    thread_end = int(w * 0.38)
    thread_region = gray[:, thread_start:thread_end]

    col_means = np.mean(thread_region, axis=0)
    variance = float(np.var(col_means))
    mean_intensity = float(np.mean(thread_region))

    has_thread_variance = variance > 100
    reasonable_intensity = 40 < mean_intensity < 220

    passed = has_thread_variance and reasonable_intensity
    confidence = 0.70 if passed else 0.35

    return {
        "feature_name": "Security Thread Region",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Thread region intensity variance: {variance:.1f}, "
                   f"mean intensity: {mean_intensity:.1f}. "
                   f"{'Thread pattern detected' if passed else 'No clear thread pattern found'}."
    }


def check_serial_number_zone(image: np.ndarray) -> dict:
    """
    Check serial number zone for text-like features.
    Genuine notes have sharp, high-contrast serial number printing.
    Detected via edge density in expected serial number regions.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    zones = [
        gray[int(h*0.08):int(h*0.22), int(w*0.55):int(w*0.95)],
        gray[int(h*0.75):int(h*0.92), int(w*0.05):int(w*0.45)],
    ]

    zone_results = []
    for zone in zones:
        if zone.size == 0:
            continue
        edges = cv2.Canny(zone, 50, 150)
        edge_density = float(np.sum(edges > 0)) / edges.size
        zone_results.append(edge_density)

    if not zone_results:
        return {
            "feature_name": "Serial Number Zone",
            "passed": False,
            "confidence": 0.3,
            "details": "Could not extract serial number zones from image."
        }

    max_density = max(zone_results)
    passed = max_density > 0.03
    confidence = min(0.85, max_density * 15) if passed else 0.30

    return {
        "feature_name": "Serial Number Zone",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Serial zone edge density: {max_density:.4f}. "
                   f"{'Sharp text features detected' if passed else 'Weak or absent text features'}."
    }


def check_watermark_region(image: np.ndarray) -> dict:
    """
    Check watermark region (Gandhi portrait area).
    Located ~15-35% from left edge.
    Genuine notes show subtle intensity variation in this region.
    """
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    watermark_region = gray[int(h*0.15):int(h*0.85), int(w*0.12):int(w*0.32)]

    if watermark_region.size == 0:
        return {
            "feature_name": "Watermark Region",
            "passed": False,
            "confidence": 0.3,
            "details": "Could not extract watermark region."
        }

    local_std = float(np.std(watermark_region))
    mean_val = float(np.mean(watermark_region))

    has_variation = local_std > 15
    reasonable_brightness = 80 < mean_val < 210

    passed = has_variation and reasonable_brightness
    confidence = 0.72 if passed else 0.32

    return {
        "feature_name": "Watermark Region",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Watermark region std deviation: {local_std:.1f}, "
                   f"mean brightness: {mean_val:.1f}. "
                   f"{'Watermark pattern present' if passed else 'No watermark variation detected'}."
    }


def check_edge_sharpness(image: np.ndarray) -> dict:
    """
    Check overall print sharpness via Laplacian variance.
    Genuine notes are printed with high precision — sharp edges throughout.
    Photocopied or inkjet counterfeits show lower sharpness scores.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    passed = laplacian_var > 200
    confidence = min(0.90, laplacian_var / 800) if passed else max(0.20, laplacian_var / 1000)

    return {
        "feature_name": "Print Sharpness",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": f"Laplacian variance: {laplacian_var:.1f}. "
                   f"{'Sharp print quality detected' if passed else 'Low sharpness — possible photocopy or low-quality print'}. "
                   f"Threshold: 200."
    }


def check_image_quality(image: np.ndarray) -> dict:
    """
    Basic image quality gate.
    Reject images that are too small, too dark, or too blurry to analyze.
    """
    h, w = image.shape[:2]

    too_small = h < 100 or w < 200
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    mean_brightness = float(np.mean(gray))
    too_dark = mean_brightness < 30
    too_bright = mean_brightness > 240

    passed = not too_small and not too_dark and not too_bright
    issues = []
    if too_small:
        issues.append(f"image too small ({w}x{h}px)")
    if too_dark:
        issues.append(f"image too dark (brightness: {mean_brightness:.0f})")
    if too_bright:
        issues.append(f"image too bright (brightness: {mean_brightness:.0f})")

    return {
        "feature_name": "Image Quality",
        "passed": passed,
        "confidence": 0.95 if passed else 0.10,
        "details": f"Resolution: {w}x{h}px, brightness: {mean_brightness:.0f}/255. "
                   + (f"Issues: {', '.join(issues)}" if issues else "Image quality acceptable.")
    }


def check_not_play_money(image: np.ndarray) -> dict:
    """
    Detect play money, monopoly notes, or obvious non-currency images.
    Real Indian currency has specific characteristics that play money lacks.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    h, w = image.shape[:2]

    # Check 1: Color variance — real notes have rich, varied colors
    # Play money often has flat, uniform colors
    saturation = gray[:, :, 1]
    sat_std = float(np.std(saturation))
    sat_mean = float(np.mean(saturation))

    # Check 2: Edge complexity — real notes have intricate patterns
    gray_bgr = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_bgr, 50, 150)
    edge_density = float(np.sum(edges > 0)) / edges.size

    # Check 3: Texture complexity — real notes have microprint and security features
    # Use Laplacian to measure texture
    laplacian = cv2.Laplacian(gray_bgr, cv2.CV_64F)
    texture_complexity = float(np.std(laplacian))

    # Check 4: Color channel distribution — real notes have specific ink patterns
    b, g, r = cv2.split(image)
    channel_std = float(np.std([np.std(b), np.std(g), np.std(r)]))

    # Decision logic
    issues = []
    is_play_money = False

    # Very low saturation variance suggests flat/uniform colors (play money)
    if sat_std < 15:
        issues.append(f"very low color variance (std: {sat_std:.1f})")
        is_play_money = True

    # Very low edge density suggests simple/flat design
    if edge_density < 0.02:
        issues.append(f"very low edge density ({edge_density:.4f})")
        is_play_money = True

    # Very low texture suggests no microprint/security features
    if texture_complexity < 20:
        issues.append(f"very low texture complexity ({texture_complexity:.1f})")
        is_play_money = True

    # Low channel variance suggests uniform coloring
    if channel_std < 10:
        issues.append(f"low color channel variance ({channel_std:.1f})")
        is_play_money = True

    # Multiple red flags = likely play money
    if len(issues) >= 2:
        passed = False
        confidence = 0.90
        details = f"SUSPECTED PLAY MONEY: {'; '.join(issues)}. This appears to be a play note, monopoly money, or non-genuine image."
    elif len(issues) == 1:
        passed = True
        confidence = 0.50
        details = f"Minor concern: {issues[0]}. Proceeding with analysis but results may be unreliable."
    else:
        passed = True
        confidence = 0.85
        details = f"Image appears to be genuine currency paper. Saturation std: {sat_std:.1f}, edge density: {edge_density:.4f}, texture: {texture_complexity:.1f}."

    return {
        "feature_name": "Genuine Currency Paper",
        "passed": passed,
        "confidence": round(confidence, 3),
        "details": details
    }
