# Medicare Hospital Ratings - Longitudinal Analysis

A comprehensive Streamlit application for analyzing Medicare hospital performance over time with AI-powered recommendations and impact estimates.

## Features

- **5-Year Historical Analysis** - Track hospital performance trends from 2020-2024
- **Performance Trends** - Visualize multi-year metric trends with interactive charts
- **Future Projections** - 1-year forward forecasts based on historical patterns
- **Impact-Based Recommendations** - Actionable recommendations with estimated improvement percentages
- **Hospital Comparison** - Compare side-by-side performance with peer hospitals
- **Peer Benchmarking** - Impact estimates based on actual peer hospital improvements
- **Confidence Levels** - Statistical confidence in all projections and impact estimates

## Quick Start

### Option 1: Docker (Recommended - Easiest)

**Prerequisites:** Docker and Docker Compose installed

#### Install Docker and Docker Compose

**On macOS:**
```bash
# Install Docker Desktop from https://www.docker.com/products/docker-desktop
# Docker Desktop includes both Docker and Docker Compose
# Verify installation:
docker --version
docker-compose --version
```

**On Linux (Ubuntu/Debian):**
```bash
# Install Docker
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add your user to docker group (to run without sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation:
docker --version
docker-compose --version
```

**On Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Restart your computer
- Verify in PowerShell: `docker --version`

#### Run the App with Docker

```bash
# Start the app
docker-compose up

# Or build and run manually
docker build -t hospital-ratings .
docker run -p 8501:8501 hospital-ratings
```

Then open http://localhost:8501 in your browser.

To stop the app, press `Ctrl+C` or run `docker-compose down`

### Option 2: Automated Setup Script

```bash
# Run setup script
./setup.sh

# Then start the app
source .venv/bin/activate
streamlit run app.py
```

### Option 3: Manual Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate it
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`

## Usage

1. **Search for a Hospital**
   - Use the sidebar to search by State & County, Hospital Name, or Rating
   - Filter by minimum rating if desired

2. **View Hospital Details**
   - Select a hospital from the results
   - See current metrics and hospital information

3. **Explore Analysis Tabs**
   - **📈 Performance** - Current year performance vs benchmarks
   - **📊 Trends** - 5-year historical trends with charts
   - **🔮 Projections** - 1-year performance forecasts
   - **💡 Impact Actions** - Recommended actions with estimated improvements
   - **🏥 Comparison** - Compare with peer hospitals in the same state

4. **Understand Impact Estimates**
   - Each recommendation shows estimated improvement % and confidence level
   - Improvement ranges are based on peer hospital performance data
   - Peer count shows how many hospitals achieved similar results

## Data

- **Source**: Medicare Hospital Compare (CMS)
- **Coverage**: 120 hospitals across 5 years (2020-2024)
- **Metrics**:
  - Overall Star Rating
  - Mortality Rates (Heart Attack, Pneumonia)
  - Readmission Rate
  - Safety Score
  - CLABSI Rate (Central Line-Associated Bloodstream Infections)

## Project Structure

```
Hospital-Ratings/
├── app.py                              # Main Streamlit application
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Docker container config
├── docker-compose.yml                  # Docker Compose config
├── setup.sh                            # Automated setup script
├── data/
│   ├── hospital_ratings.csv           # Current year hospital data
│   └── processed/
│       └── hospital_timeseries.csv    # 5-year historical time-series data
└── utils/
    ├── data_loader.py                 # Data loading and filtering
    ├── analysis_agent.py              # Hospital performance analysis
    ├── cms_data_fetcher.py            # CMS data fetching and validation
    ├── longitudinal_analysis.py       # Trend and projection analysis
    ├── impact_estimator.py            # Impact estimation engine
    └── hybrid_analysis_agent.py       # Analysis orchestration
```

## Requirements

**For Docker deployment:**
- Docker 20.10+
- Docker Compose 1.29+
- 2GB free disk space
- Internet connection for initial image download

**For local Python setup:**
- Python 3.8 or higher
- pip (Python package manager)
- 1GB free disk space
- Internet connection for dependency installation

See `requirements.txt` for specific Python package dependencies

## Troubleshooting

**"streamlit: command not found"**
- Make sure your virtual environment is activated: `source .venv/bin/activate`

**"ModuleNotFoundError"**
- Install dependencies: `pip install -r requirements.txt`

**Port 8501 already in use**
- Run on a different port: `streamlit run app.py --server.port 8502`

**Docker issues**
- Rebuild: `docker-compose build --no-cache`
- Check logs: `docker-compose logs hospital-ratings`

## Deactivating Virtual Environment

When you're done:

```bash
deactivate
```

## Data Updates

To update historical data with the latest CMS datasets:

```python
from utils.cms_data_fetcher import load_historical_data_from_csvs, save_processed_data

csv_paths = {
    2020: "path/to/2020.csv",
    2021: "path/to/2021.csv",
}
df = load_historical_data_from_csvs(csv_paths)
save_processed_data(df)
```

## License

Data source: Medicare Hospital Compare (CMS Public Data)
