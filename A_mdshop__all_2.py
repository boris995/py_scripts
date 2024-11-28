import tkinter as tk
from tkinter import ttk
import pandas as pd
import threading
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from datetime import datetime
import time
from selenium.webdriver.common.by import By

# Setup for Selenium WebDriver in headless mode
def setup_driver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_argument("--headless")  # Enable headless mode
    options.add_experimental_option("detach", True)
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

# Function to update the progress label and bar
def update_status(message, progress=None):
    status_label.config(text=message)
    if progress is not None:
        progress_var.set(progress)
    root.update_idletasks()

# Load pre-match data from Excel
def load_prematch_data():
    global pre_match_df
    pre_match_df = pd.read_excel("MDShop_BA_PREMATCH.xlsx")
    display_data(pre_match_df)

# Display pre-match data and editable cells
def display_data(df):
    for row in prematch_tree.get_children():
        prematch_tree.delete(row)
    for _, row in df.iterrows():
        prematch_tree.insert("", "end", values=(row["home"], row["away"], row["limit"], ""))

# Check for limit changes and display alerts in the 'Changes' column
def check_for_alerts(live_data):
    for _, live_row in live_data.iterrows():
        live_match = (live_row["home"], live_row["away"])
        live_limit = float(live_row["limit"]) if is_float(live_row["limit"]) else None

        # Check if this live match exists in the pre-match data
        pre_match = pre_match_df[(pre_match_df["home"] == live_match[0]) & (pre_match_df["away"] == live_match[1])]
        
        if not pre_match.empty:
            pre_limit_value = pre_match.iloc[0]["limit"]
            pre_limit = float(pre_limit_value) if is_float(pre_limit_value) else None

            # Update 'Changes' if limit changes significantly or if new live data available
            for row_id in prematch_tree.get_children():
                row_values = prematch_tree.item(row_id, "values")
                if row_values[0] == live_match[0] and row_values[1] == live_match[1]:
                    if live_limit is not None and pre_limit is not None and abs(live_limit - pre_limit) > threshold_difference:
                        change_text = f"{pre_limit} ---> {live_limit}"
                        prematch_tree.item(row_id, values=(row_values[0], row_values[1], row_values[2], change_text))
                    elif pre_limit is None and live_limit is not None:
                        change_text = f"Not available ---> {live_limit}"
                        prematch_tree.item(row_id, values=(row_values[0], row_values[1], row_values[2], change_text))

# Function to fetch live data
def run_live_script():
    try:
        update_status("Starting live script...", 0)
        driver = setup_driver()
        update_status("Opening live webpage...", 10)
        driver.get("https://www.mdshop.ba/sport-live")
        time.sleep(1)
        
        cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
        if cookie_accept:
            cookie_accept[0].click()
        
        driver.switch_to.default_content()
        driver.switch_to.frame('sportLiveIframe')

        driver.find_elements(By.XPATH, '//*[@id="centerContent"]/app-sport-groups-container/app-sport-group[2]/section/div')[0].click()
        
        update_status("Collecting live match data...", 50)

        while True:
            match_data = []
            page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
            for i in page:
                matchesandodds = i.find_elements(By.TAG_NAME, 'app-event-live')
                for j in matchesandodds:
                    hometemp = j.find_element(By.CSS_SELECTOR, 'span.home').text
                    awaytemp = j.find_element(By.CSS_SELECTOR, 'span.away').text
                    try:
                        limestemp = j.find_element(By.XPATH, './/span[@data-market="Manje"]').find_element(By.XPATH, 'following-sibling::span[1]').text
                    except NoSuchElementException:
                        limestemp = "Not available"
                    match_data.append({"home": hometemp, "away": awaytemp, "limit": limestemp})
            
            # Update the live data table
            live_df = pd.DataFrame(match_data)
            check_for_alerts(live_df)
            time.sleep(5)

    except WebDriverException as e:
        error_msg = f"Error: {str(e).splitlines()[-1]}. Please try running the live script again."
        update_status(error_msg)

# Make the Pre-Match Treeview editable
def on_double_click(event):
    item_id = prematch_tree.focus()
    column = prematch_tree.identify_column(event.x)
    if item_id:
        col_idx = int(column.replace('#', '')) - 1
        current_value = prematch_tree.item(item_id, 'values')[col_idx]
        entry_widget = tk.Entry(prematch_tree)
        entry_widget.insert(0, current_value)
        entry_widget.place(x=event.x, y=event.y)
        
        def save_edit(event=None):
            new_value = entry_widget.get()
            current_values = list(prematch_tree.item(item_id, 'values'))
            current_values[col_idx] = new_value
            prematch_tree.item(item_id, values=current_values)
            entry_widget.destroy()
            save_to_excel()

        entry_widget.bind("<Return>", save_edit)
        entry_widget.bind("<FocusOut>", lambda e: entry_widget.destroy())
        entry_widget.focus()

# Save edited pre-match data to Excel
def save_to_excel():
    rows = []
    for item in prematch_tree.get_children():
        row = prematch_tree.item(item, "values")
        rows.append(row[:3])  # Only save home, away, and limit
    df = pd.DataFrame(rows, columns=["home", "away", "limit"])
    df.to_excel("MDShop_BA_PREMATCH.xlsx", index=False)

# Check if a value is a float
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# GUI Setup
root = tk.Tk()
root.title("Pre-Match and Live Script")
root.geometry("800x600")

# Frame for the main table
frame = tk.Frame(root)
frame.pack(pady=10)

# Treeview for displaying pre-match and live updates in one table
prematch_tree = ttk.Treeview(frame, columns=("Home", "Away", "Limit", "Changes"), show="headings", height=15)
prematch_tree.heading("Home", text="Home")
prematch_tree.heading("Away", text="Away")
prematch_tree.heading("Limit", text="Limit")
prematch_tree.heading("Changes", text="Changes")
prematch_tree.pack()
prematch_tree.bind("<Double-1>", on_double_click)

# Progress bar and status label
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
progress_bar.pack(pady=5)
status_label = tk.Label(root, text="")
status_label.pack(pady=5)

# Load Pre-Match button
load_button = tk.Button(root, text="Load Pre-Match Data", command=load_prematch_data)
load_button.pack(pady=5)

# Threshold entry for alert difference
threshold_label = tk.Label(root, text="Enter limit difference threshold:")
threshold_label.pack(pady=5)
threshold_entry = tk.Entry(root)
threshold_entry.pack(pady=5)
threshold_difference = 2  # Default threshold if user does not enter any

# Set threshold and start live script
def set_threshold_and_start():
    global threshold_difference
    try:
        threshold_difference = float(threshold_entry.get())
    except ValueError:
        threshold_difference = 2  # Default value if input is invalid
    threading.Thread(target=run_live_script).start()

# Run Live Script button
run_button = tk.Button(root, text="Run Live Script", command=set_threshold_and_start)
run_button.pack(pady=5)

root.mainloop()
