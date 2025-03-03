import time
import pandas as pd
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from sentence_transformers import SentenceTransformer, util
from selenium.webdriver.common.action_chains import ActionChains
from urllib.parse import urlparse, urlunparse
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
    filename = 'latest_automation_tracker.csv'
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
        'timestamp': datetime.utcnow().strftime('%Y-%M-%d %H:%M:%S'),
        'user_login': user_login,
        'website': website,
        'status': status,
        'error_message': error_message,
        'form_fields': form_fields,
        'steps_reached': steps_reached,
        'keyword_found': keyword_found
    }
    df.loc[len(df)] = new_row
    df.to_csv('latest_automation_tracker.csv', index=False)
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

def save_screenshot(driver, website, action_desc):
    website_name = website.split("//")[-1].split("/")[0]
    folder_path = os.path.join("latest_screenshots", website_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    screenshot_path = os.path.join(folder_path, f"{action_desc}.png")
    driver.save_screenshot(screenshot_path)
    print(f"💾 Screenshot saved: {screenshot_path}")

def crawl_for_specific_keywords(driver, website):
    keywords = ["Submit", "Submit your startup", "List my startup"]
    for keyword in keywords:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{keyword}')]"))
            )
            print(f"🔑 Found keyword: {keyword}")
            save_screenshot(driver, website, f"keyword {keyword} found")
            return keyword
        except TimeoutException:
            continue
    return ""



def search_for_register_text(driver, website):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    register_texts = ['Register', 'Get Listed', 'Join', 'Sign up', 'Create Account', 'List your startup', 'Submit your startup', 'List my startup']
    register_embeddings = model.encode(register_texts, convert_to_tensor=True)
    # actions = ActionChains(driver)
    
    try:
        elements = driver.find_elements(By.XPATH, '//*[self::button or self::a or self::div or self::span or self::img or self::svg][text() or descendant::*[self::svg or self::img or contains(@class, "register")]]')
        for element in elements:
            # actions.move_to_element(element).perform()  # Hover to reveal hidden text
            element_text = element.text.strip() if element.text.strip() else element.get_attribute('title') or "Register Icon/Button"
            
            element_embedding = model.encode([element_text], convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(element_embedding, register_embeddings)
            max_similarity = similarities.max().item()
            
            if max_similarity > 0.8:  # Adjust threshold as needed
                print(f"🔑 Found register text: {element_text}")
                print("🔑 Matched with register phrase: ", register_texts[similarities.argmax().item()])
                save_screenshot(driver, website, f"register text {element_text} found")
                return element
    except TimeoutException:
        pass
    
    print("❌ No register buttons found.")
    return None
def search_for_login_text(driver, website):
    login_texts = ['Login', 'Sign in','Log in']
    for text in login_texts:
        try:
            elements = driver.find_elements(By.XPATH, f"//*[contains(., '{text}')]")
            for element in elements:
                if fuzz.ratio(text.lower(), element.text.lower()) > 90:
                    print(f"🔑 Found login text: {element.text}")
                    print("🔑 Found login button match with : ", text)
                    save_screenshot(driver, website, f"login text {text} found")
                    return element
        except TimeoutException:
            continue
    return None

def search_for_google_buttons(driver, website):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    google_button_texts = ['Register with Google', 'Continue with Google', 'Sign In with Google', 'Sign Up with Google', 'Join with Google', 'Google']
    google_embeddings = model.encode(google_button_texts, convert_to_tensor=True)
    # actions = ActionChains(driver)
    
    try:
        elements = driver.find_elements(By.XPATH, '//*[self::button or self::a or self::div or self::span or self::img or self::svg][text() or descendant::*[self::svg or self::img or contains(@class, "google")]]')
        for element in elements:
            # actions.move_to_element(element).perform()  # Hover to reveal hidden text
            element_text = element.text.strip() if element.text.strip() else element.get_attribute('title') or "Google Icon/Button"
            
            element_embedding = model.encode([element_text], convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(element_embedding, google_embeddings)
            max_similarity = similarities.max().item()
            
            if max_similarity > 0.7:  # Adjust threshold as needed
                print(f"🔑 Found Google button: {element_text}")
                print("🔑 Matched with Google phrase: ", google_button_texts[similarities.argmax().item()])
                save_screenshot(driver, website, f"Google button {element_text} found")
                return element
    except TimeoutException:
        pass
    
    print("❌ No Google buttons found.")
    return None


def proceed_with_google_auth(driver, google_email, google_password, steps_reached, website):
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
        save_screenshot(driver, website, "entered google email")

        print("🔵 Step: Entering Google password...")
        password_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        print("the password field is",password_field)
        password_field.send_keys(google_password)
        password_field.send_keys(Keys.RETURN)
        steps_reached += " -> Entered Google password"
        time.sleep(5)
        save_screenshot(driver, website, "entered google password")

        # Handle CAPTCHA (Manual Input if needed)
        try:
            print("🔵 Checking for CAPTCHA...")
            captcha_detected = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
            if captcha_detected:
                steps_reached += " -> CAPTCHA detected"
                save_screenshot(driver, website, "captcha detected")
                input("🚨 CAPTCHA detected! Solve it manually and press Enter to continue...")
        except TimeoutException:
            print("✅ No CAPTCHA detected. Proceeding...")

        # Switch back to initial window
        print("🔵 Step: Returning to initial window...")
        driver.switch_to.window(driver.window_handles[0])
        steps_reached += " -> Success"
        time.sleep(5)
        save_screenshot(driver, website, "returned to initial window")

        print("🎉 SUCCESS: Logged into website using Google!")
        return steps_reached
    except Exception as e:
        print(f"❌ ERROR: Google Signup/Login failed: {str(e)}")
        print("Stacktrace:", traceback.format_exc())
        steps_reached += " -> Failed at Google Auth"
        return steps_reached


def enter_email_password(driver, email, password, username, steps_reached, website):
    context = {
    "first_name": "John",
    "last_name": "Doe",
    "email": email,
    "password": password,
    "username": username,
    "forurl": "https://example.com",
    "agree_tnc": True,  # Terms & conditions
    "subscribe_newsletter": False  # Optional
    }

    name_labels = {
    "first_name": ["first name", "given name", "name", "your first name", "fname"],
    "last_name": ["last name", "surname", "family name", "your last name", "lname"],
    "forurl": ["website", "url", "your site", "homepage", "portfolio", "company website"],
    "agree_tnc": ["agree", "terms", "terms and conditions", "i agree", "accept terms"],
    "subscribe_newsletter": ["subscribe", "newsletter", "sign up for updates", "email updates"]
    }

    model = SentenceTransformer('all-MiniLM-L6-v2')
    steps_reached += " -> Start Email/Password Entry"
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    
    try:
        print("🔵 Step: Locating form fields using context...")

        # Locate all input fields
        input_fields = driver.find_elements(By.XPATH, "//input")

        for field in input_fields:
            try:
                label = field.get_attribute('aria-label') or field.get_attribute('placeholder') or field.get_attribute('name')
                if not label:
                    continue

                label_embedding = model.encode([label], convert_to_tensor=True)
                for key, synonyms in name_labels.items():
                    key_embeddings = model.encode(synonyms, convert_to_tensor=True)
                    similarities = util.pytorch_cos_sim(label_embedding, key_embeddings)
                    if similarities.max().item() > 0.7:
                        value = context.get(key)
                        if value:
                            driver.execute_script("arguments[0].scrollIntoView(true);", field)
                            field.send_keys(str(value))
                            steps_reached += f" -> Entered {key}"
            except StaleElementReferenceException:
                print("⚠️ Stale element encountered, skipping field.")
                continue

        # Locate checkboxes
        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for checkbox in checkboxes:
            try:
                label = checkbox.get_attribute('aria-label') or checkbox.get_attribute('name')
                if not label:
                    continue

                label_embedding = model.encode([label], convert_to_tensor=True)
                for key, synonyms in name_labels.items():
                    if key in ["agree_tnc", "subscribe_newsletter"]:
                        key_embeddings = model.encode(synonyms, convert_to_tensor=True)
                        similarities = util.pytorch_cos_sim(label_embedding, key_embeddings)
                        if similarities.max().item() > 0.7 and context.get(key):
                            if not checkbox.is_selected():
                                driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                                checkbox.click()
                                steps_reached += f" -> Checked {key}"
                                time.sleep(1)
            except StaleElementReferenceException:
                print("⚠️ Stale element encountered, skipping checkbox.")
                continue

        # Submit the form if possible
        try:
            password_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
            )
            password_field.send_keys(Keys.RETURN)
            steps_reached += " -> Submitted form"
        except TimeoutException:
            print("⚠️ Password field for submission not found. Attempting generic form submission.")
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Submit') or contains(text(), 'Sign up') or contains(text(), 'Register')]")
            if submit_buttons:
                submit_buttons[0].click()
                steps_reached += " -> Submitted using submit button"
                time.sleep(2)
        
        time.sleep(5)
        save_screenshot(driver, website, "submitted form")

        # Handle CAPTCHA (Manual Input if needed)
        try:
            print("🔵 Checking for CAPTCHA...")
            captcha_detected = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//iframe[contains(@title, 'recaptcha')]"))
            )
            if captcha_detected:
                steps_reached += " -> CAPTCHA detected"
                save_screenshot(driver, website, "captcha detected")
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

def register_with_google(driver, google_email, google_password, steps_reached, website):
    current_url = driver.current_url
    print(f"Current URL: {current_url}")
    steps_reached += " -> Start Registration"
    keyword_found = ""  # Initialize keyword_found
    try:
        print("🔵 Step: Crawl for Register related texts...")

        # Look for Register related texts
        register_button = search_for_register_text(driver, website)

        if register_button:
            register_button.click()
            steps_reached += " -> Click Register"
            time.sleep(2)
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            save_screenshot(driver, website, "clicked register button")
        else:
            print("🔵 Step: Crawl for Login related texts...")
            login_button = search_for_login_text(driver, website)

            if login_button:
                login_button.click()
                steps_reached += " -> Click Login"
                time.sleep(3)
                current_url = driver.current_url
                print(f"Current URL: {current_url}")
                save_screenshot(driver, website, "clicked login button")

                print("🔵 Step: Search for Register related texts again...")
                register_button = search_for_register_text(driver, website)
                if register_button:
                    register_button.click()
                    steps_reached += " -> Found register-related text after clicking login"
                    time.sleep(3)    
                    current_url = driver.current_url
                    print(f"Current URL: {current_url}")
                    save_screenshot(driver, website, "clicked register button after login")

        print("🔵 Step: Search for Google buttons...")
        google_button = search_for_google_buttons(driver, website)
        
        if google_button:
            google_button.click()
            steps_reached += " -> Proceed with Google Auth"
            time.sleep(3)
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            save_screenshot(driver, website, "clicked google button")
            steps_reached = proceed_with_google_auth(driver, google_email, google_password, steps_reached, website)
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

def register_website(driver, website, email, password, username, user_login, latest_automation_tracker_df):
    steps_reached = "Start"  # Initialize steps_reached
    keyword_found = ""  # Initialize keyword_found
    try:
        print(f"🔵 Attempting to register on: {website}")
        driver.get(website)
        time.sleep(3)
        save_screenshot(driver, website, "loaded website")

        # Crawl for specific keywords
        keyword_found = crawl_for_specific_keywords(driver, website)

        # Attempt to register using Google authentication
        steps_reached, _ = register_with_google(driver, email, password, steps_reached, website)
        if "Success" in steps_reached:
            print(f"✅ Successfully registered on {website}")
            form_fields = extract_form_fields(driver, website)
            update_automation_status(
                latest_automation_tracker_df,
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
            steps_reached, error_message = enter_email_password(driver, email, password, username, steps_reached, website)
            if "Success" in steps_reached:
                print(f"✅ Successfully registered on {website}")
                form_fields = extract_form_fields(driver, website)
                update_automation_status(
                    latest_automation_tracker_df,
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
                    latest_automation_tracker_df,
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
            latest_automation_tracker_df,
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


def process_link(url):
    parsed_url = urlparse(url)
    if parsed_url.scheme == "http":
        return urlunparse(parsed_url._replace(scheme="https"))
    elif not parsed_url.scheme:
        return "https://" + url
    return url

def main():
    current_user = "ShubhamGupta24"
    latest_automation_tracker_df = create_or_load_automation_data()
    
    secrets = dotenv_values(".env")
    print("Secrets:", secrets)
    email = secrets["EMAIL"]
    password = secrets["PASSWORD"]
    username = secrets["USERNAME"]
    sheet_id = secrets["SHEET_ID"]
    # df = pd.read_csv('filtered_file.csv')
    

    # websites = fetch_websites_from_sheet(sheet_id)
    df=pd.read_csv('Updated_deduplicated_output.csv')
    websites = df['Website'].tolist()

    if websites==[]:
        print("❌ No websites found in the sheet.")
        return

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument("--incognito")
    
    options.headless = False

    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
        "profile.default_content_setting_values.ads": 2
    }
    options.add_experimental_option("prefs", prefs)

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
        
        for website in websites:
            website = process_link(website)
            try:
                success = register_website(
                    driver,
                    website,
                    email,
                    password,
                    username,
                    current_user,
                    latest_automation_tracker_df
                )
                
                print("\nAutomation Tracker Status:")
                print(latest_automation_tracker_df.tail())
                
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
        print(latest_automation_tracker_df.groupby('status').size())
        
        latest_automation_tracker_df.to_csv('latest_auto_results.csv', index=False)
        print("\nProcess completed. Results saved to results.csv")

if __name__ == "__main__":
    main()