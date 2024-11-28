import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import threading
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import time

class ScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MaxBet Scraper")
        self.root.geometry("1000x600")

        # Centering style for Treeview
        style = ttk.Style()
        style.configure("Centered.Treeview", anchor="center", font=("Arial", 10))
        style.configure("Centered.Treeview.Heading", anchor="center", font=("Arial", 10, "bold"))
        
        # Set up GUI components
        self.scrape_button = tk.Button(root, text="Start Scraping", command=self.start_scraping_thread)
        self.scrape_button.pack(pady=10)
        
        # Progress bar and status label
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=5)
        
        self.status_label = tk.Label(root, text="", font=("Arial", 10))
        self.status_label.pack(pady=5)

        # Frame for Treeview with scrollbar
        frame = tk.Frame(root)
        frame.pack(expand=True, fill="both", pady=10)
        
        # Scrollbar for table
        self.tree_scroll = ttk.Scrollbar(frame)
        self.tree_scroll.pack(side="right", fill="y")

        # Table with scrollbar support and centered cell content
        self.tree = ttk.Treeview(frame, columns=("Match Time", "Home Team", "Away Team", "Home Win", "Draw", "Away Win", "Under 2.5", "Over 2.5"), show="headings", yscrollcommand=self.tree_scroll.set, style="Centered.Treeview")
        self.tree_scroll.config(command=self.tree.yview)
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")  # Center align each column

        self.tree.pack(expand=True, fill="both")

    def start_scraping_thread(self):
        # Start the scraping process in a new thread to keep the GUI responsive
        self.scrape_button.config(state="disabled")
        self.progress["value"] = 0
        self.status_label.config(text="Initializing scraping...")
        threading.Thread(target=self.scrape_data).start()

    def scrape_data(self):
        # Set up WebDriver options
        options = Options()
        options.add_argument("headless")
        options.add_argument("start-maximized")
        options.add_argument("disable-gpu")
        
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)
        
        # Open site and handle cookies
        driver.get("https://www.maxbet.ba/ba/pocetna")

        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'ds-cookies-consent-modal ion-button')))
            cookie_button.click()
            self.update_status("Accepted cookies.")
        except NoSuchElementException:
            self.update_status("No cookie button found.")

        try:
            danas = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-filter/ion-header/ion-row/ion-col[3]')))
            danas.click()
            self.update_status("Navigated to 'Danas'.")
            fudbal = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/ds-root/ion-app/div/ds-main-layout/ion-row/ion-row/div[1]/ds-left-menu-prematch/ds-offer-tree/ds-categories-list/ion-list/div/ion-item[1]/ion-label/ion-item/ion-label')))
            fudbal.click()
            self.update_status("Navigated to 'Fudbal'.")
        except NoSuchElementException:
            messagebox.showerror("Error", "Unable to navigate through the site")
            driver.quit()
            self.scrape_button.config(state="normal")
            return

        match_time, match_home_team, match_away_team = [], [], []
        odds_value_1, odds_value_x, odds_value_2, odds_value_15, odds_value_25 = [], [], [], [], []

        # Click on each league to load matches
        lige = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ds-leagues-list > div')))
        for i in lige:
            i.click()
            time.sleep(0.5)  # Minimized delay to avoid overwhelming the site

        all_matches = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ds-leagues-list .es-match')))
        total_matches = len(all_matches)

        for idx, match in enumerate(all_matches):
            try:
                match_time_TEMP = match.find_element(By.CSS_SELECTOR, '.es-match-kickoff').text
                match_time.append(match_time_TEMP)

                match_team_TEMP = match.find_elements(By.CSS_SELECTOR, '.es-match-teams-item')
                match_home_team.append(match_team_TEMP[0].text if len(match_team_TEMP) > 0 else "")
                match_away_team.append(match_team_TEMP[1].text if len(match_team_TEMP) > 1 else "")

                odds_TEMP = match.find_elements(By.CSS_SELECTOR, '.odd-btn .odd-btn--odd')
                odds_value_1.append(odds_TEMP[0].text if len(odds_TEMP) > 0 else "")
                odds_value_x.append(odds_TEMP[1].text if len(odds_TEMP) > 1 else "")
                odds_value_2.append(odds_TEMP[2].text if len(odds_TEMP) > 2 else "")
                odds_value_15.append(odds_TEMP[3].text if len(odds_TEMP) > 3 else "")
                odds_value_25.append(odds_TEMP[4].text if len(odds_TEMP) > 4 else "")

                # Update progress bar and status label
                progress_value = ((idx + 1) / total_matches) * 100
                self.update_progress(progress_value, f"Scraping match {idx + 1} of {total_matches}")
                
            except StaleElementReferenceException:
                continue

        driver.quit()
        
        # Create DataFrame
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
        self.display_data(df)
        self.scrape_button.config(state="normal")
        messagebox.showinfo("Scraping Complete", "Data scraping complete and displayed in table.")
        self.update_status("Scraping completed successfully.")

    def update_progress(self, value, status_text):
        # Update the progress bar and status label
        self.progress["value"] = value
        self.status_label.config(text=status_text)
        self.root.update_idletasks()

    def update_status(self, status_text):
        # Update the status label
        self.status_label.config(text=status_text)
        self.root.update_idletasks()

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
