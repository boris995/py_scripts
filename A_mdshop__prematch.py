# prematch_script.py

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

# Function to set up Selenium WebDriver in headless mode
def setup_driver():
    options = Options()
    options.add_argument("start-maximized")
    options.add_experimental_option("detach", True)
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)
    return driver

# Function to update the progress label and bar
def update_status(message, progress=None):
    status_label.config(text=message)
    if progress is not None:
        progress_var.set(progress)
    root.update_idletasks()

# Pre-match script function
def run_pre_match_script():
    try:
        update_status("Starting pre-match script...", 0)
        driver = setup_driver()
        update_status("Opening pre-match webpage...", 10)
        driver.get("https://www.mdshop.ba/sport-prematch?sport=Ko%C5%A1arka&region=SAD&competition=NBA&competitionId=2-122-12")
        time.sleep(1)
        
        cookie_accept = driver.find_elements(By.CSS_SELECTOR, "#cookieContainer .cookieHeader .pointer")
        if cookie_accept:
            cookie_accept[0].click()
        
        driver.switch_to.default_content()
        driver.switch_to.frame('sportIframe')
        time.sleep(1)
        
        match_data = []
        page = driver.find_elements(By.CSS_SELECTOR, "div.selected-league")
        
        update_status("Collecting match data...", 40)
        for i in page:
            matchesandodds = i.find_elements(By.TAG_NAME, 'app-event')
            for j in matchesandodds:
                hometemp = j.find_element(By.CSS_SELECTOR, 'span.home').text
                awaytemp = j.find_element(By.CSS_SELECTOR, 'span.away').text
                try:
                    limestemp = j.find_element(By.XPATH, './/span[@data-market="Manje"]').find_element(By.XPATH, 'following-sibling::span[1]').text
                except NoSuchElementException:
                    limestemp = ""
                match_data.append({"home": hometemp, "away": awaytemp, "limit": limestemp})

        driver.quit()
        df = pd.DataFrame(match_data)
        df.to_excel("MDShop_BA_PREMATCH.xlsx", index=False)
        display_data(df)
        update_status("Pre-match data saved successfully!", 100)

    except WebDriverException as e:
        update_status(f"Error: {e}")

# Display the data in a table
def display_data(df):
    for row in prematch_tree.get_children():
        prematch_tree.delete(row)
    for _, row in df.iterrows():
        prematch_tree.insert("", "end", values=(row["home"], row["away"], row["limit"]))

# Make the table cells editable
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

# Save to Excel
def save_to_excel():
    rows = []
    for item in prematch_tree.get_children():
        row = prematch_tree.item(item, "values")
        rows.append(row)
    df = pd.DataFrame(rows, columns=["home", "away", "limit"])
    df.to_excel("MDShop_BA_PREMATCH.xlsx", index=False)

# GUI Setup
root = tk.Tk()
root.title("Pre-Match Script")
root.geometry("600x400")

frame = tk.Frame(root)
frame.pack(pady=10)

# Progress bar and status label
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
progress_bar.pack(pady=5)
status_label = tk.Label(frame, text="")
status_label.pack(pady=5)

# Run button
run_button = tk.Button(frame, text="Run Pre-Match Script", command=lambda: threading.Thread(target=run_pre_match_script).start())
run_button.pack(pady=5)

# Treeview for displaying pre-match data
prematch_tree = ttk.Treeview(frame, columns=("Home", "Away", "Limit"), show="headings", height=10)
prematch_tree.heading("Home", text="Home")
prematch_tree.heading("Away", text="Away")
prematch_tree.heading("Limit", text="Limit")
prematch_tree.pack()
prematch_tree.bind("<Double-1>", on_double_click)

root.mainloop()