# Hotel Review Scraper and Analyzer 🏨📊

This project scrapes hotel review data from [Booking.com](https://www.booking.com) and [Expedia](https://www.expedia.com), cleans and merges the data, and analyzes it using Python libraries like pandas, matplotlib, and seaborn. The goal is to explore patterns in guest sentiment and ratings, and later apply machine learning models for deeper insights.

---

## 🚀 Project Structure

### 1. **Data Collection (Selenium + BeautifulSoup)**
- Scrapes reviews using `undetected-chromedriver` to bypass anti-bot detection.
- Extracts fields like:
  - Review text (positive + negative)
  - Rating
  - Traveler name
  - Date of review
  - Length of stay
  - Traveler type (Booking.com only)
- Handles pagination and review modals.
- Saves results as `.csv` files per platform.

### 2. **Data Cleaning**
- Merges Booking and Expedia datasets.
- Normalizes column names and types:
  - Converts dates to `datetime`
  - Converts ratings to `float`
  - Removes duplicates (based on text + name + date)
  - Removes extremely old or empty reviews
- Saves a single, clean dataset for analysis.

### 3. **Data Analysis & Visualization**
- Exploratory Data Analysis (EDA) using:
  - Histogram of rating distribution
  - Review counts per platform
  - Boxplots comparing rating distributions
  - Ratings over time (monthly trends)
- Focuses on reviews from 2020 onward for consistency.

### 4. **Future Plans**
- Sentiment analysis on review text.
- Rating prediction models based on review content.
- Dashboards or reports for hotel operators.

---

## 📊 Sample Visualizations

(To be added...)

---

## 📌 Notes

Traveler Type is only available from Booking.com due to better structured HTML.

Duplicate reviews posted on both platforms are removed using exact matches on review_text, traveler_name, and review_date.

All review dates are converted to consistent datetime format and filtered to include only 2020 and later.

---

## 📁 Files

- `bookingScraper.py` – Booking.com scraper
- `expediaScraper.py` – Expedia scraper
- `dataCleaner.py` – Data merging and cleaning
- `dataAnalyzer.py` – Visual and statistical analysis
- `cleaned_reviews.csv` – Clean, unified dataset

  
---

## 🛠️ Requirements

```bash
pip install pandas matplotlib seaborn beautifulsoup4 selenium undetected-chromedriver
