import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd

def setup_driver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("detach", True)
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

def run_pre_match_script():
    driver = setup_driver()
    driver.get("https://www.mdshop.ba/sport-prematch?sport=Ko%C5%A1arka&region=SAD&competition=NBA&competitionId=2-122-12")
    time.sleep(1)
    cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
    if cookie_accept:
        cookie_accept[0].click()
    driver.switch_to.default_content()
    driver.switch_to.frame('sportIframe')

    match_data = []
    page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
    for i in page:
        matchesandodds = i.find_elements(By.TAG_NAME, 'app-event')
        for j in matchesandodds:
            hometemp = j.find_element(By.CSS_SELECTOR, 'span.home').text
            awaytemp = j.find_element(By.CSS_SELECTOR, 'span.away').text
            try:
                limestemp = j.find_element(By.XPATH, './/span[@data-market="Manje"]').find_element(By.XPATH, 'following-sibling::span[1]').text
                match_data.append({'home': hometemp, 'away': awaytemp, 'limit': limestemp})
            except NoSuchElementException:
                match_data.append({'home': hometemp, 'away': awaytemp, 'limit': None})
    driver.quit()

    # Save pre-match limits to Excel
    df = pd.DataFrame(match_data)
    df.to_excel("pre_match_limits.xlsx", index=False)
    print("Pre-match limits saved to pre_match_limits.xlsx")

# Run this script once before the games
run_pre_match_script()
