from datetime import datetime, timezone
import os
from dotenv import dotenv_values
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urlunparse
from selenium.webdriver.chrome.service import Service
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_or_load_automation_data():
    """Create or load the automation tracking DataFrame"""
    filename = 'uneed_automation_tracker.csv'
    if os.path.exists(filename):
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=[
            'timestamp',
            'user_login',
            'website',
            'status',  # 1 for success, 0 for failure
            'error_message',
            'steps_reached',
            'keyword_found'
        ])

def update_automation_status(df, user_login, website, status, error_message="", steps_reached="", keyword_found=""):
    """Update the DataFrame with Uneed automation attempt"""
    automation_row = {
        'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
        'user_login': user_login,
        'website': website,
        'status': status,
        'error_message': error_message,
        'steps_reached': steps_reached,
        'keyword_found': keyword_found
    }
    df.loc[len(df)] = automation_row
    df.to_csv('uneed_automation_tracker.csv', index=False)
    return df

def save_screenshot(driver, website, action_desc):
    """Save a screenshot of the current browser state"""
    website_name = website.split("//")[-1].split("/")[0]
    folder_path = os.path.join("uneed_screenshots", website_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    screenshot_path = os.path.join(folder_path, f"{action_desc}_{int(time.time())}.png")
    driver.save_screenshot(screenshot_path)
    logging.info(f"💾 Screenshot saved: {screenshot_path}")

def setup_driver():
    """Set up and return a configured ChromeDriver instance"""
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--incognito")
    # Block Notifications
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_setting_values.popups": 2,
        "profile.default_content_setting_values.ads": 2,
    }
    options.add_experimental_option("prefs", prefs)

    # Use webdriver_manager to automatically manage ChromeDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def login_register(driver, google_email, google_password):
    """Automate the Google login process on Uneed"""
    logging.info("🔵 Step 1: Clicking 'Log In' button...")
    signin_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Log in')]"))
    )
    signin_button.click()
    save_screenshot(driver, "uneed", "click_log_in_button")
    logging.info("Clicked on Log In Button")
    time.sleep(2)  # Wait for the login form to load
    initial_window = driver.current_window_handle

    # Now find and click the Google button
    logging.info("🔵 Clicking 'Continue with Google'...")
    google_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Sign in with Google')]"))
    )
    google_button.click()
    save_screenshot(driver, "uneed", "click_continue_with_google")
    time.sleep(2)

    logging.info("🔵 Step 4: Entering Google email...")
    email_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
    )
    email_field.send_keys(google_email)
    email_field.send_keys(Keys.RETURN)
    save_screenshot(driver, "uneed", "shared_email_to_website")

    time.sleep(4)

    logging.info("🔵 Step 5: Entering Google password...")
    password_field = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "Passwd"))
    )
    password_field.send_keys(google_password)
    password_field.send_keys(Keys.RETURN)
    save_screenshot(driver, "uneed", "shared_password_to_website")
    time.sleep(5)

    try:
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Continue')]"))).click()
        time.sleep(5)
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="headlessui-dialog-panel-v-11"]/div[1]/buttons'))).click()
    except:
        pass

    # Switch back to the original window
    driver.switch_to.window(initial_window)
    logging.info("🎉 SUCCESS: Logged into Uneed using Google!")
    return 'success'

def add_product_handle(driver):
    """Listing a product on Uneed"""
    logging.info("Listing a product")
    try:
        try:
            add_product_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Add your product")]'))
            )
            add_product_btn.click()
            save_screenshot(driver, "uneed", "navigating_to_add_product")
            logging.info("Success: Navigated to Add Product")
        except Exception as e:
            logging.error(f"Error: Navigating to Add Product - {str(e)}")

        time.sleep(2)

        try:
            product_name = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div[2]/div/div/form/div[1]/div[2]/div/input'))
            )
            product_name.send_keys("Fin Tech Revo")
            save_screenshot(driver, "uneed", "product_name")
            logging.info("Success: Added product name")
        except Exception as e:
            logging.error(f"Error: Adding product name - {str(e)}")

        time.sleep(3)

        try:
            product_url = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div[2]/div/div/form/div[2]/div[2]/div/input'))
            )
            product_url.send_keys("https://fintechrevolution.io")
            save_screenshot(driver, "uneed", "product_url")
            logging.info("Success: Added product URL")
        except Exception as e:
            logging.error(f"Error: Adding product URL - {str(e)}")

        try:
            submit_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div[2]/div/div/form/button'))
            )
            submit_btn.click()
            save_screenshot(driver, "uneed", "submit_product")
            logging.info("Success: Submitted product form")
        except Exception as e:
            logging.error(f"Error: Submitting product form - {str(e)}")

        time.sleep(10)

        try:
            price_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div/div[2]/form/div/div[2]/div[1]/div/div[3]/div[1]/div[2]/div/select'))
            )
            price = Select(price_element)
            price.select_by_visible_text("Freemium")
            save_screenshot(driver, "uneed", "product_price")
            logging.info("Success: Added product price")
        except Exception as e:
            logging.error(f"Error: Adding product price - {str(e)}")
        time.sleep(2)

        try:
            category_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div[2]/div[2]/form/div/div[2]/div[1]/div/div[2]/div[2]/div[2]/div/select'))
            )
            category_dropdown = Select(category_element)
            category_dropdown.select_by_value("Development")
            save_screenshot(driver, "uneed", "product_category")
            logging.info("Success: Added product category")
        except Exception as e:
            logging.error(f"Error: Adding product category - {str(e)}")
        time.sleep(3)

        try:
            tag_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div/div[2]/form/div/div[2]/div[1]/div/div[3]/div[2]/div[2]/div/div/button'))
            )
            tag_dropdown = Select(tag_element)
            tag_dropdown.select_by_visible_text("Education")
            save_screenshot(driver, "uneed", "product_tag")
            logging.info("Success: Added product tag")
        except Exception as e:
            logging.error(f"Error: Adding product tag - {str(e)}")

        time.sleep(3)

        try:
            product_tagline = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div/div[2]/form/div/div[2]/div[1]/div/div[4]/div[2]/div/textarea'))
            )
            product_tagline.clear()
            product_tagline.send_keys("Better for you")
            save_screenshot(driver, "uneed", "product_tagline")
            logging.info("Success: Added product tagline")
        except Exception as e:
            logging.error(f"Error: Adding product tagline - {str(e)}")

        time.sleep(2)

        try:
            description_box = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div/div[2]/form/div/div[2]/div[1]/div/div[5]/div[2]/div/div/div/div[2]/div/p'))
            )
            driver.execute_script("arguments[0].innerText = '';", description_box)
            description_text = "This is the product description."
            driver.execute_script("arguments[0].innerText = arguments[1];", description_box, description_text)
            save_screenshot(driver, "uneed", "product_description")
            logging.info("Success: Added product description")
        except Exception as e:
            logging.error(f"Error: Adding product description - {str(e)}")

        time.sleep(2)

        try:
            submit_product_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div/div[3]/div/div/section/div/div[1]/button[1]'))
            )
            submit_product_btn.click()
            save_screenshot(driver, "uneed", "submit_product_details")
            logging.info("Success: Submitted product details")
        except Exception as e:
            logging.error(f"Error: Submitting product details - {str(e)}")

        logging.info(f"🎉 SUCCESS: Added product to Uneed!")
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to add product to Uneed. Error: {str(e)}")
        save_screenshot(driver, "uneed", "error_add_product")
        return 'fail'
    return 'success'

def main():
    """Automate the Google login process on Uneed"""
    # Load secrets from .env file
    secrets = dotenv_values(".env")
    if not secrets:
        logging.error("❌ ERROR: No secrets found in .env file.")
        return

    # Extract credentials from secrets
    google_email = secrets.get("EMAIL")
    google_password = secrets.get("PASSWORD")
    if not google_email or not google_password:
        logging.error("❌ ERROR: Google email or password not found in .env file.")
        return

    # Initialize automation tracking DataFrame
    current_user = secrets.get("USERNAME", "ShubhamGupta24")
    automation_tracker_df = create_or_load_automation_data()

    # Initialize driver
    driver = setup_driver()
    driver.get("https://www.uneed.best/submit-a-tool")

    try:
        logging.info(f"🌐 Processing website: Uneed")
        result = login_register(driver, google_email, google_password)
        if result == 'success':
            add_result = add_product_handle(driver)
            if add_result == 'success':
                update_automation_status(automation_tracker_df, current_user, "uneed.com", 1)
            else:
                update_automation_status(automation_tracker_df, current_user, "uneed.com", 0, error_message="Failed to add product")
    except Exception as e:
        logging.error(f"❌ ERROR: Automation failed. Error: {str(e)}")
        update_automation_status(automation_tracker_df, current_user, "uneed.com", 0, error_message=str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()