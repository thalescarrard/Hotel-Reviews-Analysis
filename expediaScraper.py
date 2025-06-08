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

url = "https://www.expedia.com/Miami-Hotels-Boulan-South-Beach.h4599935.Hotel-Information?locale=en_US&siteid=1&pwaDialog=product-reviews"
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
    review_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-stid="reviews-link"]')))
    
    # Scroll the button into view with some offset
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", review_button)
    time.sleep(1)

    # Wait a little for the sticky bar to settle
    time.sleep(2)

    # Click with JS to bypass overlapping elements
    driver.execute_script("arguments[0].click();", review_button)
    print("Clicked read reviews button")
except Exception as e:
    print(f"Failed to click read reviews button: {e}")
    driver.quit()
    exit()

# --- Wait for review modal and scrollable container ---
try:
    review_modal = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "section[role='dialog']"))
    )
    # Then find the scrollable content inside the modal
    scroll_container = review_modal.find_element(By.CSS_SELECTOR, "div.uitk-sheet-content.uitk-sheet-content-padded")
    for _ in range(5):
        driver.execute_script("arguments[0].scrollTop += 500;", scroll_container)
        time.sleep(random.uniform(1.5, 3))
    print("Review modal loaded")
except Exception as e:
    print(f"Review modal did not load: {e}")
    driver.quit()
    exit()

# --- Click "More reviews" until none left ---
while True:
    try:
        # Scroll the modal to bottom
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_container)
        time.sleep(random.uniform(2, 3))

        # Try to click "More reviews" inside the modal
        more_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'More reviews')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
        time.sleep(random.uniform(1.5, 2.5))
        more_btn.click()
        time.sleep(random.uniform(2.5, 4))
    except:
        print("No more 'More reviews' button found or all reviews loaded.")
        break

# --- Parse HTML ---
soup = BeautifulSoup(driver.page_source, "html.parser")

# --- Extract total rating and review count ---
try:
    total_rating_elem = soup.select_one("div.uitk-text.uitk-type-500.uitk-type-bold.uitk-text-default-theme")
    total_rating = total_rating_elem.text.strip() if total_rating_elem else None

    total_reviews_elem = soup.select_one("button.uitk-more-info-trigger > span")
    total_reviews = total_reviews_elem.text.strip() if total_reviews_elem else None
except:
    total_rating = None
    total_reviews = None

# --- Extract reviews ---
review_list = []
reviews = soup.select('article[itemprop="review"]')

for review in reviews:
    try:
        review_text = review.select_one("span[itemprop='description']").text.strip()
    except:
        review_text = None
    try:
        rating_raw = review.select_one("span[itemprop='ratingValue']").text.strip()
        rating = float(rating_raw.split('/')[0])
    except:
        rating = None
    try:
        name = review.select_one("h4.uitk-heading.uitk-heading-7").text.strip()
    except:
        name = None
    try:
        date = review.select_one("span[itemprop='datePublished']").text.strip()
    except:
        date = None
    try:
        stay_text = review.select_one("div.uitk-text.uitk-type-200.uitk-text-standard-theme.uitk-layout-flex-item").text.strip()
        import re
        match = re.search(r"Stayed (\d+) night", stay_text)
        length_of_stay = int(match.group(1)) if match else None
    except:
        length_of_stay = None

    review_list.append({
        'source': 'Expedia.com',
        'review_text': review_text,
        'review_rating': rating,
        'traveler_name': name,
        'review_date': date,
        'length_of_stay': length_of_stay
    })

# --- Save to CSV ---
df = pd.DataFrame(review_list)
df['total_rating'] = total_rating
df['total_reviews'] = total_reviews
df.to_csv("expedia_reviews_Boulan.csv", index=False)

print(f"Scraped {len(review_list)} reviews, total rating: {total_rating}, total reviews: {total_reviews}")

driver.quit()

# Revert to default sleep behavior
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)

