import os
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# File paths and Google Sheets configuration
excel_file = "web_scraped_data2.xlsx"
json_creds_file = 'soy-antenna-441517-h0-8e4d7daecbcc.json'
sheet_name = "Web Summit Featured Startups"
your_google_email = "dj.boris995@gmail.com"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def upload_to_google_sheets(df, sheet_name, json_creds_file):
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        creds = Credentials.from_service_account_file(json_creds_file, scopes=scope)
        client = gspread.authorize(creds)
        drive_service = build('drive', 'v3', credentials=creds)
        logging.info("Successfully authenticated with Google API.")
    except Exception as e:
        logging.error(f"Failed to authenticate with Google API: {e}")
        return

    try:
        spreadsheet = client.open(sheet_name)
        sheet = spreadsheet.sheet1
        logging.info(f"Spreadsheet '{sheet_name}' found.")
    except gspread.SpreadsheetNotFound:
        try:
            logging.warning(f"Spreadsheet '{sheet_name}' not found. Creating a new spreadsheet...")
            spreadsheet = client.create(sheet_name)
            sheet = spreadsheet.sheet1
            logging.info(f"Spreadsheet '{sheet_name}' created successfully.")
            drive_service.permissions().create(
                fileId=spreadsheet.id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            logging.info("Spreadsheet is now public.")
        except Exception as e:
            logging.error(f"Error creating or sharing the spreadsheet: {e}")
            return

    try:
        sheet.clear()
        logging.info("Cleared existing data in the Google Sheet.")
    except HttpError as e:
        logging.error(f"Failed to clear data in the Google Sheet: {e}")
        return

    header = df.columns.values.tolist()
    rows = df.values.tolist()
    try:
        sheet.insert_row(header, index=1)
        sheet.insert_rows(rows, row=2)
        logging.info("Header and data rows inserted successfully.")
    except HttpError as e:
        logging.error(f"Failed to insert header and data rows: {e}")
        return

    spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
    logging.info(f"Access your Google Sheet here: {spreadsheet_url}")
    print(f"Access your Google Sheet here: {spreadsheet_url}")

# Selenium setup
driver = webdriver.Chrome()
url = "https://websummit.com/startups/featured-startups/"
driver.get(url)
driver.maximize_window()
wait = WebDriverWait(driver, 10)

try:
    accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.Button__StyledButton-sc-d4ee7b0f-0.dlUEar")))
    accept_button.click()
    print("Clicked 'Accept all' button.")
except Exception as e:
    print("No 'Accept all' button found or an error occurred:", e)

def extract_data():
    data = []
    try:
        attendees = driver.find_elements(By.CSS_SELECTOR, ".ListItemStyles__StyledListItemWrapper-sc-94ce60d2-2")
        for i in range(3):  # Collect only 3 entries
            attendees = driver.find_elements(By.CSS_SELECTOR, ".ListItemStyles__StyledListItemWrapper-sc-94ce60d2-2")
            try:
                attendees[i].click()
                time.sleep(2)

                # Scrape data
                name = driver.find_element(By.CSS_SELECTOR, ".headlines__H1-sc-31df2319-0").text
                profession = driver.find_element(By.CSS_SELECTOR, ".bodyCopy__Overline-sc-986c63f9-4").text
                country = driver.find_element(By.CSS_SELECTOR, ".ContentTagList__ContentTagListWrapper-sc-6e6a07b7-0 .ContentTagList__ContentTagListItem-sc-6e6a07b7-1:first-child p").text
                niche_category = driver.find_element(By.CSS_SELECTOR, ".ContentTagList__ContentTagListWrapper-sc-6e6a07b7-0 .ContentTagList__ContentTagListItem-sc-6e6a07b7-1:nth-child(2) p").text
                
                website_elem = driver.find_elements(By.CSS_SELECTOR, "a[label='website']")
                email = website_elem[0].get_attribute("href").split("mailto:")[-1] if website_elem and "mailto:" in website_elem[0].get_attribute("href") else "N/A"

                data.append([name, profession, country, niche_category, email])
                print(f"Name: {name}, Profession: {profession}, Country: {country}, Category: {niche_category}, Email: {email}")
            except Exception as e:
                print(f"Failed to retrieve data for attendee: {e}")
            finally:
                driver.back()
                time.sleep(2)
    except Exception as e:
        print(f"Error navigating attendee elements: {e}")
    return data

# Collect data and save it to Excel
all_data = extract_data()
df = pd.DataFrame(all_data, columns=["Name", "Profession", "Country", "Category", "Email"])
df.to_excel(excel_file, index=False)
print(f"Data saved to {excel_file}.")

driver.quit()

# Upload data to Google Sheets
upload_to_google_sheets(df, sheet_name, json_creds_file)
