import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

from bs4 import BeautifulSoup
import time
import random
import pandas as pd
import os
import shutil
import ctypes
import re

# Prevent Windows from sleeping
ES_CONTINUOUS = 0x80000000
ES_SYSTEM_REQUIRED = 0x00000001
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)

# --- Global config ---
MAX_RETRIES = 2
profile_path = "/tmp/selenium_profile"
url = "https://www.tripadvisor.com/Hotel_Review-g34439-d2443641-Reviews-Boulan_South_Beach-Miami_Beach_Florida.html"

def start_driver(profile_dir=None):
    if profile_dir is None:
        # Try removing old profile folder with retries
        for attempt in range(3):
            try:
                if os.path.exists(profile_path):
                    shutil.rmtree(profile_path)
                profile_dir = profile_path
                break
            except (PermissionError, FileNotFoundError):
                time.sleep(1)
        else:
            # If still locked, use a unique profile folder
            unique_suffix = str(int(time.time()))
            profile_dir = f"{profile_path}_{unique_suffix}"
            print(f"Profile path in use. Using fallback: {profile_dir}")
    options = Options()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    return uc.Chrome(service=Service(), options=options), profile_dir

def human_scroll(driver, times=3):
    for _ in range(times):
        driver.execute_script(f"window.scrollBy(0, {random.randint(200, 400)});")
        time.sleep(random.uniform(1.5, 3))

def extract_total_rating(soup):
    rating_div = soup.find("div", {"data-automation": "bubbleRatingValue"})
    if rating_div:
        try:
            return round(float(rating_div.text.strip()) * 2, 1)  # Convert to 10 scale
        except ValueError:
            return None
    return None

def extract_total_reviews(soup):
    review_count_div = soup.find("div", {"data-automation": "bubbleReviewCount"})
    if review_count_div:
        match = re.search(r"([\d,]+)", review_count_div.text)
        if match:
            return int(match.group(1).replace(",", ""))
    return None

def parse_reviews(soup):
    reviews_data = []
    review_divs = soup.select("div[class*='JVaPo']")
    if not review_divs:
        print("No reviews found with new selector")
        return []

    for div in review_divs:
        text_el = div.select_one("span._d._c[data-automation^='reviewText']")
        review_text = text_el.get_text(strip=True) if text_el else None
        rating = None
        title_el = div.select_one("svg[data-automation='bubbleRatingImage'] title")
        if title_el:
            m = re.search(r"(\d(?:\.\d)?) of 5 bubbles", title_el.text)
            if m:
                rating = float(m.group(1)) * 2

        name_el = div.select_one("a.BMQDV._F.Gv.wSSLS.SwZTJ.FGwzt.ukgoS")
        traveler_name = name_el.get_text(strip=True) if name_el else None

        title_link = div.select_one("div[data-test-target='review-title'] > div > a")
        review_title = title_link.get_text(strip=True) if title_link else None

        date_el = div.select_one("div.hDWtV span[title]")
        review_date = date_el["title"] if date_el else None

        visited_divs = div.select("div.TgEgi div.biGQs._P.fiohW.fOtGX")
        date_visited = visited_divs[0].get_text(strip=True) if len(visited_divs) > 0 else None
        trip_type_raw = visited_divs[1].get_text(strip=True) if len(visited_divs) > 1 else None
        if trip_type_raw == "Friends":
            traveler_type = "Group"
        elif trip_type_raw == "Business":
            traveler_type = "Solo"
        else:
            traveler_type = trip_type_raw

        reviews_data.append({
            "review_text": review_text,
            "review_rating": rating,
            "traveler_name": traveler_name,
            "review_title": review_title,
            "review_date": review_date,
            "date_visited": date_visited,
            "traveler_type": traveler_type
        })

    return reviews_data

# --- Main scraping logic ---
review_list = []
current_page = 1
max_pages = 100
total_rating, total_reviews = None, None

driver, profile_dir = start_driver()
wait = WebDriverWait(driver, 15)
driver.get(url)
human_scroll(driver, times=5)
wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.JVaPo.Gi.kQjeB")))

while current_page <= max_pages:
    for retry in range(MAX_RETRIES):
        try:
            time.sleep(random.uniform(3, 5))
            soup = BeautifulSoup(driver.page_source, "html.parser")

            if current_page == 1:
                total_rating = extract_total_rating(soup)
                total_reviews = extract_total_reviews(soup)

            reviews = parse_reviews(soup)
            if not reviews:
                print(f"No reviews found on page {current_page}. Possibly last page.")
                break  # Safely exit the loop instead of crashing

            review_list.extend(reviews)
            print(f"Scraped {len(reviews)} reviews from page {current_page}")

            # Try to find the next page link
            next_page_num = current_page + 1
            try:
                next_page_link = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f'//a[@aria-label="{next_page_num}"]')
                ))
            except Exception:
                print(f"No more pages found after page {current_page}. Stopping.")
                current_page = max_pages + 1  # Exit outer loop
                break

            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_link)
            time.sleep(random.uniform(1, 2))
            next_page_link.click()
            current_page += 1
            time.sleep(random.uniform(3, 6))
            break

        except InvalidSessionIdException:
            print("Invalid session detected. Restarting driver.")
            try:
                driver.quit()
            except:
                pass
            driver, profile_dir = start_driver(profile_dir)
            wait = WebDriverWait(driver, 15)
            driver.get(url)
            human_scroll(driver, times=5)

            # Navigate back to current page
            for page_to_navigate in range(1, current_page):
                try:
                    next_page_link = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f'//a[@aria-label="{page_to_navigate + 1}"]')
                    ))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_link)
                    next_page_link.click()
                    time.sleep(random.uniform(2, 4))
                except Exception as e_nav:
                    print(f"Navigation error while resuming: {e_nav}")
                    break

        except WebDriverException as e:
            print(f"WebDriver error on page {current_page}, attempt {retry + 1}: {e}")
            time.sleep(2)

        except Exception as e:
            print(f"Error on page {current_page}, attempt {retry + 1}: {e}")
            time.sleep(2)

    else:
        print(f"Retry limit reached for page {current_page}. Skipping.")
        current_page += 1  # Go to next page anyway

# Save to CSV
df = pd.DataFrame(review_list)
df['total_rating'] = total_rating
df['total_reviews'] = total_reviews
df.to_csv("tripadvisor_reviews_Boulan.csv", index=False)

print(f"Total scraped reviews: {len(review_list)}")
print(f"Total rating (10 scale): {total_rating}")
print(f"Total reviews count: {total_reviews}")

driver.quit()
ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
