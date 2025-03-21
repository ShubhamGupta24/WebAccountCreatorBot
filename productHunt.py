from datetime import datetime, timezone
import os
from dotenv import dotenv_values
import pandas as pd
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
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
    filename = 'producthunt_automation_tracker.csv'
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
    """Update the DataFrame with Product Hunt automation attempt"""
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
    df.to_csv('producthunt_automation_tracker.csv', index=False)
    return df

def save_screenshot(driver, website, action_desc):
    """Save a screenshot of the current browser state"""
    website_name = website.split("//")[-1].split("/")[0]
    folder_path = os.path.join("producthunt_screenshots", website_name)
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
PRODUCT_URL = "quantumcomputing.io"
PRODUCT_NAME = "Quanta Course"
PRODUCT_TAGLINE = "Better for you"
PRODUCT_DESCRIPTION = "This is a product description"

def login_register(driver, google_email, google_password):
    """Automate the Google login process on Product Hunt"""
    logging.info("🔵 Step 1: Clicking 'Sign In' button...")
    try:
        # Click the "Sign In" button
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[1]/header/div/div[2]/div'))
        ).click()
        save_screenshot(driver, "producthunt", "click_log_in_button")
        logging.info("Clicked on 'Sign In' button")
        time.sleep(2)  # Wait for the login form to load

        # Store the initial window handle
        initial_window = driver.current_window_handle

        # Click the "Sign in with Google" button
        logging.info("🔵 Step 2: Clicking 'Sign in with Google'...")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[2]/div/div/div/div/div[1]/button'))
        ).click()
        save_screenshot(driver, "producthunt", "click_continue_with_google")
        logging.info("Clicked 'Sign in with Google'")

        # Enter Google email
        logging.info("🔵 Step 3: Entering Google email...")
        email_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//input[@type="email"]'))
        )
        email_field.send_keys(google_email)
        email_field.send_keys(Keys.RETURN)
        save_screenshot(driver, "producthunt", "shared_email_to_website")
        logging.info("Entered Google email")

        # Enter Google password
        logging.info("🔵 Step 4: Entering Google password...")
        password_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password_field.send_keys(google_password)
        password_field.send_keys(Keys.RETURN)
        save_screenshot(driver, "producthunt", "shared_password_to_website")
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

        # Switch back to the original window
        driver.switch_to.window(initial_window)
        logging.info("🎉 SUCCESS: Logged into Product Hunt using Google!")
        return 'success'
    except Exception as e:
        logging.error(f"❌ ERROR: Failed to log in. Error: {str(e)}")
        save_screenshot(driver, "producthunt", "error_during_login")
        return 'fail'


def submit_product_handle(driver, image_path, target_date):
    """Listing a product on Product Hunt."""
    logging.info("Submitting a product")
    try:
        # Click on "Add product"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Submit")]'))
        ).click()
        save_screenshot(driver, "producthunt", "click_add_product")

        # Add product URL
        logging.info("Adding product URL")
        product_url_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="www.producthunt.com"]'))
        )
        product_url_field.clear()
        product_url_field.send_keys(PRODUCT_URL)
        save_screenshot(driver, "producthunt", "add_product_url")

        # Click on "Get started"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Get started")]'))
        ).click()
        save_screenshot(driver, "producthunt", "click_get_started")

          # Add product name
        logging.info("Adding product name")
        product_name_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Simply the name of the product"]'))
        )
        save_screenshot(driver, "producthunt", "add_product_name")
        product_name_field.clear()
        product_name_field.send_keys(PRODUCT_NAME)

        # Add description
        logging.info("Adding description")
        description_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//textarea[@placeholder="Short description of the product"]'))
        )
        save_screenshot(driver, "producthunt", "add_description")
        description_field.clear()
        description_field.send_keys(PRODUCT_DESCRIPTION)

        # Add tagline
        logging.info("Adding tagline")
        tagline_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@placeholder="Concise and descriptive tagline for the product"]'))
        )
        save_screenshot(driver, "producthunt", "add_tagline")
        tagline_field.clear()
        tagline_field.send_keys(PRODUCT_TAGLINE)


        # Click on "Select a launch tag"
        logging.info("Selecting launch tag")
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/div[3]/form/div/div/div[2]/div/div[4]/div[2]/label/div[2]/div[1]/div/div/input'))
        ).click()
        save_screenshot(driver, "producthunt", "click_select_launch_tag")
        time.sleep(4)

        # Click on "View all launch tags"
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "View all launch tags")]'))
        ).click()
        save_screenshot(driver, "producthunt", "click_view_all_launch_tags")
        time.sleep(4)

        # Function to scroll the specific container and load more tags
        def scroll_to_load_more_tags():
            try:
                # Locate the scrollable container
                container = driver.find_element(By.CLASS_NAME, "styles_topicsContainer__dxLE0.mt-6")

                # Get the initial scroll height of the container
                last_height = driver.execute_script("return arguments[0].scrollHeight", container)

                while True:
                    # Scroll to the bottom of the container
                    driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", container)
                    time.sleep(2)  # Wait for new tags to load

                    # Calculate new scroll height and compare with last scroll height
                    new_height = driver.execute_script("return arguments[0].scrollHeight", container)
                    if new_height == last_height:
                        break  # No more new tags loaded
                    last_height = new_height

            except NoSuchElementException:
                logging.error("❌ ERROR: Scrollable container not found.")
                raise

        # Function to find the "Tech" tag
        def find_tech_tag():
            tags = driver.find_elements(By.CLASS_NAME, "styles_item__ldx07")
            for tag in tags:
                try:
                    # Locate nested elements
                    div2 = tag.find_element(By.CLASS_NAME, "flex.flex-row.items-center.justify-between.py-5")
                    div3 = div2.find_element(By.CLASS_NAME, "flex.flex-row.items-center.gap-2")
                    button = div3.find_element(By.CLASS_NAME, "styles_iconButton__WlBnX")
                    div4 = button.find_element(By.CLASS_NAME, "text-16.font-semibold.text-dark-gray")

                    # Check if the text inside div4 is 'Tech'
                    if div4.text.strip() == "Tech":
                        div4.click()  # Click the 'Tech' tag
                        logging.info("Clicked on 'Tech' tag")
                        return True
                except NoSuchElementException:
                    continue  # Skip if any nested element is not found
            return False

        # Search for the "Tech" tag with dynamic loading
        tag_found = False
        max_attempts = 5  # Maximum number of scroll attempts
        attempt = 0

        while not tag_found and attempt < max_attempts:
            # Try to find the "Tech" tag in the current list of tags
            tag_found = find_tech_tag()
            if tag_found:
                break

            # If not found, scroll to load more tags
            logging.info(f"🔍 'Tech' tag not found. Scrolling to load more tags (Attempt {attempt + 1}/{max_attempts})...")
            scroll_to_load_more_tags()  # Scroll the specific container
            attempt += 1

        if not tag_found:
            logging.error("❌ ERROR: 'Tech' tag not found after scrolling.")
            return 'fail'

        # Save the selected tag
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Save launch tags")]'))
        ).click()
        save_screenshot(driver, "producthunt", "save_launch_tags")


        # Switch to image upload
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Next step: Images and media")]'))
        ).click()
        save_screenshot(driver, "producthunt", "click_next_step_images")
        time.sleep(2)

        # Add image
        logging.info("Adding image")
        browse_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Browse for files")]'))
        )

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", browse_button)
        time.sleep(1)  # Wait for the scroll to complete

        # Use JavaScript to click the element
        driver.execute_script("arguments[0].click();", browse_button)
        save_screenshot(driver, "producthunt", "click_browse_for_files")
        time.sleep(2)

        # Use pyautogui to upload the image
        pyautogui.write(image_path)
        pyautogui.press('enter')
        time.sleep(4)

        # Go to launch checklist
        logging.info("Going to launch checklist")
        launch_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Launch checklist")]'))
        )

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", launch_button)
        time.sleep(1)  # Wait for the scroll to complete

        # Use JavaScript to click the element
        driver.execute_script("arguments[0].click();", launch_button)
        save_screenshot(driver, "producthunt", "click_launch_checklist")
        time.sleep(2)

        # Schedule launch
        logging.info("Scheduling launch")
        schedule_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//*[contains(text(), "Schedule launch for later")]'))
        )

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", schedule_button)
        time.sleep(1)  # Wait for the scroll to complete

        # Use JavaScript to click the element
        driver.execute_script("arguments[0].click();", schedule_button)
        save_screenshot(driver, "producthunt", "click_schedule_launch")
        time.sleep(2)

        # Wait for all available schedule dates to load
        available_dates_elements = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@data-test, 'schedule-date-')]"))
        )
        time.sleep(2)

        # Extract and convert available dates
        available_dates = []
        for element in available_dates_elements:
            date_str = element.get_attribute("data-test").replace("schedule-date-", "")
            available_dates.append(datetime.strptime(date_str, "%Y-%m-%d"))

        # Sort available dates
        available_dates.sort()
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        closest_date = min(available_dates, key=lambda d: abs(d - target_datetime))
        closest_date_str = closest_date.strftime("%Y-%m-%d")

        # Click on the closest available date
        schedule_xpath = f"//div[@data-test='schedule-date-{closest_date_str}']"
        date_element = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, schedule_xpath))
        )
        date_element.click()

        # Submit product
        logging.info("SConfirming launch schedule")
        confirm_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Confirm scheduled date")]'))
        )

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", confirm_button)
        time.sleep(1)  # Wait for the scroll to complete

        # Use JavaScript to click the element
        driver.execute_script("arguments[0].click();", confirm_button)
        logging.info("🎉 SUCCESS: Added product to Product Hunt!")
        return 'success'

    except Exception as e:
        logging.error(f"❌ ERROR: Failed to add product to Product Hunt. Error: {str(e)}")
        return 'fail'

    
def main():
    """Automate the Google login process on Product Hunt"""
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
    driver.get("https://www.producthunt.com")

    try:      
        try:
            logging.info(f"🌐 Processing website: Product Hunt")
            result = login_register(driver, google_email, google_password)
            if result == 'success':
                add_result = submit_product_handle(driver, secrets.get("IMAGE_PATH"), "2025-03-22")
                if add_result == 'success':
                    update_automation_status(automation_tracker_df, current_user, "producthunt.com", 1)
                
        except Exception as e:
            logging.error(f"❌ ERROR: Google Signup/Login failed : {str(e)}")
            logging.error("Stacktrace:", exc_info=True)
            update_automation_status(automation_tracker_df, current_user, "", 0, error_message=str(e))
    finally:
        driver.quit()

if __name__ == "__main__":
    main()