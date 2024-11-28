import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# Prompt user for threshold difference or set to default 2 points
try:
    difference_threshold = float(input("Enter the limit difference to follow (default is 2 points): ") or 2)
except ValueError:
    print("Invalid input. Using default value of 2 points.")
    difference_threshold = 2

# Function to send an alert
def send_alert(match, pre_limit, live_limit):
    print(f"ALERT: Limit changed for {match}: {pre_limit} -> {live_limit}")

# Read pre-match limits from Excel file
pre_match_limits = pd.read_excel("pre_match_limits.xlsx")
pre_match_limits_dict = {(row['home'], row['away']): float(row['limit']) for index, row in pre_match_limits.iterrows()}

# Dictionary to track the last known live limit
last_live_limits = {}

def setup_driver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("detach", True)
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

def run_live_script():
    driver = setup_driver()
    driver.get("https://www.mdshop.ba/sport-live")
    time.sleep(1)
    cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
    if cookie_accept:
        cookie_accept[0].click()
    driver.switch_to.default_content()
    driver.switch_to.frame('sportLiveIframe')
    basketball = driver.find_elements(By.XPATH, '//*[@id="centerContent"]/app-sport-groups-container/app-sport-group[2]/section/div')
    basketball[0].click()

    while True:
        live_limits = {}
        page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
        for i in page:
            matchesandodds = i.find_elements(By.TAG_NAME, 'app-event-live')
            for j in matchesandodds:
                hometemp = j.find_element(By.CSS_SELECTOR, 'span.home').text
                awaytemp = j.find_element(By.CSS_SELECTOR, 'span.away').text
                match = (hometemp, awaytemp)

                # Only check matches that are in the pre-match Excel file
                if match in pre_match_limits_dict:
                    try:
                        limit_text = j.find_element(By.XPATH, './/span[@data-market="Manje"]').find_element(By.XPATH, 'following-sibling::span[1]').text
                        # Check if the limit_text is a valid number
                        try:
                            limestemp = float(limit_text)
                            live_limits[match] = limestemp
                        except ValueError:
                            # If conversion to float fails, ignore this limit
                            print(f"Skipping non-numeric limit for {hometemp} vs {awaytemp}: {limit_text}")
                            live_limits[match] = None
                    except NoSuchElementException:
                        live_limits[match] = None

        # Compare live limits with the pre-match limits and detect live limit changes
        for match, live_limit in live_limits.items():
            if live_limit is not None:
                pre_limit = pre_match_limits_dict.get(match)
                
                # Check if live limit is different from pre-match limit
                if pre_limit is not None and live_limit != pre_limit:
                    last_live_limit = last_live_limits.get(match)

                    # Check if the live limit has changed since the last check
                    if last_live_limit is None or live_limit != last_live_limit:
                        send_alert(match, pre_limit, live_limit)

                    # Update the last live limit for this match
                    last_live_limits[match] = live_limit

        # Wait for 5 seconds before checking again
        time.sleep(5)

# Run the live script continuously
run_live_script()