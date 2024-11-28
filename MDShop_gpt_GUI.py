import tkinter as tk
import pandas as pd
import threading
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import time
from selenium.webdriver.common.by import By
from tkinter import ttk, scrolledtext, Tk, DoubleVar

# Function to set up Selenium WebDriver in headless mode
def setup_driver():
    options = Options()
    options.add_argument("--headless")  # Enable headless mode
    options.add_argument("--start-maximized")
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

# Function to update the progress label and bar
def update_status(message, progress=None):
    status_label.config(text=message)
    if progress is not None:
        progress_var.set(progress)
    root.update_idletasks()

# Pre-match script function with progress bar and error handling
def run_pre_match_script():
    try:
        update_status("Starting pre-match script...", 0)
        driver = setup_driver()
        
        update_status("Opening pre-match webpage...", 10)
        driver.get("https://www.mdshop.ba/sport-prematch?sport=Ko%C5%A1arka&region=SAD&competition=NBA&competitionId=2-122-12")
        time.sleep(1)

        update_status("Accepting cookies...", 20)
        cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
        if cookie_accept:
            cookie_accept[0].click()

        update_status("Switching frames...", 30)
        driver.switch_to.default_content()
        driver.switch_to.frame('sportIframe')

        match_data = []
        page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
        total_matches = sum(len(i.find_elements(By.TAG_NAME, 'app-event')) for i in page)
        match_counter = 0

        update_status("Collecting match data...", 40)
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

                # Update progress bar for each match
                match_counter += 1
                progress_percent = 40 + (match_counter / total_matches) * 60
                update_status(f"Processing match {match_counter}/{total_matches}...", progress_percent)

        driver.quit()

        update_status("Saving data to Excel...", 100)
        # Save pre-match limits to Excel
        df = pd.DataFrame(match_data)
        df.to_excel("pre_match_limits.xlsx", index=False)

        update_status("Pre-match limits saved successfully!")
        display_pre_match_limits()

    except WebDriverException as e:
        update_status(f"Error: {e}")
        alert_textbox.insert(tk.END, f"Error occurred: {e}\nClick 'Run Again' to retry.\n")
        enable_retry_pre_match()

# Display pre-match and live match limits in a unified table
def display_pre_match_limits():
    try:
        df = pd.read_excel("pre_match_limits.xlsx")
        # Clear the treeview table
        for row in tree.get_children():
            tree.delete(row)

        # Insert data into the treeview table
        for index, row in df.iterrows():
            tree.insert("", "end", values=(row['home'], row['away'], row['limit'], ""))

    except Exception as e:
        update_status(f"Error: {e}")

# Live script function with user-defined limit difference and error handling
def run_live_script(difference_threshold):
    try:
        update_status("Starting live script...", 0)
        driver = setup_driver()

        update_status("Opening live webpage...", 10)
        driver.get("https://www.mdshop.ba/sport-live")
        time.sleep(1)

        update_status("Accepting cookies...", 20)
        cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
        if cookie_accept:
            cookie_accept[0].click()

        update_status("Switching frames...", 30)
        driver.switch_to.default_content()
        driver.switch_to.frame('sportLiveIframe')

        update_status("Collecting live match data...", 50)
        pre_match_limits = pd.read_excel("pre_match_limits.xlsx")
        pre_match_limits_dict = {(row['home'], row['away']): float(row['limit']) for index, row in pre_match_limits.iterrows()}
        last_live_limits = {}

        while True:
            live_limits = {}
            page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
            for i in page:
                matchesandodds = i.find_elements(By.TAG_NAME, 'app-event-live')
                for j in matchesandodds:
                    hometemp = j.find_element(By.CSS_SELECTOR, 'span.home').text
                    awaytemp = j.find_element(By.CSS_SELECTOR, 'span.away').text
                    match = (hometemp, awaytemp)

                    if match in pre_match_limits_dict:
                        try:
                            limit_text = j.find_element(By.XPATH, './/span[@data-market="Manje"]').find_element(By.XPATH, 'following-sibling::span[1]').text
                            limestemp = float(limit_text)
                            live_limits[match] = limestemp
                        except (ValueError, NoSuchElementException):
                            live_limits[match] = None

            # Update the table for missing and changed live limits
            for row_id in tree.get_children():
                row_values = tree.item(row_id, "values")
                match = (row_values[0], row_values[1])
                if match in live_limits:
                    live_limit = live_limits[match]
                    pre_limit = pre_match_limits_dict.get(match)
                    if live_limit is not None and pre_limit is not None:
                        if abs(live_limit - pre_limit) >= difference_threshold:
                            change = f"Changed from {pre_limit} to {live_limit}"
                            tree.item(row_id, values=(row_values[0], row_values[1], row_values[2], change))
                        else:
                            tree.item(row_id, values=(row_values[0], row_values[1], row_values[2], "No Change"))
                else:
                    tree.item(row_id, values=(row_values[0], row_values[1], row_values[2], "Not Live"))

            time.sleep(5)

    except WebDriverException as e:
        update_status(f"Error: {e}")
        alert_textbox.insert(tk.END, f"Error occurred: {e}\nClick 'Run Again' to retry.\n")
        enable_retry_live_script()

# Function to send alerts and display them in the GUI
def send_alert(match, pre_limit, live_limit):
    alert_message = f"ALERT: Limit changed for {match}: {pre_limit} -> {live_limit}\n"
    alert_textbox.insert(tk.END, alert_message)
    alert_textbox.see(tk.END)

# Enable retry button after an error
def enable_retry_pre_match():
    retry_pre_match_button.config(state=tk.NORMAL)

def enable_retry_live_script():
    retry_live_button.config(state=tk.NORMAL)

# Function to start the live script in a separate thread with user input
def start_live_script():
    try:
        difference_threshold = float(threshold_entry.get())
    except ValueError:
        difference_threshold = 2  # Default value if input is invalid
    threading.Thread(target=run_live_script, args=(difference_threshold,)).start()

# Create the main Tkinter window
root = tk.Tk()
root.title("Pre-Match and Live Script GUI")
root.geometry("800x600")

# Frame for pre-match and live table
pre_match_frame = tk.Frame(root)
pre_match_frame.pack(pady=10)

# Button to run the pre-match script
pre_match_button = tk.Button(pre_match_frame, text="Run Pre-Match Script", command=lambda: threading.Thread(target=run_pre_match_script).start())
pre_match_button.pack(pady=5)

# Retry button for pre-match script
retry_pre_match_button = tk.Button(pre_match_frame, text="Run Again", command=lambda: threading.Thread(target=run_pre_match_script).start(), state=tk.DISABLED)
retry_pre_match_button.pack(pady=5)

# Progress bar and status label
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(pre_match_frame, variable=progress_var, maximum=100)
progress_bar.pack(pady=5)
status_label = tk.Label(pre_match_frame, text="")
status_label.pack(pady=5)

# Unified table for both pre-match and live data
tree = ttk.Treeview(pre_match_frame, columns=("Home", "Away", "Limit", "Alert"), show='headings', height=15)
tree.heading("Home", text="Home")
tree.heading("Away", text="Away")
tree.heading("Limit", text="Limit")
tree.heading("Alert", text="Alert")
tree.pack()

# Frame for threshold and start button
live_frame = tk.Frame(root)
live_frame.pack(pady=10)

# Threshold input and button for live script
threshold_label = tk.Label(live_frame, text="Enter limit difference threshold:")
threshold_label.pack(pady=5)
threshold_entry = tk.Entry(live_frame)
threshold_entry.pack(pady=5)
live_button = tk.Button(live_frame, text="Run Live Script", command=start_live_script)
live_button.pack(pady=5)

# Retry button for live script
retry_live_button = tk.Button(live_frame, text="Run Again", command=start_live_script, state=tk.DISABLED)
retry_live_button.pack(pady=5)

# Textbox for alerts
alert_textbox = scrolledtext.ScrolledText(root, height=5, width=70)
alert_textbox.pack()

# Run the Tkinter event loop
root.mainloop()
