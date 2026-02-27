# ================================================================
# Sentinel-2 NDVI Processing Pipeline
# Includes:
# 1) Unzip product
# 2) Locate SAFE structure
# 3) Read B04 & B08 (10m)
# 4) Compute NDVI
# 5) Read SCL (20m) and resample
# 6) Cloud masking
# ================================================================

import glob
import os
import zipfile
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from skimage.transform import resize

# ================================================================
# STEP 0 — UNZIP SENTINEL-2 PRODUCT
# ================================================================

# Folder where Sentinel-2 ZIP is stored (project-relative, cross-platform)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(PROJECT_ROOT, "data")

# Folder where contents will be extracted
OUT = os.path.join(FOLDER, "extracted")
os.makedirs(OUT, exist_ok=True)

# Output folder for generated results (figures + rasters)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "sentinel2")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Full ZIP path
zip_path = os.path.join(FOLDER, "Sentinel2_product.zip")
print("ZIP Found:", zip_path)

# Extract all files into OUT folder
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(OUT)

print("Extraction Completed")

# ================================================================
# STEP 1 — Locate SAFE Folder and Required Bands
# ================================================================

# After extraction, find Sentinel-2 SAFE folder
base_folder = OUT
s2_safe = glob.glob(os.path.join(base_folder, "*S2*.SAFE"))[0]

# Path to Red band (B04 - 10m resolution)
b4_path = glob.glob(os.path.join(
    s2_safe, "GRANULE", "*", "IMG_DATA", "R10m", "*B04_10m.jp2"
))[0]

# Path to NIR band (B08 - 10m resolution)
b8_path = glob.glob(os.path.join(
    s2_safe, "GRANULE", "*", "IMG_DATA", "R10m", "*B08_10m.jp2"
))[0]

# Path to Scene Classification Layer (20m resolution)
scl_path = glob.glob(os.path.join(
    s2_safe, "GRANULE", "*", "IMG_DATA", "R20m", "*SCL_20m.jp2"
))[0]

print("B04 Path:", b4_path)
print("B08 Path:", b8_path)
print("SCL Path:", scl_path)

# ================================================================
# STEP 2 — Read Bands (Window-Based for Memory Safety)
# ================================================================

# Define window size (same used in SAR processing)
window_size = 4000

# Read Red band (B04)
with rasterio.open(b4_path) as src:
    red = src.read(
        1,
        window=rasterio.windows.Window(0, 0, window_size, window_size)
    ).astype(np.float32)

# Read NIR band (B08)
with rasterio.open(b8_path) as src:
    nir = src.read(
        1,
        window=rasterio.windows.Window(0, 0, window_size, window_size)
    ).astype(np.float32)

# Convert digital numbers to reflectance
red = red / 10000.0
nir = nir / 10000.0

# ================================================================
# STEP 3 — Compute NDVI
# ================================================================

# NDVI formula
ndvi = (nir - red) / (nir + red + 1e-10)

print("NDVI Min:", np.nanmin(ndvi))
print("NDVI Max:", np.nanmax(ndvi))

# Plot raw NDVI
plt.figure(figsize=(7,6))
plt.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
plt.title("NDVI (Raw)")
plt.colorbar(label="NDVI")
plt.savefig(os.path.join(OUTPUT_DIR, "s2_ndvi_raw.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s2_ndvi_raw.png")

# ================================================================
# STEP 4 — Read SCL (20m) and Resample to 10m Grid
# ================================================================

# Read SCL window (20m resolution → half window size)
with rasterio.open(scl_path) as src:
    scl = src.read(
        1,
        window=rasterio.windows.Window(0, 0, window_size//2, window_size//2)
    )

# Resample SCL to match NDVI shape (nearest neighbor)
scl_resampled = resize(
    scl,
    ndvi.shape,
    order=0,               # nearest neighbor (keeps class values)
    preserve_range=True,
    anti_aliasing=False
)

# ================================================================
# STEP 5 — Cloud Masking Using SCL
# ================================================================

# SCL classes:
# 3  = Cloud shadow
# 8  = Medium cloud
# 9  = High cloud
# 10 = Thin cirrus
# 11 = Snow/Ice

cloud_mask = np.isin(scl_resampled, [3, 8, 9, 10, 11])

# Apply cloud mask to NDVI
ndvi_masked = np.where(cloud_mask, np.nan, ndvi)

# Plot cloud-masked NDVI
plt.figure(figsize=(7,6))
plt.imshow(ndvi_masked, cmap='RdYlGn', vmin=-1, vmax=1)
plt.title("NDVI (Cloud Masked)")
plt.colorbar(label="NDVI")
plt.savefig(os.path.join(OUTPUT_DIR, "s2_ndvi_cloud_masked.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s2_ndvi_cloud_masked.png")

# Save processed rasters
with rasterio.open(b4_path) as src:
    window = rasterio.windows.Window(0, 0, window_size, window_size)
    profile = src.profile.copy()
    profile.update(
        driver="GTiff",
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan,
        transform=src.window_transform(window),
        height=window_size,
        width=window_size,
    )
    ndvi_path = os.path.join(OUTPUT_DIR, "s2_ndvi.tif")
    ndvi_masked_path = os.path.join(OUTPUT_DIR, "s2_ndvi_cloud_masked.tif")
    with rasterio.open(ndvi_path, "w", **profile) as dst:
        dst.write(ndvi.astype(np.float32), 1)
    with rasterio.open(ndvi_masked_path, "w", **profile) as dst:
        dst.write(ndvi_masked.astype(np.float32), 1)
    print(f"Saved: {ndvi_path}")
    print(f"Saved: {ndvi_masked_path}")

# Display all figures at once
plt.show()