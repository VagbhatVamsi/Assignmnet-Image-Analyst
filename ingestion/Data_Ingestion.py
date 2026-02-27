# ===========================================================
# Copernicus Data Space – Sentinel-1 & Sentinel-2 Downloader
# ===========================================================

import requests
import os
from shapely.geometry import shape
from tqdm import tqdm

# -----------------------------------------------------------
# 1️⃣ USER INPUTS
# -----------------------------------------------------------

USERNAME = "vagbhat19@gmail.com"       # <-- Replace
PASSWORD = "Vagbhat@5794"    # <-- Replace

START_DATE = "2025-10-15T00:00:00Z"
END_DATE   = "2025-10-27T00:00:00Z"

AOI_POLYGON = (
    "POLYGON((78.30 17.20, "
    "78.30 17.60, "
    "78.70 17.60, "
    "78.70 17.20, "
    "78.30 17.20))"
)

# Project-relative data folder (cross-platform)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOAD_FOLDER = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# -----------------------------------------------------------
# 2️⃣ AUTHENTICATION
# -----------------------------------------------------------

auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

auth_data = {
    "client_id": "cdse-public",
    "grant_type": "password",
    "username": USERNAME,
    "password": PASSWORD
}

response = requests.post(auth_url, data=auth_data)
response.raise_for_status()

access_token = response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}"
}

print("✅ Authentication successful")


# -----------------------------------------------------------
# 3️⃣ BUILD COMMON SPATIAL FILTER
# -----------------------------------------------------------

bbox_filter = (
    "OData.CSC.Intersects(area=geography'SRID=4326;"
    f"{AOI_POLYGON}')"
)


# -----------------------------------------------------------
# 4️⃣ SEARCH SENTINEL-1 GRD
# -----------------------------------------------------------

query_s1 = (
    f"{bbox_filter} and "
    "Collection/Name eq 'SENTINEL-1' and "
    f"ContentDate/Start ge {START_DATE} and "
    f"ContentDate/Start le {END_DATE} and "
    "Attributes/OData.CSC.StringAttribute/any(att:"
    "att/Name eq 'productType' and "
    "att/OData.CSC.StringAttribute/Value eq 'GRD')"
)

url_s1 = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter={query_s1}"

response_s1 = requests.get(url_s1, headers=headers)
response_s1.raise_for_status()

data_s1 = response_s1.json()["value"]

print(f"🛰 Sentinel-1 products found: {len(data_s1)}")


# -----------------------------------------------------------
# 5️⃣ SEARCH SENTINEL-2 L2A
# -----------------------------------------------------------

query_s2 = (
    f"{bbox_filter} and "
    "Collection/Name eq 'SENTINEL-2' and "
    f"ContentDate/Start ge {START_DATE} and "
    f"ContentDate/Start le {END_DATE} and "
    "Attributes/OData.CSC.StringAttribute/any(att:"
    "att/Name eq 'productType' and "
    "att/OData.CSC.StringAttribute/Value eq 'S2MSI2A')"
)

url_s2 = f"https://catalogue.dataspace.copernicus.eu/odata/v1/Products?$filter={query_s2}"

response_s2 = requests.get(url_s2, headers=headers)
response_s2.raise_for_status()

data_s2 = response_s2.json()["value"]

print(f"🌍 Sentinel-2 products found: {len(data_s2)}")


# -----------------------------------------------------------
# 6️⃣ AUTO SELECT BEST OVERLAP PAIR
# -----------------------------------------------------------

best_pair = None
best_overlap = 0

for s1 in data_s1:
    geom_s1 = shape(s1["GeoFootprint"])
    
    for s2 in data_s2:
        geom_s2 = shape(s2["GeoFootprint"])
        
        intersection = geom_s1.intersection(geom_s2)
        
        if not intersection.is_empty:
            overlap = (intersection.area / geom_s2.area) * 100
            
            if overlap > best_overlap:
                best_overlap = overlap
                best_pair = (s1, s2)

if best_pair is None:
    raise Exception("❌ No overlapping S1-S2 pair found")

product_s1, product_s2 = best_pair

print(f"\n✅ Best overlap found: {best_overlap:.2f}%")
print("Selected S1:", product_s1["Name"])
print("Selected S2:", product_s2["Name"])


# -----------------------------------------------------------
# 7️⃣ DOWNLOAD FUNCTION
# -----------------------------------------------------------

def download_product(product, filename):
    
    product_id = product["Id"]
    total_size = int(product["ContentLength"])
    
    download_url = (
        f"https://zipper.dataspace.copernicus.eu/odata/v1/"
        f"Products({product_id})/$value"
    )
    
    session = requests.Session()
    session.headers.update(headers)
    
    response = session.get(download_url, stream=True)
    response.raise_for_status()
    
    file_path = os.path.join(DOWNLOAD_FOLDER, filename)
    
    with open(file_path, "wb") as f:
        for chunk in tqdm(response.iter_content(chunk_size=8192),
                          total=total_size // 8192,
                          unit="KB"):
            if chunk:
                f.write(chunk)
    
    print(f"✅ Download complete: {filename}")


# -----------------------------------------------------------
# 8️⃣ DOWNLOAD S1 & S2
# -----------------------------------------------------------

download_product(product_s1, "Sentinel1_product.zip")
download_product(product_s2, "Sentinel2_product.zip")

print("\n🎉 All downloads completed successfully")