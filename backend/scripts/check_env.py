"""
Environment readiness check for KiranaStudio backend.
Validates Python version, dependencies, FFmpeg, and optional AWS/config.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Python version (POC requires 3.11)
REQUIRED_PYTHON = (3, 11)

# Required packages (import name -> pip name)
PACKAGES = [
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn[standard]"),
    ("boto3", "boto3"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic-settings"),
    ("dotenv", "python-dotenv"),
    ("cv2", "opencv-python"),
    ("imagehash", "imagehash"),
    ("numpy", "numpy"),
    ("python_multipart", "python-multipart"),
]


def check_python() -> bool:
    v = sys.version_info
    ok = (v.major, v.minor) >= REQUIRED_PYTHON
    req = f"{REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+"
    print(f"  Python {v.major}.{v.minor}.{v.micro}: {'OK' if ok else 'FAIL (need ' + req + ')'}")
    return ok


def check_packages() -> bool:
    all_ok = True
    for mod, pip_name in PACKAGES:
        try:
            __import__(mod)
            print(f"  {pip_name}: OK")
        except ImportError as e:
            print(f"  {pip_name}: MISSING ({e})")
            all_ok = False
    return all_ok


def check_ffmpeg() -> bool:
    ffmpeg = shutil.which("ffmpeg")
    ok = ffmpeg is not None
    print(f"  ffmpeg on PATH: {'OK' if ok else 'MISSING (required for frame extraction)'}")
    if ffmpeg:
        print(f"    -> {ffmpeg}")
    return ok


def check_config() -> None:
    try:
        from app.config.settings import get_settings
        s = get_settings()
        print("  Config (.env / env): loaded")
        print(f"    environment={s.environment}, api_prefix={s.api_v1_prefix}")
        print(f"    aws_region={s.aws_region}")
        print(f"    s3 buckets: videos={s.s3_videos_bucket}, frames={s.s3_frames_bucket}, images={s.s3_images_bucket}")
        print(f"    dynamodb: jobs={s.jobs_table_name}, catalogs={s.catalogs_table_name}")
        has_creds = bool(s.aws_access_key_id and s.aws_secret_access_key)
        print(f"    AWS credentials set: {'yes' if has_creds else 'no (use .env or default credential chain)'}")
    except Exception as e:
        print(f"  Config: WARN - {e}")


def main() -> int:
    print("KiranaStudio backend - environment readiness\n")
    print("1. Python version")
    py_ok = check_python()
    print("\n2. Dependencies (import check)")
    pkg_ok = check_packages()
    print("\n3. FFmpeg (frame extraction)")
    ff_ok = check_ffmpeg()
    print("\n4. Config (optional)")
    check_config()
    print()
    if py_ok and pkg_ok and ff_ok:
        print("Ready. Start server: uvicorn app.main:app --reload")
        return 0
    print("Fix the failures above (e.g. pip install -r requirements.txt, install FFmpeg).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
