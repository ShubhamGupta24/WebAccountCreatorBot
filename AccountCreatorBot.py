import time
import pandas as pd
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import dotenv_values
from datetime import datetime
import os
import undetected_chromedriver as uc
import sys
from fuzzywuzzy import fuzz

# Temporarily increase the recursion limit
sys.setrecursionlimit(1500)

def create_or_load_automation_data():
    """Create or load the automation tracking DataFrame"""
    filename = 'automation_tracker.csv'
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=[
            'timestamp',
            'user_login',
            'website',
            'status',  # 1 for success, 0 for failure
            'error_message',
            'form_fields',
            'steps_reached',
            'keyword_found'
        ])

def update_automation_status(df, user_login, website, status, form_fields="", error_message="", steps_reached="", keyword_found=""):
    """Update the DataFrame with new automation attempt"""
    new_row = {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'user_login': user_login,
        'website': website,
        'status': status,
        'error_message': error_message,
        'form_fields': form_fields,
        'steps_reached': steps_reached,
        'keyword_found': keyword_found
    }
    df.loc[len(df)] = new_row
    df.to_csv('automation_tracker.csv', index=False)
    return df

def fetch_websites_from_sheet(sheet_id):
    try:
        # Google API credentials
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "../webaccountcreationautomation-88a762a56e74.json",
            ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive",
             "https://www.googleapis.com/auth/spreadsheets"]
        )
        client = gspread.authorize(creds)

        sheet = client.open_by_key(sheet_id).sheet1

        data = sheet.get_all_values()
        df = pd.DataFrame(data[1:], columns=data[0])
        
        return df["Website"].dropna().tolist()
    
    except Exception as e:
        print(f"❌ ERROR: Failed to fetch websites from sheet: {str(e)}")
        return []

def crawl_for_specific_keywords(driver):
    keywords = ["Submit", "Submit your startup", "List my startup"]
    for keyword in keywords:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{keyword}')]"))
            )
            print(f"🔑 Found keyword: {keyword}")
            return keyword
        except TimeoutException:
            continue
    return ""

def search_for_register_text(driver):
    register_texts = ['Register', 'Sign up', 'Create Account']
    for text in register_texts:
        try:
            elements = driver.find_elements(By.XPATH, "//*")
            for element in elements:
                if fuzz.partial_ratio(text.lower(), element.text.lower()) > 75:
                    print(f"🔑 Found register text: {text}")
                    return element
        except TimeoutException:
            continue
    return None

def search_for_login_text(driver):
    login_texts = ['Login', 'Sign in']
    for text in login_texts:
        try:
            elements = driver.find_elements(By.XPATH, "//*")
            for element in elements:
                if fuzz.partial_ratio(text.lower(), element.text.lower()) > 75:
                    print(f"🔑 Found login text: {element.text}")
                    return element
        except TimeoutException:
            continue
    return None

def search_for_google_buttons(driver):
    google_button_locators = [
        "//div[contains(text(), 'Register with Google')]",
        "//a[contains(text(), 'Register with Google')]",
        "//span[contains(text(), 'Register with Google')]",
        "//button[contains(text(), 'Register with Google')]",
        "//button[contains(text(), 'Continue with Google')]",
        "//span[contains(text(), 'Continue with Google')]",
        "//div[contains(text(), 'Continue with Google')]",
        "//a[contains(text(), 'Continue with Google')]",
        "//div[contains(text(), 'Sign In with Google')]",
        "//a[contains(text(), 'Sign In with Google')]",
        "//span[contains(text(), 'Sign In with Google')]",
        "//button[contains(text(), 'Sign In with Google')]",
        "//div[contains(text(), 'Sign Up with Google')]",
        "//a[contains(text(), 'Sign Up with Google')]",
        "//span[contains(text(), 'Sign Up with Google')]",
        "//button[contains(text(), 'Sign Up with Google')]",
        "//div[contains(text(), 'Join with Google')]",
        "//a[contains(text(), 'Join with Google')]",
        "//span[contains(text(), 'Join with Google')]",
        "//button[contains(text(), 'Join with Google')]",
    ]
    for locator in google_button_locators:
        try:
            elements = driver.find_elements(By.XPATH, "//*")
            for element in elements:
                if fuzz.partial_ratio(locator.lower(), element.text.lower()) > 75:
                    print("🔑 Found Google button : ",element.text)
                    return element
        except TimeoutException:
            continue
    return None

def proceed_with_google_auth(driver, google_email, google_password, steps_reached):
    steps_reached += " -> Proceed with Google Auth"
    try:
        print("🔵 Step: Entering Google email...")
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        print("the email field is",email_field)
        email_field.send_keys(google_email)
        email_field.send_keys(Keys.RETURN)
        steps_reached += " -> Entered Google email"
        time.sleep(3)

        print("🔵 Step: Entering Google password...")
        password_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        print("the password field is",password_field)
        password_field.send_keys(google_password)
        password_field.send_keys(Keys.RETURN)
        steps_reached += " -> Entered Google password"
        time.sleep(5)

        # Handle CAPTCHA (Manual Input if needed)
        try:
            print("🔵 Checking for CAPTCHA...")
            captcha_detected = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
            if captcha_detected:
                steps_reached += " -> CAPTCHA detected"
                input("🚨 CAPTCHA detected! Solve it manually and press Enter to continue...")
        except TimeoutException:
            print("✅ No CAPTCHA detected. Proceeding...")

        # Switch back to initial window
        print("🔵 Step: Returning to initial window...")
        driver.switch_to.window(driver.window_handles[0])
        steps_reached += " -> Success"
        time.sleep(5)

        print("🎉 SUCCESS: Logged into website using Google!")
        return steps_reached
    except Exception as e:
        print(f"❌ ERROR: Google Signup/Login failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())
        steps_reached += " -> Failed at Google Auth"
        return steps_reached

def enter_email_password(driver, email, password, username, steps_reached):
    steps_reached += " -> Start Email/Password Entry"
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    try:
        print("🔵 Step: Locating email, password, and username fields...")
        
        # Locate email input field
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        print("the email field is",email_field)
        email_field.send_keys(email)
        steps_reached += " -> Entered email"

        # Locate password input field
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        print("the password field is",password_field)
        password_field.send_keys(password)
        steps_reached += " -> Entered password"

        # Locate username input field if present
        try:
            username_field = driver.find_element(By.XPATH, "//input[@name='username']")
            username_field.send_keys(username)
            steps_reached += " -> Entered username"
        except NoSuchElementException:
            print("Username field not found, continuing without it.")
        
        # Locate confirm password input field if present
        try:
            confirm_password_field = driver.find_element(By.XPATH, "//input[@name='confirm_password']")
            confirm_password_field.send_keys(password)
            steps_reached += " -> Entered confirm password"
        except NoSuchElementException:
            print("Confirm password field not found, continuing without it.")

        # Submit the form
        password_field.send_keys(Keys.RETURN)
        steps_reached += " -> Submitted form"
        time.sleep(5)

        # Handle CAPTCHA (Manual Input if needed)
        try:
            print("🔵 Checking for CAPTCHA...")
            captcha_detected = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
            if captcha_detected:
                steps_reached += " -> CAPTCHA detected"
                input("🚨 CAPTCHA detected! Solve it manually and press Enter to continue...")
        except TimeoutException:
            print("✅ No CAPTCHA detected. Proceeding...")

        print("🎉 SUCCESS: Logged into website using email and password!")
        steps_reached += " -> Success"
        return steps_reached, ""
    except Exception as e:
        print(f"❌ ERROR: Email/Password Signup/Login failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())
        steps_reached += " -> Failed at Email/Password Entry"
        return steps_reached, str(e)

def register_with_google(driver, google_email, google_password, steps_reached):
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    steps_reached += " -> Start Registration"
    keyword_found = ""  # Initialize keyword_found
    try:
        print("🔵 Step: Crawl for Register related texts...")

        # Look for Register related texts
        register_button = search_for_register_text(driver)

        if register_button:
            register_button.click()
            steps_reached += " -> Click Register"
            time.sleep(2)
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
        else:
            print("🔵 Step: Crawl for Login related texts...")
            login_button = search_for_login_text(driver)

            if login_button:
                login_button.click()
                steps_reached += " -> Click Login"
                time.sleep(2)
                current_url = driver.current_url
                print(f"Current URL: {current_url}")

                print("🔵 Step: Search for Register related texts again...")
                register_button = search_for_register_text(driver)
                if register_button:
                    register_button.click()
                    steps_reached += " -> Found register-related text after clicking login"
                    time.sleep(2)
                    current_url = driver.current_url
                    print(f"Current URL: {current_url}")

        print("🔵 Step: Search for Google buttons...")
        google_button = search_for_google_buttons(driver)
        
        if google_button:
            google_button.click()
            steps_reached += " -> Proceed with Google Auth"
            time.sleep(3)
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            steps_reached = proceed_with_google_auth(driver, google_email, google_password, steps_reached)
            return steps_reached, keyword_found
        else:
            # If Google button is not found, proceed with registration using email & password
            steps_reached += " -> Proceed with Registration Using Email & Password"
            return steps_reached, keyword_found

    except Exception as e:
        print(f"❌ ERROR: Google Signup/Login failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())
        steps_reached += " -> Failed at Registration"
        return steps_reached, keyword_found

def register_website(driver, website, email, password, username, user_login, automation_tracker_df):
    steps_reached = "Start"  # Initialize steps_reached
    keyword_found = ""  # Initialize keyword_found
    try:
        print(f"🔵 Attempting to register on: {website}")
        driver.get(website)
        time.sleep(3)

        # Crawl for specific keywords
        keyword_found = crawl_for_specific_keywords(driver)

        # Attempt to register using Google authentication
        steps_reached, _ = register_with_google(driver, email, password, steps_reached)
        if "Success" in steps_reached:
            print(f"✅ Successfully registered on {website}")
            form_fields = extract_form_fields(driver, website)
            update_automation_status(
                automation_tracker_df,
                user_login,
                website,
                1,
                steps_reached=steps_reached,
                form_fields=", ".join(form_fields),
                keyword_found=keyword_found
            )
            return True
        else:
            # If Google registration fails, try email/password registration
            steps_reached, error_message = enter_email_password(driver, email, password, username, steps_reached)
            if "Success" in steps_reached:
                print(f"✅ Successfully registered on {website}")
                form_fields = extract_form_fields(driver, website)
                update_automation_status(
                    automation_tracker_df,
                    user_login,
                    website,
                    1,
                    steps_reached=steps_reached,
                    form_fields=", ".join(form_fields),
                    keyword_found=keyword_found
                )
                return True
            else:
                # If both methods fail, log the failure
                update_automation_status(
                    automation_tracker_df,
                    user_login,
                    website,
                    0,
                    steps_reached=steps_reached,
                    error_message="Both email/password and Google registration failed: " + error_message,
                    keyword_found=keyword_found
                )
                return False

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: Failed to register on {website}: {error_msg}")
        update_automation_status(
            automation_tracker_df,
            user_login,
            website,
            0,
            steps_reached=steps_reached,
            error_message=error_msg,
            keyword_found=keyword_found
        )
        return False

def extract_form_fields(driver, website):
    """Extract form fields from the website"""
    try:
        # Add your form field extraction logic here
        # This is a placeholder
        return ["email", "password"]  # Replace with actual form fields
    except Exception as e:
        print(f"❌ ERROR: Failed to extract form fields from {website}: {str(e)}")
        return []

def main():
    current_user = "ShubhamGupta24"
    automation_tracker_df = create_or_load_automation_data()
    
    secrets = dotenv_values(".env")
    print("Secrets:", secrets)
    email = secrets["EMAIL"]
    password = secrets["PASSWORD"]
    username = secrets["USERNAME"]
    # sheet_id = secrets["SHEET_ID"]
    df = pd.read_csv('register_file.csv')

    websites = df['website']
    print("Websites:", websites)

    if websites.empty:
        print("❌ No websites found in the sheet.")
        return

    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.headless = False

    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
        "profile.default_content_setting_values.ads": 2,
        "profile.default_content_setting_values.cookies": 2
    }
    options.add_experimental_option("prefs", prefs)

    try:
        driver = uc.Chrome(options=options)
        
        for website in websites:
            if not website.startswith("https"):
                website = "https://" + website
            try:
                success = register_website(
                    driver,
                    website,
                    email,
                    password,
                    username,
                    current_user,
                    automation_tracker_df
                )
                
                print("\nAutomation Tracker Status:")
                print(automation_tracker_df.tail())
                
            except Exception as e:
                print(f"❌ ERROR processing {website}: {str(e)}")
                continue

    except Exception as e:
        print(f"❌ ERROR: Main process failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())

    finally:
        if 'driver' in locals():
            driver.quit()
        
        
        print("\nFinal Results:")
        print(automation_tracker_df.groupby('status').size())
        
        automation_tracker_df.to_csv('results.csv', index=False)
        print("\nProcess completed. Results saved to results.csv")

if __name__ == "__main__":
    main()