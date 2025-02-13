from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def fetch_websites_from_sheet(sheet_url):
    # Google API credentials (replace with your JSON key file)
    creds = ServiceAccountCredentials.from_json_keyfile_name("./webaccountcreationautomation-88a762a56e74.json",
                                                             ["https://www.googleapis.com/auth/spreadsheets","https://www.googleapis.com/auth/drive","https://www.googleapis.com/auth/spreadsheets"])
    client = gspread.authorize(creds)

    # Extract sheet ID from the URL
    import re
    sheet_id = "1vgHkgBjOkvip0eHoJ6NrzD611bA5JJKseyYHNPcFJ7k"

    sheet = client.open_by_key(sheet_id).sheet1  # Access the first sheet

    # Get all data
    data = sheet.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])  # Convert to DataFrame, assuming first row is headers

    return df["Website"].dropna().tolist()  # Adjust column name based on actual sheet data


def extract_form_fields(driver, url):
    driver.get(url)
    time.sleep(3)  # Wait for the page to load

    form_fields = []
    input_elements = driver.find_elements(By.TAG_NAME, "input")
    for input_elem in input_elements:
        field_type = input_elem.get_attribute("type")
        field_name = input_elem.get_attribute("name") or input_elem.get_attribute("id")
        if field_type in ["text", "email", "password"] and field_name:
            form_fields.append(field_name)

    return form_fields

def register_account(driver, url, email, password):
    driver.get(url)
    time.sleep(3)

    # Find the input fields
    email_field = driver.find_element(By.XPATH, "//input[@type='email']")
    password_field = driver.find_element(By.XPATH, "//input[@type='password']")
    submit_button = driver.find_element(By.XPATH, "//button[@type='submit']")

    # Fill the form and submit
    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()
    time.sleep(5)  # Wait for registration to complete

    return True

def main():
    sheet_url = "https://docs.google.com/spreadsheets/d/1jmcx-APfMQ8ZM5mBffNVdL1dYkGoWKAZ/edit?usp=sharing&ouid=116536410878783318591&rtpof=true&sd=true"
    websites = fetch_websites_from_sheet(sheet_url)

    driver = webdriver.Chrome()
    data = []

    for site in websites:
        try:
            form_fields = extract_form_fields(driver, site)
            success = register_account(driver, site, "sparklog.marketing@gmail.com", "Sparklog@2025")
            data.append({"Website": site, "Form Fields": ", ".join(form_fields), "Status": "Success" if success else "Failed"})
        except Exception as e:
            data.append({"Website": site, "Form Fields": "Error", "Status": f"Failed - {str(e)}"})

    driver.quit()
    df = pd.DataFrame(data)
    df.to_csv("website_registration_results.csv", index=False)
    print("Process completed. Results saved to website_registration_results.csv")

if __name__ == "__main__":
    main()
