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
    
    def get_company_links_from_page(self):
        try:
            company_links = []
            
            company_containers = self.driver.find_elements(By.CSS_SELECTOR, ".flex-row.flex-space-between.flex-align-center")
            
            print(f"Found {len(company_containers)} company containers")
            
            for container in company_containers:
                try:
                    company_link = container.find_element(By.CSS_SELECTOR, "a[href*='/company/']")
                    
                    href = company_link.get_attribute('href')
                    company_name = company_link.find_element(By.CSS_SELECTOR, ".hover-link.ink-900").text.strip()
                    
                    if (href and '/company/' in href and company_name and 
                        company_name.upper() != 'PDF' and 
                        '/source/quarter/' not in href and
                        company_name != ''):
                        
                        url_parts = href.split('/company/')[1].split('/')
                        if len(url_parts) >= 2 and url_parts[0] == 'id':
                            symbol = f"id/{url_parts[1]}"
                        else:
                            symbol = url_parts[0]
                        
                        if symbol != 'source' and not href.endswith('/source/quarter/'):
                            company_data = {
                                'name': company_name,
                                'url': href,
                                'symbol': symbol
                            }
                            company_links.append(company_data)
                            
                            print(f"  -> {company_name} ({symbol})")
                            
                except Exception as e:
                    continue
            
            print(f"Extracted {len(company_links)} company links from current page")
            return company_links
            
        except Exception as e:
            print(f"Error getting company links: {e}")
            return []
    
    def get_total_pages(self):
        try:
            pagination_selectors = [
                ".paginator a",
                "p.paginator a",
                ".end"
            ]
            
            max_page = 1
            
            try:
                end_link = self.driver.find_element(By.CSS_SELECTOR, "a.end")
                href = end_link.get_attribute('href')
                if href and 'p=' in href:
                    page_num = int(href.split('p=')[1].split('&')[0])
                    max_page = page_num
                    print(f"Found end link with page: {max_page}")
                    return max_page
            except:
                pass
            
            for selector in pagination_selectors:
                try:
                    page_links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in page_links:
                        href = link.get_attribute('href')
                        if href and 'p=' in href:
                            try:
                                page_num = int(href.split('p=')[1].split('&')[0])
                                max_page = max(max_page, page_num)
                            except:
                                pass
                        
                        text = link.text.strip()
                        if text.isdigit():
                            max_page = max(max_page, int(text))
                    
                    if max_page > 1:
                        break
                except:
                    continue
            
            try:
                results_text = self.driver.find_element(By.CSS_SELECTOR, ".paginator").text
                if "results" in results_text.lower():
                    import re
                    numbers = re.findall(r'\d+', results_text)
                    if numbers:
                        total_results = int(numbers[-1])
                        estimated_pages = (total_results + 24) // 25
                        max_page = max(max_page, estimated_pages)
                        print(f"Found {total_results} total results, estimated {estimated_pages} pages")
            except:
                pass
            
            print(f"Detected maximum page: {max_page}")
            return max_page
            
        except Exception as e:
            print(f"Error getting total pages: {e}")
            return 1
    
    def navigate_to_page(self, page_num):
        try:
            current_url = self.driver.current_url
            
            if '?p=' in current_url:
                base_url = current_url.split('?p=')[0]
            elif '&p=' in current_url:
                base_url = current_url.split('&p=')[0]
            else:
                base_url = current_url
            
            if '?' in base_url:
                new_url = f"{base_url}&p={page_num}"
            else:
                new_url = f"{base_url}?p={page_num}"
            
            print(f"Navigating to page {page_num}: {new_url}")
            self.driver.get(new_url)
            time.sleep(3)
            
            try:
                current_page_element = self.driver.find_element(By.CSS_SELECTOR, ".this-page")
                current_page = int(current_page_element.text.strip())
                if current_page == page_num:
                    print(f"Successfully navigated to page {page_num}")
                    return True
                else:
                    print(f"Page mismatch: expected {page_num}, got {current_page}")
                    return False
            except:
                print(f"Could not verify page number, assuming navigation successful")
                return True
            
        except Exception as e:
            print(f"Error navigating to page {page_num}: {e}")
            return False
    
    def get_all_company_links(self):
        try:
            all_companies = []
            
            print("Getting company links from all pages...")
            
            total_pages = self.get_total_pages()
            print(f"Total pages to scrape: {total_pages}")
            
            for page_num in range(1, total_pages + 1):
                print(f"\n--- Scraping page {page_num}/{total_pages} ---")
                
                if page_num > 1:
                    if not self.navigate_to_page(page_num):
                        print(f"Failed to navigate to page {page_num}, skipping...")
                        continue
                
                time.sleep(2)
                
                print(f"Companies found on page {page_num}:")
                page_companies = self.get_company_links_from_page()
                
                if page_companies:
                    all_companies.extend(page_companies)
                    print(f"✓ Page {page_num} complete. Total companies collected so far: {len(all_companies)}")
                else:
                    print(f"✗ No companies found on page {page_num}")
                
                time.sleep(1)
            
            print(f"\n🎉 Completed! Total companies collected: {len(all_companies)}")
            return all_companies
            
        except Exception as e:
            print(f"Error getting all company links: {e}")
            return []
    
    def save_companies_to_csv(self, companies, filename="companies_list.csv"):
        try:
            if companies:
                df = pd.DataFrame(companies)
                df.to_csv(filename, index=False)
                print(f"Companies saved to {filename}")
                
                print(f"Total companies: {len(companies)}")
                print("\nFirst few companies:")
                for i, company in enumerate(companies[:5]):
                    print(f"{i+1}. {company['name']} - {company['symbol']}")
                    
            else:
                print("No companies to save")
                
        except Exception as e:
            print(f"Error saving companies: {e}")

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
            print("Already logged in! Proceeding to get company list...")
            login_successful = True
        else:
            print("Not logged in. Going to login page...")
            scraper.driver.get("https://www.screener.in/login/?next=/results/latest/")
            time.sleep(3)
            scraper.debug_login_page()
            
            print("\n=== ATTEMPTING LOGIN ===")
            login_successful = scraper.login(EMAIL, PASSWORD)
        
        if login_successful:
            print("Ready to get company list...")
            
            current_url = scraper.driver.current_url
            if "/results/latest/" not in current_url:
                print("Navigating to results page...")
                scraper.driver.get("https://www.screener.in/results/latest/")
                time.sleep(3)
            
            companies = scraper.get_all_company_links()
            
            if companies:
                scraper.save_companies_to_csv(companies)
                print(f"\nSuccessfully collected {len(companies)} companies!")
            else:
                print("No companies found. Taking screenshot for debugging...")
                scraper.driver.save_screenshot("no_companies_found.png")
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