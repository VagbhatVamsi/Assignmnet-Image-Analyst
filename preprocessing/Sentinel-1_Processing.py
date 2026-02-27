import numpy as np
import rasterio
import matplotlib.pyplot as plt
import glob
import os, zipfile

# Base folder containing the ZIP (project-relative, cross-platform)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDER = os.path.join(PROJECT_ROOT, "data")

# Output folder for extraction
OUT = os.path.join(FOLDER, "extracted")
os.makedirs(OUT, exist_ok=True)

# Output folder for generated results (figures + rasters)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "sentinel1")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Full path of Sentinel-1 ZIP
zip_path = os.path.join(FOLDER, "Sentinel1_product.zip")
print("ZIP Found:", zip_path)

# Extract ZIP
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(OUT)

print("Extraction Done")

# Find SAFE folder after extraction
s1_safe = glob.glob(os.path.join(OUT, "*S1*.SAFE"))[0]

# Go to measurement folder
measurement_folder = os.path.join(s1_safe, "measurement")

# Find VH file inside measurement folder
vh_path = glob.glob(os.path.join(measurement_folder, "*vh*.tif*"))[0]

print("VH Path:", vh_path)

# ================================================================
# Read VH Image
# ================================================================

with rasterio.open(vh_path) as src:
    window = rasterio.windows.Window(0, 0, 4000, 4000)
    vh = src.read(1, window=window).astype(np.float32)
# ================================================================
# STEP 1 — Scale Back to True Linear Sigma0
# ================================================================

sigma0_linear = vh / 10000.0

print("Linear Min:", np.min(sigma0_linear))
print("Linear Max:", np.max(sigma0_linear))


# ================================================================
# STEP 2 — Convert to dB
# ================================================================

sigma0_db = 10 * np.log10(sigma0_linear + 1e-10)

print("Before Masking dB Min:", np.nanmin(sigma0_db))
print("Before Masking dB Max:", np.nanmax(sigma0_db))


# ================================================================
# STEP 3 — Mask Unrealistic Values
# ================================================================

sigma0_db[sigma0_db < -40] = np.nan
sigma0_db[sigma0_db > 5] = np.nan

print("After Masking dB Min:", np.nanmin(sigma0_db))
print("After Masking dB Max:", np.nanmax(sigma0_db))
print("Number of NaNs:", np.isnan(sigma0_db).sum())

# ================================================================
# Memory-Safe Plotting (Downsampled View)
# ================================================================

factor = 5

sigma_small = sigma0_db[::factor, ::factor]

plt.figure(figsize=(8,6))
plt.imshow(sigma_small, cmap='gray', vmin=-25, vmax=5)
plt.title(f"Sentinel-1 VH (Sigma0 dB) - Downsampled x{factor}")
plt.colorbar(label="Backscatter (dB)")
plt.savefig(os.path.join(OUTPUT_DIR, "s1_sigma0_db_downsampled.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s1_sigma0_db_downsampled.png")


# ================================================================
# STEP 6A — Read Manageable Window
# ================================================================

window_size = 4000

with rasterio.open(vh_path) as src:
    window = rasterio.windows.Window(0, 0, window_size, window_size)
    vh_window = src.read(1, window=window).astype(np.float32)

sigma0_linear = vh_window / 10000.0
sigma0_db_window = 10 * np.log10(sigma0_linear + 1e-10)

sigma0_db_window[sigma0_db_window < -40] = np.nan
sigma0_db_window[sigma0_db_window > 5] = np.nan

print("Window Shape:", sigma0_db_window.shape)
print("Window Min:", np.nanmin(sigma0_db_window))
print("Window Max:", np.nanmax(sigma0_db_window))


# ================================================================
# STEP 6B — Lee Filter on Window
# ================================================================

from scipy.ndimage import uniform_filter

temp = np.nan_to_num(sigma0_db_window, nan=-40)

mean = uniform_filter(temp, size=5)
mean_sq = uniform_filter(temp**2, size=5)

variance = mean_sq - mean**2
overall_variance = np.var(temp)

lee_filtered = mean + (variance / (variance + overall_variance)) * (temp - mean)

lee_filtered[np.isnan(sigma0_db_window)] = np.nan

plt.figure(figsize=(7,6))
plt.imshow(lee_filtered, cmap='gray', vmin=-25, vmax=5)
plt.title("Lee Filtered SAR VH (Window)")
plt.colorbar(label="Backscatter (dB)")
plt.savefig(os.path.join(OUTPUT_DIR, "s1_lee_filtered.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s1_lee_filtered.png")


patch_before = sigma0_db_window[1000:1500, 1000:1500]
patch_after  = lee_filtered[1000:1500, 1000:1500]

plt.figure(figsize=(14,6))

plt.subplot(1,2,1)
plt.imshow(patch_before, cmap='gray', vmin=-25, vmax=5)
plt.title("Before Filtering (Zoom)")

plt.subplot(1,2,2)
plt.imshow(patch_after, cmap='gray', vmin=-25, vmax=5)
plt.title("After Lee Filtering (Zoom)")

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "s1_before_after_filtering.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s1_before_after_filtering.png")


# ================================================================
# STEP 7 — GLCM Texture (Small Patch)
# ================================================================

from skimage.feature import graycomatrix, graycoprops
from skimage.util import img_as_ubyte

patch = lee_filtered[1000:1200, 1000:1200]

norm_patch = (patch - np.nanmin(patch)) / \
             (np.nanmax(patch) - np.nanmin(patch))

patch_uint8 = img_as_ubyte(np.nan_to_num(norm_patch))

glcm = graycomatrix(
    patch_uint8,
    distances=[1],
    angles=[0],
    levels=256,
    symmetric=True,
    normed=True
)

contrast = graycoprops(glcm, 'contrast')[0,0]

print("GLCM Contrast:", contrast)

plt.figure(figsize=(5,5))
plt.imshow(patch_uint8, cmap='gray')
plt.title("Texture Patch")
plt.colorbar()
plt.savefig(os.path.join(OUTPUT_DIR, "s1_texture_patch.png"), dpi=150, bbox_inches="tight")
print(f"Saved: {OUTPUT_DIR}/s1_texture_patch.png")

# Save processed rasters
with rasterio.open(vh_path) as src:
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
    lee_path = os.path.join(OUTPUT_DIR, "s1_lee_filtered.tif")
    with rasterio.open(lee_path, "w", **profile) as dst:
        dst.write(lee_filtered.astype(np.float32), 1)
    print(f"Saved: {lee_path}")

# Display all figures at once
plt.show()