from datetime import datetime, timezone
import os
from dotenv import dotenv_values
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import logging
import pyautogui

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_or_load_automation_data():
    """Create or load the automation tracking DataFrame"""
    filename = 'devhunt_automation_tracker.csv'
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
    """Update the DataFrame with devhunt automation attempt"""
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
    df.to_csv('devhunt_automation_tracker.csv', index=False)
    return df

def save_screenshot(driver, website, action_desc):
    """Save a screenshot of the current browser state"""
    website_name = website.split("//")[-1].split("/")[0]
    folder_path = os.path.join("devhunt_screenshots", website_name)
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

# Constants
PRODUCT_URL = "https://quantumcomputing.io"
PROJECT_NAME = "Quantum Computing Project"
PROJECT_slogan = "Revolutionizing Quantum Computing"
PROJECT_DESCRIPTION = "This is a project description for a quantum computing project."

def login_register(driver, google_email, google_password,social_link):
    """Automate the login process on devhunt"""
    logging.info("🔵 Step 1: Clicking 'Log In' button...")
    try:
        # Click the login button
        logging.info("🔵 Step 1: Clicking 'Log In' button...")
        login_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Sign In')]"))
        )
        login_button.click()
        save_screenshot(driver, "devhunt", "clicked_login_button")
        logging.info("Clicked 'Log In' button")
    

       # Store the initial window handle
        initial_window = driver.current_window_handle

        # Click the "Log in with Google" button
        logging.info("🔵 Step 2: Clicking 'Log in with Google'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Continue with Google")]'))
        ).click()
        save_screenshot(driver, "devhunt", "click_continue_with_google")
        logging.info("Clicked 'Log in with Google'")

        # Enter Google email
        logging.info("🔵 Step 3: Entering Google email...")
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="email"]'))
        )
        email_field.send_keys(google_email)
        email_field.send_keys(Keys.RETURN)
        save_screenshot(driver, "devhunt", "shared_email_to_website")
        logging.info("Entered Google email")

       # Enter Google password
        logging.info("🔵 Step 4: Entering Google password...")
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password_field.send_keys(google_password)
        password_field.send_keys(Keys.RETURN)
        save_screenshot(driver, "devhunt", "shared_password_to_website")
        logging.info("Entered Google password")

        # Handle the "Continue" button (if it appears)
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Continue')]"))
            ).click()
            logging.info("Clicked 'Continue' button")
            time.sleep(2)
        except TimeoutException:
            logging.info("No 'Continue' button found")

        time.sleep(5)
        try : 
            logging.info("🔵 Step 5: Entering social link...")
            social_link_field = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Twitter/Linkedin/Facebook or Any other social media']")))
            social_link_field.click()
            social_link_field.send_keys(social_link)
            social_link_field.send_keys(Keys.RETURN)

        
            logging.info("🔵 Step 6: Clicking 'Save' button...")
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Save')]"))
            ).click()
            logging.info("Clicked 'Save' button")
            save_screenshot(driver, "devhunt", "clicked_save_button")
            time.sleep(2)
        except TimeoutException:
            logging.info("No 'Save' button found")
        

        # Switch back to the original window
        driver.switch_to.window(initial_window)
        logging.info("🎉 SUCCESS: Logged into Product Hunt using Google!")
        return 'success'
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to log in. Error: {str(e)}")
        save_screenshot(driver, "devhunt", "error_during_login")
        

def submit_project(driver, image_paths):
    """Submit a project on devhunt"""
    logging.info("Submitting a project")
    
    # Step 1: Click Submit button
    try:
        logging.info("🔵 Step 1: Clicking 'Submit' button...")
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Submit your Dev Tool')]"))
        )
        submit_button.click()
        save_screenshot(driver, "devhunt", "clicked_submit_button")
        time.sleep(2)
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to click 'Submit' button. Error: {str(e)}")
        save_screenshot(driver, "devhunt", "error_during_submit_button")

    # Step 2: Click New Tool button
    try:
        logging.info("🔵 Step 2: Clicking 'New tool' button...")
        new_tool_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'New tool')]"))
        )
        new_tool_button.click()
        save_screenshot(driver, "devhunt", "clicked_new_tool_button")
        time.sleep(2)
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to click 'New tool' button. Error: {str(e)}")
        save_screenshot(driver, "devhunt", "error_during_new_tool_button")

    # Step 3: Upload main image
    try:
        logging.info("Adding main image")
        browse_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Select an image")]'))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", browse_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", browse_button)
        save_screenshot(driver, "devHunt", "click_browse_for_files")
        time.sleep(2)
    
        pyautogui.write(image_paths[0])
        pyautogui.press('enter')
        time.sleep(4)
        save_screenshot(driver, "devHunt", "uploaded_image")
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to add main image. Error: {str(e)}")
        save_screenshot(driver, "devHunt", "error_during_image_upload")

    # Step 4: Fill basic info
    try:
        logging.info("Adding project name")
        project_name_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="My Awesome Dev Tool"]'))
        )
        project_name_field.send_keys(PROJECT_NAME)
        save_screenshot(driver, "devhunt", "added_project_name")
        
        logging.info("Adding slogan")
        slogan_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Supercharge Your Development Workflow!"]'))
        )
        slogan_field.send_keys(PROJECT_slogan)
        save_screenshot(driver, "devhunt", "added_slogan")
        
        logging.info("Adding product URL")
        product_url_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="https://myawesomedevtool.com/"]'))
        )
        product_url_field.clear()
        product_url_field.send_keys(PRODUCT_URL)
        save_screenshot(driver, "devHunt", "add_product_url")
        
        logging.info("Adding description")
        description_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//textarea[@placeholder='Briefly explain what your tool does. HTML is supported']"))
        )
        description_field.send_keys(PROJECT_DESCRIPTION)
        save_screenshot(driver, "devhunt", "added_description")
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to add basic info. Error: {str(e)}")
        save_screenshot(driver, "devhunt", "error_during_basic_info")

    # Step 5: Price selection (improved version)
    try:
        logging.info("Selecting pricing option")
            # Approach 1: Click via JavaScript
        radio_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='radio' and contains(@value,'free')]"))
            )
        driver.execute_script("arguments[0].click();", radio_button)
        save_screenshot(driver, "devHunt", "selected_pricing_option")
        logging.info("Clicked radio button via JavaScript")
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to select pricing option. Error: {str(e)}")
        save_screenshot(driver, "devHunt", "error_during_price_selection")

    # Step 6: Additional images (improved version)
    try:
        if len(image_paths) > 1:
            logging.info("Adding additional images")
            file_input_xpath = '//input[@id="image-upload" and @type="file" and @accept="image/*"]'
            
            for i, image_path in enumerate(image_paths[1:], start=2):
                try:
                    file_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, file_input_xpath)))
                    
                    # Make sure input is interactable
                    driver.execute_script("arguments[0].style.display = 'block';", file_input)
                    driver.execute_script("arguments[0].style.visibility = 'visible';", file_input)
                    file_input.send_keys(image_path.strip())
                    
                    # Wait for upload indicator
                    WebDriverWait(driver, 10).until(
                        lambda d: any(indicator in d.page_source 
                                    for indicator in ["upload-complete", "preview", "thumbnail"])
                    )
                    save_screenshot(driver, "devHunt", f"uploaded_image_{i}")
                    time.sleep(1)
                except Exception as e:
                    logging.error(f"❌ WARNING: Failed to upload image {i}. Error: {str(e)}")
                    save_screenshot(driver, "devHunt", f"warning_uploading_image_{i}")
                    continue
    except Exception as e:
        logging.error(f"❌ ERROR: Failed in additional images upload. Error: {str(e)}")
        save_screenshot(driver, "devHunt", "error_during_additional_uploads")
    # Add Smart Launch Week Selection
    try:
        logging.info("Selecting nearest available free launch week")
        
        # Wait for the launch week dropdown using the confirmed name attribute
        dropdown = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//select[@name='week']"))
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown)
        time.sleep(1)
        
        # Get all available options
        select = Select(dropdown)
        options = select.options
        
        # Find the nearest free launch week
        selected_option = None
        current_date = datetime.now()
        min_date_diff = float('inf')
        
        for option in options:
            option_text = option.text.strip()
            if "Free" in option_text:
                try:
                    # Extract date from option text (format: "March 25, 2025 - April 1, 2025")
                    date_part = option_text.split(' - ')[0]
                    option_date = datetime.strptime(date_part, "%B %d, %Y")
                    
                    # Only consider future dates
                    if option_date >= current_date:
                        date_diff = (option_date - current_date).days
                        
                        # Select the nearest upcoming date
                        if date_diff < min_date_diff:
                            min_date_diff = date_diff
                            selected_option = option
                except Exception as e:
                    logging.warning(f"Couldn't parse date from option: {option_text}. Error: {str(e)}")
                    continue
        
        if selected_option:
            # Select the found option by value
            select.select_by_value(selected_option.get_attribute("value"))
            logging.info(f"Selected launch week: {selected_option.text}")
            save_screenshot(driver, "devHunt", "selected_free_launch_week")
            time.sleep(2)  # Wait for selection to register
        else:
            raise Exception("No upcoming free launch week options available")
            
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to select launch week. Error: {str(e)}")
        save_screenshot(driver, "devHunt", "error_during_launch_week_selection")
        return 'fail'
    
    # Step 7: Submit the project
    try:
        logging.info("Submitting the project")
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        submit_button.click()
        save_screenshot(driver, "devHunt", "clicked_submit_project")
        time.sleep(10)
        logging.info("Project submitted successfully")
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to submit the project. Error: {str(e)}")
    
    return 'success'


def main():
    """Automate the login and project submission process on devhunt"""
    # Load secrets from .env file
    secrets = dotenv_values(".env")
    if not secrets:
        logging.error("❌ ERROR: No secrets found in .env file.")
        return

    # Extract credentials from secrets
    email = secrets.get("EMAIL")
    password = secrets.get("PASSWORD")
    image_paths = secrets.get("IMAGE_PATH", "").strip().split(",")  # Split into a list
    social_link = secrets.get("SOCIAL_LINK")
    if not email or not password or not image_paths:
        logging.error("❌ ERROR: Email, password, or image path not found in .env file.")
        return

    # Initialize automation tracking DataFrame
    current_user = secrets.get("USERNAME", "ShubhamGupta24")
    automation_tracker_df = create_or_load_automation_data()

    # Initialize driver
    driver = setup_driver()
    # Navigate to devhunt
    driver.get("https://devhunt.org/")

    try:
        logging.info(f"🌐 Processing website: devhunt")
        result = login_register(driver, email, password, social_link)
        if result == 'success':
            submit_result = submit_project(driver, image_paths)  # Pass the list of image paths
            if submit_result == 'success':
                update_automation_status(automation_tracker_df, current_user, "devhunt.com", 1)
            else:
                update_automation_status(automation_tracker_df, current_user, "devhunt.com", 0, error_message="Failed to submit project")
        else:
            update_automation_status(automation_tracker_df, current_user, "devhunt.com", 0, error_message="Failed to log in")
    except Exception as e:
        logging.error(f"❌ ERROR: An error occurred: {str(e)}")
        logging.error("Stacktrace:", exc_info=True)
        update_automation_status(automation_tracker_df, current_user, "devhunt.com", 0, error_message=str(e))
    finally:
        driver.quit()


if __name__ == "__main__":
    main()