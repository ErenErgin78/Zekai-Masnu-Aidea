"""
ML & SoilType API Integration Test (No Mocks)
--------------------------------------------
Bu script, canlı çalışan API'leri test eder:
- Main API kök ve health
- SoilType health ve manuel analiz
- ML health, Auto analiz ve Manual analiz

Çalıştırma:
    python test_ml_api.py
"""

import json
import sys
from typing import Any, Dict

import requests


BASE_URL = "http://localhost:8000"          # Main + SoilType
SOIL_BASE = f"{BASE_URL}/soiltype"
ML_BASE = "http://localhost:8003/ml"         # ML standalone (8003)

# Kısa timeoutları merkezi tanımla
TIMEOUT_GET = 5
TIMEOUT_POST = (5, 8)       # (connect, read) for SoilType/Main
TIMEOUT_POST_ML = (5, 25)   # ML analyze can take longer due to internal fallbacks


def get(url: str) -> requests.Response:
    """GET isteği (kısa timeout ve basit hata yakalama)."""
    try:
        return requests.get(url, timeout=TIMEOUT_GET)
    except Exception as e:
        print(f"GET error: {url} -> {e}")
        raise


def post(url: str, payload: Dict[str, Any]) -> requests.Response:
    """POST isteği (kısa timeout ve basit hata yakalama)."""
    try:
        # Route ML calls to longer timeout
        timeout = TIMEOUT_POST_ML if "/ml/" in url else TIMEOUT_POST
        return requests.post(url, json=payload, timeout=timeout)
    except Exception as e:
        print(f"POST error: {url} -> {e}")
        raise


def pretty(obj: Any) -> str:
    """JSON çıktısını okunabilir yazdır."""
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def check_main_health() -> bool:
    print("\n1) Main API Health")
    try:
        r = get(f"{BASE_URL}/health")
        print(f"HTTP {r.status_code}")
        if r.ok:
            print(pretty(r.json()))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def check_soil_health() -> bool:
    print("\n2) SoilType Health")
    try:
        r = get(f"{SOIL_BASE}/health")
        print(f"HTTP {r.status_code}")
        if r.ok:
            print(pretty(r.json()))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def check_ml_health() -> bool:
    print("\n3) ML API Health")
    try:
        r = get(f"{ML_BASE}/health")
        print(f"HTTP {r.status_code}")
        if r.ok:
            print(pretty(r.json()))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def soil_manual_test(longitude: float = 35.0, latitude: float = 39.0) -> bool:
    print("\n4) SoilType Manual Analyze")
    payload = {"method": "Manual", "longitude": longitude, "latitude": latitude}
    try:
        r = post(f"{SOIL_BASE}/analyze", payload)
        print(f"HTTP {r.status_code}")
        if r.ok:
            data = r.json()
            print(pretty({k: data.get(k) for k in ["success", "soil_id", "coordinates", "classification"]}))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def ml_auto_test() -> bool:
    print("\n5) ML Analyze (Auto)")
    payload = {"method": "Auto"}
    try:
        r = post(f"{ML_BASE}/analyze", payload)
        print(f"HTTP {r.status_code}")
        if r.ok:
            data = r.json()
            print(pretty({k: data.get(k) for k in ["success", "coordinates", "recommendations", "model_info"]}))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def ml_manual_test(longitude: float = 35.0, latitude: float = 39.0) -> bool:
    print("\n6) ML Analyze (Manual)")
    payload = {"method": "Manual", "coordinates": {"longitude": longitude, "latitude": latitude}}
    try:
        r = post(f"{ML_BASE}/analyze", payload)
        print(f"HTTP {r.status_code}")
        if r.ok:
            data = r.json()
            print(pretty({k: data.get(k) for k in ["success", "coordinates", "recommendations", "model_info"]}))
            return True
        print(r.text)
        return False
    except Exception:
        return False


def main() -> int:
    print("\n=== ML & SoilType Integration Test (No Mocks) ===")
    ok_main = check_main_health()
    ok_soil = check_soil_health()
    ok_ml = check_ml_health()

    # Soil manual zorunlu: SoilType'ın gerçekten çalıştığını doğrular
    ok_soil_manual = soil_manual_test()

    # ML Auto ve Manual
    ok_ml_auto = ml_auto_test()
    ok_ml_manual = ml_manual_test()

    all_ok = all([ok_main, ok_soil, ok_ml, ok_soil_manual, ok_ml_auto or ok_ml_manual])

    print("\n--- Summary ---")
    print(f"Main Health:        {'OK' if ok_main else 'FAIL'}")
    print(f"SoilType Health:    {'OK' if ok_soil else 'FAIL'}")
    print(f"ML Health:          {'OK' if ok_ml else 'FAIL'}")
    print(f"Soil Manual:        {'OK' if ok_soil_manual else 'FAIL'}")
    print(f"ML Auto:            {'OK' if ok_ml_auto else 'FAIL'}")
    print(f"ML Manual:          {'OK' if ok_ml_manual else 'FAIL'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    # Script'i çalıştıran kullanıcıya exit code ile sonuç bildir
    sys.exit(main())


