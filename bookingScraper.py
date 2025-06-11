import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import os
import shutil
import ctypes

# Prevent Windows from sleeping
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

# --- Setup options ---
options = Options()

# Remove headless to avoid detection
# options.add_argument("--headless")

# Use a fresh user profile folder
profile_path = "/tmp/selenium_profile"
if os.path.exists(profile_path):
    shutil.rmtree(profile_path)
options.add_argument(f"--user-data-dir={profile_path}")

driver = uc.Chrome(service=Service(), options=options)

url = "https://www.booking.com/hotel/us/new-york-32-east-32nd-street.html?aid=356980&label=gog235jc-1DCA0o7AFCHG5ldy15b3JrLTMyLWVhc3QtMzJuZC1zdHJlZXRIM1gDaI4CiAEBmAExuAEXyAEM2AED6AEB-AECiAIBqAIDuALl8ZHCBsACAdICJDlkNjgwNmQwLTYxOWItNDkwNS04OWNkLWQ0NmQ3ZDZiN2UxZtgCBOACAQ&sid=cdbbcb537506c49c4f17396bffb3731a#tab-main"
driver.get(url)
wait = WebDriverWait(driver, 15)

# --- Human-like scrolling on page ---
def human_scroll(driver, times=3):
    for _ in range(times):
        driver.execute_script(f"window.scrollBy(0, {random.randint(200, 400)});")
        time.sleep(random.uniform(1.5, 3))

human_scroll(driver, times=5)

# --- Click the "Read reviews" button ---
try:
    review_tab = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.ID, "reviews-tab-trigger"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_tab)
    time.sleep(1)
    review_tab.click()
    time.sleep(2)
    driver.execute_script("window.scrollBy(0, 500);")
    print("Clicked Guest Reviews tab")
except Exception as e:
    print(f"Failed to click read reviews button: {e}")
    driver.quit()
    exit()

# --- Wait for review modal and scrollable container ---
try:
    review_modal = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="dialog"][aria-modal="true"]'))
    )
    # Then find the scrollable content inside the modal
    scroll_container = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.c1cb99b7ca"))
    )
    for _ in range(10):
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
        time.sleep(random.uniform(1.5, 2.5))
    print("Review modal loaded")
except Exception as e:
    print(f"Review modal did not load: {e}")
    driver.quit()
    exit()

review_list = []
current_page = 1
max_pages = 60  # Safety limit to avoid infinite loop

# --- Click "More reviews" until none left ---
while current_page < max_pages:
    # --- Parse HTML ---
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # --- Extract total rating and review count ---
    try:
        total_rating_elem = soup.select_one("div.f63b14ab7a.dff2e52086")
        total_rating = total_rating_elem.text.strip() if total_rating_elem else None

        total_reviews_elem = soup.select_one("div.fff1944c52.fb14de7f14.eaa8455879")
        total_reviews = total_reviews_elem.text.strip() if total_reviews_elem else None
    except:
        total_rating = None
        total_reviews = None

    # --- Extract reviews ---
    reviews = soup.select("div[data-testid='review-card']")

    for review in reviews:
        try:
            positive = review.select_one('div[data-testid="review-positive-text"]').get_text(separator=" ", strip=True)
        except:
            positive = ""
        try:
            negative = review.select_one('div[data-testid="review-negative-text"]').get_text(separator=" ", strip=True)
        except:
            negative = ""

        # Combine both with a separator, or just a space
        review_text = (positive + " " + negative).strip()
        try:
            rating_raw = review.select_one("div.f63b14ab7a.dff2e52086").text.strip()
            rating = float(rating_raw.split('/')[0])
        except:
            rating = None
        try:
            name = review.select_one("div.b08850ce41.f546354b44").text.strip()
        except:
            name = None
        try:
            date_elem = review.select_one("span[data-testid='review-date']")
            raw_date = date_elem.text.strip()
            review_date = raw_date.replace("Reviewed:", "").strip()
        except Exception:
            review_date = None
        try:
            stay_elem = review.select_one("span[data-testid='review-num-nights']")
            stay_text = stay_elem.text.strip()
            import re
            match = re.search(r"(\d+)\s+nights?", stay_text)
            length_of_stay = int(match.group(1)) if match else None
        except Exception:
            length_of_stay = None
        try:
            traveler_type_elem = review.select_one("span[data-testid='review-traveler-type']")
            traveler_type = traveler_type_elem.text.strip() if traveler_type_elem else None
        except Exception:
            traveler_type = None

        review_list.append({
            'review_text': review_text,
            'review_rating': rating,
            'traveler_name': name,
            'review_date': review_date,
            'length_of_stay': length_of_stay,
            'traveler_type': traveler_type
        })

    try:
        # Scroll the modal to bottom
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
        time.sleep(random.uniform(2, 3))

        # Try to click "More reviews" inside the modal
        next_page_number = str(current_page + 1)
        next_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{next_page_number}']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
        time.sleep(random.uniform(1, 2))
        next_button.click()
        time.sleep(random.uniform(3, 5))
        current_page += 1
    except:
        print(f"No page {current_page + 1} found. Finished scraping.")
        break

# --- Save to CSV ---
df = pd.DataFrame(review_list)
df['total_rating'] = total_rating
df['total_reviews'] = total_reviews
df.to_csv("booking_reviews_Boulan.csv", index=False)

print(f"Scraped {len(review_list)} reviews, total rating: {total_rating}, total reviews: {total_reviews}")

driver.quit()

# Revert to default sleep behavior
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

