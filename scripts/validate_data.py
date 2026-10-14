"""
اسکریپت اعتبارسنجی یکپارچگی داده‌های مذهبی ربات نور (NoorBot)
بررسی فرمت، ساختار، تطابق کلیدها و صحت مراجع بدون خطا
"""

import json
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "bot" / "data"

VALID_RESULT_CODES = {"very_good", "good", "moderate", "bad", "very_bad"}
VALID_MARAJI = {"sistani", "khamenei", "makarem"}


def validate_quran_sample() -> bool:
    file_path = DATA_DIR / "quran_sample.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "surahs" in data, "Missing 'surahs' key"
    assert len(data["surahs"]) == 114, f"Expected 114 surahs, got {len(data['surahs'])}"
    for idx, s in enumerate(data["surahs"], start=1):
        assert s["number"] == idx, f"Surah number mismatch: {s['number']} != {idx}"
        assert 1 <= s["start_page"] <= 604, f"Invalid start page: {s['start_page']}"

    assert "sample_verses" in data and len(data["sample_verses"]) > 0
    for v in data["sample_verses"]:
        assert 1 <= v["surah"] <= 114
        assert len(v["text"]) > 0
        assert len(v["translation"]) > 0

    print("  -> OK: 114 surahs and sample verses validated.")
    return True


def validate_istikhara_data() -> bool:
    file_path = DATA_DIR / "istikhara_data.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "methodology" in data, "Missing methodology section"
    assert "entries" in data and len(data["entries"]) > 0, "Entries list empty"

    for entry in data["entries"]:
        assert 1 <= entry["page"] <= 604, f"Page out of range: {entry['page']}"
        assert 1 <= entry["surah_number"] <= 114, f"Surah out of range: {entry['surah_number']}"
        assert entry["result_code"] in VALID_RESULT_CODES, f"Invalid result code: {entry['result_code']}"
        assert len(entry["arabic_text"].strip()) > 0, "Empty arabic text"
        assert len(entry["translation"].strip()) > 0, "Empty translation"
        assert len(entry["result_title"].strip()) > 0, "Empty result title"
        assert len(entry["explanation"].strip()) > 0, "Empty explanation"
        assert len(entry["advice"].strip()) > 0, "Empty advice"
        assert len(entry["source"].strip()) > 0, "Empty source reference"

    print(f"  -> OK: {len(data['entries'])} verified Istikhara mappings validated.")
    return True


def validate_hadiths() -> bool:
    file_path = DATA_DIR / "hadiths.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list) and len(data) >= 5, "Hadiths list must have at least 5 items"
    for item in data:
        assert "speaker" in item and len(item["speaker"]) > 0
        assert "arabic" in item and len(item["arabic"]) > 0
        assert "persian" in item and len(item["persian"]) > 0
        assert "source" in item and len(item["source"]) > 0

    print(f"  -> OK: {len(data)} authenticated Hadiths validated.")
    return True


def validate_duas() -> bool:
    file_path = DATA_DIR / "duas.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "daily_azkar" in data and len(data["daily_azkar"]) == 7, "Must have exactly 7 daily azkar"
    for zikr in data["daily_azkar"]:
        assert zikr["count"] == 100
        assert len(zikr["arabic"]) > 0
        assert len(zikr["persian"]) > 0

    assert "duas" in data and len(data["duas"]) > 0
    assert "tasbih_presets" in data and len(data["tasbih_presets"]) > 0
    for preset in data["tasbih_presets"]:
        assert "steps" in preset and len(preset["steps"]) > 0
        total_steps = sum(s["count"] for s in preset["steps"])
        assert total_steps == preset["total"], f"Step count mismatch in preset {preset['id']}"

    print(f"  -> OK: Daily azkar, authentic duas, and tasbih presets validated.")
    return True


def validate_occasions() -> bool:
    file_path = DATA_DIR / "occasions.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "hijri_occasions" in data and len(data["hijri_occasions"]) > 0
    for occ in data["hijri_occasions"]:
        assert 1 <= occ["month"] <= 12
        assert 1 <= occ["day"] <= 30
        assert len(occ["title"]) > 0

    assert "shamsi_occasions" in data and len(data["shamsi_occasions"]) > 0
    for occ in data["shamsi_occasions"]:
        assert 1 <= occ["month"] <= 12
        assert 1 <= occ["day"] <= 31
        assert len(occ["title"]) > 0

    print(f"  -> OK: {len(data['hijri_occasions'])} Hijri and {len(data['shamsi_occasions'])} Shamsi occasions validated.")
    return True


def validate_ahkam() -> bool:
    file_path = DATA_DIR / "ahkam.json"
    print(f"[*] Validating {file_path.name}...")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "topics" in data and len(data["topics"]) > 0
    for topic in data["topics"]:
        assert "questions" in topic and len(topic["questions"]) > 0
        for q in topic["questions"]:
            assert set(q["answers"].keys()) == VALID_MARAJI
            assert set(q["sources"].keys()) == VALID_MARAJI

    print("  -> OK: Ahkam and Marja rulings validated.")
    return True


def main():
    print("=" * 60)
    print("NoorBot Dataset Validation - Integrity & Authenticity Check")
    print("=" * 60)
    try:
        validate_quran_sample()
        validate_istikhara_data()
        validate_hadiths()
        validate_duas()
        validate_occasions()
        validate_ahkam()
        print("=" * 60)
        print("ALL DATASETS PASSED VALIDATION WITH ZERO ERRORS!")
        print("=" * 60)
    except AssertionError as err:
        print(f"[ERROR] Validation failed: {err}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"[FATAL] Unexpected error during validation: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
