# ============================================================
# Main Pipeline Runner
# Image Analyst Assignment – GalaxEye
# ============================================================

import os
import subprocess


def run_script(script_name):
    """
    Utility function to execute a Python script
    and stop execution if it fails.
    """
    print(f"\n▶ Running {script_name} ...")

    result = subprocess.run(["python", script_name])

    if result.returncode != 0:
        raise Exception(f"❌ {script_name} failed.")
    else:
        print(f"✅ {script_name} completed successfully.")


def main():
    print("=================================================")
    print("🚀 Multi-Sensor Satellite Processing Pipeline")
    print("=================================================")

    # Step 1 – Data Ingestion
    run_script("ingestion/Data_Ingestion.py")

    # Step 2 – Sentinel-1 Processing (run in background so figures don't block)
    print("\n▶ Running preprocessing/Sentinel-1_Processing.py ...")
    p_s1 = subprocess.Popen(["python", "preprocessing/Sentinel-1_Processing.py"])

    # Step 3 – Sentinel-2 Processing (starts immediately, no need to close S1 figures)
    run_script("preprocessing/Sentinel-2_Processing.py")

    # Wait for Sentinel-1 to finish (user can close S1 figures anytime)
    p_s1.wait()
    if p_s1.returncode != 0:
        raise Exception("❌ preprocessing/Sentinel-1_Processing.py failed.")
    print("✅ preprocessing/Sentinel-1_Processing.py completed successfully.")

    print("\n🎉 Entire Pipeline Completed Successfully.")


if __name__ == "__main__":
    main()