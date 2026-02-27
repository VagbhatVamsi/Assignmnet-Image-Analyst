# 🛰 Multi-Sensor Satellite Data Processing Pipeline

## 📌 Assignment: Image Analyst -- GalaxEye

### Objective

Build a production-ready data processing pipeline that automatically:

-   Downloads Sentinel-1 (GRD SAR) and Sentinel-2 (L2A Optical)
-   Cleans and preprocesses imagery
-   Generates analysis-ready datasets for machine learning and
    geospatial workflows

------------------------------------------------------------------------

## 📂 Project Structure

image-analyst-pipeline/ │ ├── main.py ├── requirements.txt ├── README.md
│ ├── Data_Ingestion.py ├── Sentinel-1_Processing.py ├──
Sentinel-2_Processing.py

------------------------------------------------------------------------

## ⚙️ Features Implemented

### 1️⃣ Data Ingestion

-   Authenticates with Copernicus Data Space
-   Searches Sentinel-1 & Sentinel-2 products
-   Automatically selects best overlapping pair
-   Downloads ZIP products

### 2️⃣ Sentinel-1 Processing

-   Reads SAR backscatter (VH polarization)
-   Converts to Linear and dB scale
-   Applies Lee speckle filtering
-   Generates GLCM texture features

### 3️⃣ Sentinel-2 Processing

-   Loads B04 (Red) and B08 (NIR)
-   Computes NDVI
-   Uses Scene Classification Layer (SCL)
-   Applies cloud masking

------------------------------------------------------------------------

## 🚀 How to Run

### Step 1 -- Install Dependencies

pip install -r requirements.txt

### Step 2 -- Run Pipeline

python main.py

The pipeline will: 1. Download Sentinel data 2. Process SAR imagery 3.
Process optical imagery 4. Generate visualization outputs

------------------------------------------------------------------------

## 🧠 Technical Highlights

-   Modular Python structure
-   Window-based raster reading (memory safe)
-   SAR speckle reduction (Lee filter)
-   Texture extraction using GLCM
-   Cloud masking using SCL
-   Fully reproducible pipeline

------------------------------------------------------------------------

## ⚠️ Important Notes

**RAM & Memory Constraints:** Due to limited RAM consistency, all images are downscaled before plotting. Some visualizations are cropped and plotted for a specific region only to reduce memory usage.

------------------------------------------------------------------------

## 👨‍💻 Author

S. Vagbhat Vamsi Krishna\
Submission for Image Analyst Assignment -- GalaxEye
