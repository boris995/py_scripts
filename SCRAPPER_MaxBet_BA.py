from selenium import webdriver
from selenium.webdriver.edge import options
from selenium.webdriver.edge import service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
import numpy as np
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchFrameException, NoSuchElementException, StaleElementReferenceException

options = Options()
options.add_argument("start-maximized")
# options.add_argument("--headless")
options.add_experimental_option("detach", True)
# options.add_argument("headless")
# options.add_argument("window-size=1920,1080")
# options.add_experimental_option("headless", True)
driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)

# driver.get("https://www.mdshop.ba/sport-prematch?sport=Fudbal")
driver.get("https://www.maxbet.ba/ba/pocetna")
time.sleep(2)

cookie_button = driver.find_element(By.CSS_SELECTOR, 'ds-cookies-consent-modal ion-button')
cookie_button.click()

time.sleep(2)

danas = driver.find_element(By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-filter/ion-header/ion-row/ion-col[3]')
danas.click()

time.sleep(2)

fudbal = driver.find_element(By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-list/ion-list/div/ion-item[1]/ion-label/ion-item/ion-label')
fudbal.click()

time.sleep(2)


## Otvoriti sve lige jednu po jednu

lige = driver.find_elements(By.CSS_SELECTOR, 'ds-leagues-list > div')
for i in lige:
    time.sleep(0.7)
    i.click()

match_time= []
league_name = []

match_home_team = []
match_away_team = []
# odds_value_1 = []
# odds_value_x = []
# odds_value_2 = []
# odds_value_15 = []
# odds_value_25 = []

## Uzmi sve utakmice

all_matches = driver.find_elements(By.CSS_SELECTOR, '.es-match')

for match in all_matches:
    match_time_TEMP = match.find_element(By.CSS_SELECTOR, '.es-match-kickoff')
    time.sleep(0.3)
    match_time.append(match_time_TEMP.text)
    # print(match_time.text)
    match_team_TEMP = match.find_elements(By.CSS_SELECTOR,'.es-match-teams-item')
    time.sleep(0.3)
    match_home_team.append(match_team_TEMP[0].text)
    time.sleep(0.3)
    match_away_team.append(match_team_TEMP[1].text)
    time.sleep(0.3)

    # odds_TEMP = match.find_elements(By.CSS_SELECTOR, '.odd-btn--odd')
    # odds_value_1.append(odds_TEMP[0].text)
    # time.sleep(0.1)
    # odds_value_x.append(odds_TEMP[1].text)
    # time.sleep(0.1)
    # # time.sleep(0.3)
    # # odds_value_2.append(odds_TEMP[2].text)
    # # odds_value_15.append(odds_TEMP[3].text)
    # # time.sleep(0.3)
    # # odds_value_25.append(odds_TEMP[4].text)


Xyz = {
    'Match Time': match_time,
    'Home Team': match_home_team,
    # 'Away Team': match_away_team,
    # '1'  :odds_value_1,
    # 'X' : odds_value_x,
    # # '2' : odds_value_2,
    # # '0-2': odds_value_15,
    # # '3+' : odds_value_25
}

df = pd.DataFrame.from_dict(Xyz)

driver.quit()

now = datetime.now()
dt_string = now.strftime("%d%m%Y%H%M%S")

df.to_excel("MaxBet_BA_PREMATCH_"+dt_string+".xlsx")