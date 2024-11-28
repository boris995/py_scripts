import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

## Make progress bar better
## Scroll bar

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MaxBet Scraper")
        self.root.geometry("1000x600")

        # Centering style for Treeview
        style = ttk.Style()
        style.configure("Centered.Treeview", anchor="center")
        style.configure("Centered.Treeview.Heading", anchor="center")
        
        # Set up GUI components
        self.scrape_button = tk.Button(root, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)
        
        # Table
        self.tree = ttk.Treeview(root, columns=("Match Time", "Home Team", "Away Team", "Home Win", "Draw", "Away Win", "Under 2.5", "Over 2.5"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(expand=True, fill="both", pady=10)

    def start_scraping(self):
        # Start scraping in a separate function
        self.scrape_button.config(state="disabled")
        self.progress["value"] = 0
        self.scrape_data()
        
    def scrape_data(self):
        # Options for headless mode
        options = Options()
        options.add_argument("headless")
        options.add_argument("start-maximized")
        
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        
        # Your scraping logic
        driver.get("https://www.maxbet.ba/ba/pocetna")
        time.sleep(2)

        # Accept cookies
        try:
            cookie_button = driver.find_element(By.CSS_SELECTOR, 'ds-cookies-consent-modal ion-button')
            cookie_button.click()
            print("Cookie button found.")
        except NoSuchElementException:
            print("No cookie button found.")

        time.sleep(2)

        try:
            danas = driver.find_element(By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-filter/ion-header/ion-row/ion-col[3]')
            danas.click()
            # print("Danas element found.")
            time.sleep(2)
            fudbal = driver.find_element(By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-list/ion-list/div/ion-item[1]/ion-label/ion-item/ion-label')
            fudbal.click()
            # print("Fudbal element found.")
            time.sleep(2)
        except NoSuchElementException:
            messagebox.showerror("Error", "Unable to navigate through the site")
            driver.quit()
            self.scrape_button.config(state="normal")
            return

        match_time = []
        match_home_team = []
        match_away_team = []
        odds_value_1 = []
        odds_value_x = []
        odds_value_2 = []
        odds_value_15 = []
        odds_value_25 = []

        lige = driver.find_elements(By.CSS_SELECTOR, 'ds-leagues-list > div')
        for i in lige:
            time.sleep(0.7)
            i.click()

        all_matches = driver.find_elements(By.CSS_SELECTOR, 'ds-leagues-list .es-match')
        total_matches = len(all_matches)

        for idx, match in enumerate(all_matches):
            try:
                match_time_TEMP = match.find_element(By.CSS_SELECTOR, '.es-match-kickoff').text
                match_time.append(match_time_TEMP)
                # print('-------------')
                # print(match_time)

                match_team_TEMP = match.find_elements(By.CSS_SELECTOR, '.es-match-teams-item')
                match_home_team.append(match_team_TEMP[0].text if len(match_team_TEMP) > 0 else "")
                match_away_team.append(match_team_TEMP[1].text if len(match_team_TEMP) > 1 else "")

                odds_TEMP = match.find_elements(By.CSS_SELECTOR, '.odd-btn .odd-btn--odd')
                odds_value_1.append(odds_TEMP[0].text if len(odds_TEMP) > 0 else "")
                odds_value_x.append(odds_TEMP[1].text if len(odds_TEMP) > 1 else "")
                odds_value_2.append(odds_TEMP[2].text if len(odds_TEMP) > 2 else "")
                odds_value_15.append(odds_TEMP[3].text if len(odds_TEMP) > 3 else "")
                odds_value_25.append(odds_TEMP[4].text if len(odds_TEMP) > 4 else "")

                # Update progress bar
                self.progress["value"] = ((idx + 1) / total_matches) * 100
                self.root.update_idletasks()
                time.sleep(0.1)
                
            except StaleElementReferenceException:
                continue

        # driver.quit()
        
        # Create DataFrame to hold the data
        data = {
            'Match Time': match_time,
            'Home Team': match_home_team,
            'Away Team': match_away_team,
            '1': odds_value_1,
            'X': odds_value_x,
            '2': odds_value_2,
            '0-2': odds_value_15,
            '3+': odds_value_25
        }
        
        df = pd.DataFrame(data)
        # print(df)  # Debug: print DataFrame to check data
        self.display_data(df)
        self.scrape_button.config(state="normal")
        messagebox.showinfo("Scraping Complete", "Data scraping complete and displayed in table.")

    def display_data(self, df):
        # Clear any existing data in the table
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        # Insert scraped data into the table
        for row in df.itertuples(index=False):
            self.tree.insert("", "end", values=row)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScraperApp(root)
    root.mainloop()
