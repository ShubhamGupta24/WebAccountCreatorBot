import time
import pandas as pd
import gspread
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
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

def create_or_load_automation_data():
    """Create or load the automation tracking DataFrame"""
    filename = 'final_automation_tracking.csv'
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=[
            'timestamp',
            'user_login',
            'website',
            'status',  # 1 for success, 0 for failure
            'error_message',
            'form_fields'
        ])

def update_automation_status(df, user_login, website, status, form_fields="", error_message=""):
    """Update the DataFrame with new automation attempt"""
    new_row = {
        'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        'user_login': user_login,
        'website': website,
        'status': status,
        'error_message': error_message,
        'form_fields': form_fields
    }
    df.loc[len(df)] = new_row
    df.to_csv('final_automation_tracking.csv', index=False)
    return df

def fetch_websites_from_sheet(sheet_id):
    try:
        # Google API credentials
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "./webaccountcreationautomation-88a762a56e74.json",
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

def register_google(driver, google_email, google_password):
    try:
        print("🔵 Step 1: Clicking 'Sign In' button...")

        # Updated to check for multiple possible texts
        signin_texts = ['Sign in', 'Sign up', 'Login', 'Register']
        signin_button = None
        for text in signin_texts:
            try:
                signin_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{text}')]"))
                )
                if signin_button:
                    break
            except TimeoutException:
                continue

        if not signin_button:
            for text in signin_texts:
                try:
                    signin_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{text}')]"))
                    )
                    if signin_button:
                        break
                except TimeoutException:
                    continue

        if not signin_button:
            raise TimeoutException("🔴 Sign in/Sign up/Login/Register button not found.")

        signin_button.click()
        time.sleep(2)

        print("🔵 Step 2: Clicking 'Continue with Google'...")
        initial_window = driver.current_window_handle
        google_button_locators = [
            "//button[contains(text(), 'Sign in with Google')]",
            "//span[contains(text(), 'Sign in with Google')]",
            "//div[contains(text(), 'Sign in with Google')]"
        ]
        
        google_button = None
        for locator in google_button_locators:
            try:
                google_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, locator))
                )
                if google_button:
                    break
            except TimeoutException:
                continue
        
        if not google_button:
            raise TimeoutException("🔴 'Continue with Google' button not found.")

        google_button.click()
        time.sleep(3)

        print("🔵 Step 4: Entering Google email...")
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
        )
        email_field.send_keys(google_email)
        email_field.send_keys(Keys.RETURN)
        time.sleep(3)

        print("🔵 Step 5: Entering Google password...")
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        password_field.send_keys(google_password)
        password_field.send_keys(Keys.RETURN)
        time.sleep(5)

        # Handle CAPTCHA (Manual Input if needed)
        try:
            print("🔵 Checking for CAPTCHA...")
            captcha_detected = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
            if captcha_detected:
                input("🚨 CAPTCHA detected! Solve it manually and press Enter to continue...")
        except TimeoutException:
            print("✅ No CAPTCHA detected. Proceeding...")

        # Switch back to initial window
        print("🔵 Step 6: Returning to initial window...")
        driver.switch_to.window(initial_window)
        time.sleep(5)

        print("🎉 SUCCESS: Logged into website using Google!")
        return True

    except Exception as e:
        print(f"❌ ERROR: Google Signup/Login failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())
        return False

def register_website(driver, website, email, password, user_login, final_automation_tracking_df):
    """Handle registration for a specific website"""
    try:
        print(f"🔵 Attempting to register on: {website}")
        driver.get(website)
        time.sleep(3)

        # Attempt Google registration
        success = register_google(driver, email, password)
        
        if success:
            print(f"✅ Successfully registered on {website}")
            form_fields = extract_form_fields(driver, website)
            update_automation_status(
                final_automation_tracking_df,
                user_login,
                website,
                1,
                form_fields=", ".join(form_fields)
            )
            return True
        
        return False

    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: Failed to register on {website}: {error_msg}")
        update_automation_status(
            final_automation_tracking_df,
            user_login,
            website,
            0,
            error_message=error_msg
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
    current_user = "Sparklog"  # You can make this dynamic
    final_automation_tracking_df = create_or_load_automation_data()
    
    secrets = dotenv_values(".env")
    print("Secrets:", secrets)
    sheet_id = secrets["SHEET_ID"]

    websites = fetch_websites_from_sheet(sheet_id)

    if not websites:
        print("❌ No websites found in the sheet.")
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    prefs = {"profile.default_content_setting_values.notifications": 2}
    options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        for website in websites:
            try:
                success = register_website(
                    driver,
                    website,
                    secrets["EMAIL"],
                    secrets["PASSWORD"],
                    current_user,
                    final_automation_tracking_df
                )
                
                # Display current status
                print("\nAutomation Tracking Status:")
                print(final_automation_tracking_df.tail())
                
            except Exception as e:
                print(f"❌ ERROR processing {website}: {str(e)}")
                continue

    except Exception as e:
        print(f"❌ ERROR: Main process failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())

    finally:
        driver.quit()
        
        # Save final results
        print("\nFinal Results:")
        print(final_automation_tracking_df.groupby('status').size())
        
        # Export to CSV
        final_automation_tracking_df.to_csv('final_automation_results.csv', index=False)
        print("\nProcess completed. Results saved to final_automation_results.csv")

if __name__ == "__main__":
    main()