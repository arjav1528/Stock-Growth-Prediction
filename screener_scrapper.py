from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import pandas as pd
import dotenv
import os
dotenv.load_dotenv()

class ScreenerScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        })
        
        self.wait = WebDriverWait(self.driver, 15)
        
    def login(self, email, password):
        try:
            print("Visiting home page to establish session...")
            self.driver.get("https://www.screener.in/")
            time.sleep(2)
            
            print("Navigating to login page...")
            self.driver.get("https://www.screener.in/login/?next=/results/latest/")
            
            time.sleep(3)
            
            print("Page title:", self.driver.title)
            print("Current URL:", self.driver.current_url)
            
            print("Looking for email field...")
            email_field = self.wait.until(
                EC.element_to_be_clickable((By.ID, "id_username"))
            )
            
            email_field.click()
            time.sleep(0.5)
            email_field.clear()
            time.sleep(0.5)
            
            for char in email:
                email_field.send_keys(char)
                time.sleep(0.1)
            
            print("Email entered successfully")
            
            print("Looking for password field...")
            password_field = self.wait.until(
                EC.element_to_be_clickable((By.ID, "id_password"))
            )
            
            password_field.click()
            time.sleep(0.5)
            password_field.clear()
            time.sleep(0.5)
            
            for char in password:
                password_field.send_keys(char)
                time.sleep(0.1)
            
            print("Password entered successfully")
            
            time.sleep(1)
            
            print("Looking for login button...")
            
            button_selectors = [
                "input[type='submit']",
                "button[type='submit']", 
                ".button-primary",
                "button",
                "input[value*='Login']",
                "input[value*='login']",
                "button:contains('Login')",
                "[type='submit']"
            ]
            
            login_button = None
            for selector in button_selectors:
                try:
                    login_button = self.wait.until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    print(f"Found login button with selector: {selector}")
                    break
                except:
                    continue
            
            if not login_button:
                print("No login button found, trying to submit form...")
                form = self.driver.find_element(By.TAG_NAME, "form")
                self.driver.execute_script("arguments[0].submit();", form)
                time.sleep(3)
            else:
                print(f"Found login button: {login_button.tag_name} with text: {login_button.get_attribute('value') or login_button.text}")
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                time.sleep(0.5)
                
                login_button.click()
                print("Login button clicked")
            
            time.sleep(3)
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            print(f"After login attempt - Current URL: {current_url}")
            
            error_indicators = [
                "invalid", "incorrect", "error", "wrong", "failed",
                "Invalid credentials", "Login failed"
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for error in error_indicators:
                if error.lower() in page_text:
                    print(f"Found error indicator: {error}")
                    try:
                        error_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                            ".error, .alert, .message, .errorlist, .field-error")
                        for elem in error_elements:
                            if elem.text:
                                print(f"Error message: {elem.text}")
                    except:
                        pass
                    
                    self.driver.save_screenshot("login_error_detailed.png")
                    return False
            
            success_indicators = [
                "/results/latest/" in current_url,
                "/dashboard" in current_url.lower(),
                "logout" in page_text,
                "dashboard" in page_text
            ]
            
            try:
                logout_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                    "form[action*='logout'], a[href*='logout'], .logout")
                if logout_elements:
                    print("Found logout element - Login successful!")
                    success_indicators.append(True)
            except:
                pass
            
            if any(success_indicators):
                print("Login successful!")
                print(f"Current URL: {current_url}")
                return True
            else:
                print("Login status unclear. Taking screenshot for analysis...")
                self.driver.save_screenshot("login_unclear.png")
                
                time.sleep(5)
                
                final_url = self.driver.current_url
                
                try:
                    logout_elements_final = self.driver.find_elements(By.CSS_SELECTOR, 
                        "form[action*='logout'], a[href*='logout'], .logout")
                    if logout_elements_final or "/results/latest/" in final_url or "dashboard" in final_url.lower():
                        print("Login successful after additional wait!")
                        return True
                except:
                    pass
                
                print(f"Login might have failed. Final URL: {final_url}")
                return False
            
        except Exception as e:
            print(f"Login failed with exception: {str(e)}")
            print(f"Current URL: {self.driver.current_url}")
            self.driver.save_screenshot("login_exception.png")
            return False
    
    def scrape_results_page(self, url=None):
        try:
            if url:
                self.driver.get(url)
            
            time.sleep(3)
            
            print(f"Scraping page: {self.driver.current_url}")
            
            table_selectors = [
                "table",
                ".data-table table",
                "#results-table",
                "[data-table]"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if table:
                        print(f"Found table with selector: {selector}")
                        break
                except:
                    continue
            
            if not table:
                print("No table found. Page title:", self.driver.title)
                print("Current URL:", self.driver.current_url)
                possible_containers = self.driver.find_elements(By.CSS_SELECTOR, 
                    ".results, .data, .table-container, .content, main")
                
                if possible_containers:
                    print(f"Found {len(possible_containers)} possible data containers")
                    print("Sample content:", possible_containers[0].text[:200])
                
                return None, None
            
            headers = []
            try:
                header_elements = table.find_elements(By.CSS_SELECTOR, "thead tr th, thead tr td, tr:first-child th, tr:first-child td")
                for header in header_elements:
                    text = header.text.strip()
                    if text:
                        headers.append(text)
            except:
                print("Could not find table headers")
            
            rows_data = []
            try:
                row_selectors = ["tbody tr", "tr"]
                rows = []
                
                for selector in row_selectors:
                    try:
                        rows = table.find_elements(By.CSS_SELECTOR, selector)
                        if rows:
                            if selector == "tr" and headers:
                                rows = rows[1:]
                            break
                    except:
                        continue
                
                for row in rows:
                    row_data = []
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if not cells:
                        cells = row.find_elements(By.TAG_NAME, "th")
                    
                    for cell in cells:
                        text = cell.text.strip()
                        if not text:
                            links = cell.find_elements(By.TAG_NAME, "a")
                            if links:
                                text = links[0].text.strip()
                        row_data.append(text)
                    
                    if row_data and any(cell for cell in row_data):
                        rows_data.append(row_data)
                        
            except Exception as e:
                print(f"Error extracting table rows: {str(e)}")
            
            print(f"Extracted {len(rows_data)} rows with {len(headers)} headers")
            return headers, rows_data
            
        except Exception as e:
            print(f"Error scraping results: {str(e)}")
            self.driver.save_screenshot("scraping_error.png")
            return None, None
    
    def save_to_csv(self, headers, data, filename):
        try:
            if headers and data:
                max_cols = len(headers)
                normalized_data = []
                
                for row in data:
                    if len(row) < max_cols:
                        padded_row = row + [''] * (max_cols - len(row))
                    elif len(row) > max_cols:
                        padded_row = row[:max_cols]
                    else:
                        padded_row = row
                    
                    normalized_data.append(padded_row)
                
                print(f"Normalized data: {len(normalized_data)} rows with {max_cols} columns each")
                
                df = pd.DataFrame(normalized_data, columns=headers)
                df.to_csv(filename, index=False)
                print(f"Data saved to {filename}")
            else:
                print("No data to save")
                
        except Exception as e:
            print(f"Error saving to CSV: {e}")
            try:
                with open(f"raw_{filename}", 'w') as f:
                    f.write(f"Headers: {headers}\n")
                    f.write(f"Data rows: {len(data)}\n")
                    for i, row in enumerate(data):
                        f.write(f"Row {i}: {row}\n")
                print(f"Raw data saved to raw_{filename}")
            except:
                print("Failed to save even raw data")
    
    def check_login_status(self):
        try:
            current_url = self.driver.current_url
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            logout_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "form[action*='logout'], a[href*='logout'], .logout")
            
            if any(page in current_url.lower() for page in ["/login", "/register", "/signup"]):
                print(f"=== LOGIN STATUS CHECK ===")
                print(f"Current URL: {current_url}")
                print(f"On login/register page - NOT LOGGED IN")
                return False
            
            login_indicators = [
                bool(logout_elements),
                "/results/" in current_url and all(x not in current_url.lower() for x in ["/login", "/register"]),
                "/dashboard" in current_url,
                "logout" in page_text and "login" not in page_text
            ]
            
            is_logged_in = any(login_indicators)
            
            print(f"=== LOGIN STATUS CHECK ===")
            print(f"Current URL: {current_url}")
            print(f"Found logout elements: {bool(logout_elements)}")
            print(f"Login status: {'LOGGED IN' if is_logged_in else 'NOT LOGGED IN'}")
            
            return is_logged_in
            
        except Exception as e:
            print(f"Error checking login status: {e}")
            return False

    def debug_login_page(self):
        try:
            print("=== LOGIN PAGE DEBUG INFO ===")
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page Title: {self.driver.title}")
            
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            print(f"Found {len(forms)} forms on the page")
            
            for i, form in enumerate(forms):
                print(f"\nForm {i+1}:")
                print(f"  Action: {form.get_attribute('action')}")
                print(f"  Method: {form.get_attribute('method')}")
                
                inputs = form.find_elements(By.TAG_NAME, "input")
                for input_elem in inputs:
                    input_type = input_elem.get_attribute('type')
                    input_name = input_elem.get_attribute('name')
                    input_id = input_elem.get_attribute('id')
                    print(f"    Input: type='{input_type}', name='{input_name}', id='{input_id}'")
            
            error_selectors = [".error", ".alert", ".message", ".errorlist", ".field-error", "[class*='error']"]
            for selector in error_selectors:
                try:
                    errors = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for error in errors:
                        if error.text.strip():
                            print(f"Found error element: {error.text}")
                except:
                    pass
                    
        except Exception as e:
            print(f"Debug failed: {e}")
    
    def close(self):
        self.driver.quit()

def main():
    EMAIL = os.environ.get("SCREENER_EMAIL")
    PASSWORD = os.environ.get("SCREENER_PASSWORD")

    if not EMAIL or not PASSWORD:
        print("Error: Please set SCREENER_EMAIL and SCREENER_PASSWORD environment variables.")
        return


    
    scraper = ScreenerScraper()
    
    try:
        print("Checking current page status...")
        scraper.driver.get("https://www.screener.in/results/latest/")
        time.sleep(3)
        
        if scraper.check_login_status():
            print("Already logged in! Proceeding to scrape data...")
            login_successful = True
        else:
            print("Not logged in. Going to login page...")
            scraper.driver.get("https://www.screener.in/login/?next=/results/latest/")
            time.sleep(3)
            scraper.debug_login_page()
            
            print("\n=== ATTEMPTING LOGIN ===")
            login_successful = scraper.login(EMAIL, PASSWORD)
        
        if login_successful:
            print("Ready to scrape data...")
            
            current_url = scraper.driver.current_url
            if "/results/latest/" not in current_url:
                print("Navigating to results page...")
                scraper.driver.get("https://www.screener.in/results/latest/")
                time.sleep(3)
            
            headers, data = scraper.scrape_results_page()
            
            if headers and data:
                scraper.save_to_csv(headers, data, "screener_results.csv")
                print(f"Successfully scraped {len(data)} rows of data")
                
                if data:
                    print("\nFirst few rows:")
                    print("Headers:", headers)
                    for i, row in enumerate(data[:3]):
                        print(f"Row {i+1}:", row)
            else:
                print("No data found. The page might not contain a data table.")
                print("Taking screenshot for debugging...")
                scraper.driver.save_screenshot("current_page.png")
        else:
            print("\n=== LOGIN FAILED ===")
            print("Debugging the current page state...")
            scraper.debug_login_page()
            print("\nPlease check the screenshots for more details:")
            print("- login_error_detailed.png (if error found)")
            print("- login_exception.png (if exception occurred)")
            print("- login_unclear.png (if login status unclear)")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        scraper.driver.save_screenshot("error_screenshot.png")
    
    finally:
        input("Press Enter to close the browser...")
        scraper.close()

if __name__ == "__main__":
    main()