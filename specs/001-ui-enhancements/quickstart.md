# UI Enhancements Quickstart

This guide explains how to spin up the local environment to test and develop the new UI capabilities (sorting, filtering, real-time controls).

## 1. Prerequisites
- Python 3.11+
- Modern Web Browser (Chrome, Firefox, Safari)
- Valid Kubernetes configuration (if testing K8s collector) or Git/Vault configurations for the other collectors.

## 2. Running the Backend
1. Open a terminal in the `backend/` directory.
2. Install dependencies (if not already done): `pip install -r requirements.txt` (or via your usual python environment setup).
3. Start the FastAPI server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

## 3. Running the Frontend
1. The frontend strictly uses Vanilla HTML/CSS/JS with no build step required.
2. You can serve the frontend using any basic HTTP server. For example, from the `frontend/` directory:
   ```bash
   python -m http.server 8000
   ```
3. Open your browser and navigate to `http://localhost:8000/src/index.html`.

## 4. Testing the Features
- **Sorting**: Click any column header in a loaded dashboard to toggle sorting ascending/descending.
- **Filtering**: Type in the filter box above the table to see exact matches and autocomplete suggestions.
- **Real-time Controls**: 
  - Click "Refresh Now" to force an immediate API reload.
  - Change the "Max Data Value" input to clip the dataset size.
  - Adjust the auto-refresh interval from the dropdown.
- **Theming**: Click the light/dark mode toggle button to switch CSS variable palettes.
