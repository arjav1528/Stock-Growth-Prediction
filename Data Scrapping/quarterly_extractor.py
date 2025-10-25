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

class QuarterlyExtractor:
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
            self.driver.get("https://www.screener.in/login/")
            
            time.sleep(3)
            
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
            
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[type='submit']"))
            )
            login_button.click()
            print("Login button clicked")
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            print(f"After login attempt - Current URL: {current_url}")
            
            if "login" not in current_url.lower():
                print("Login successful!")
                return True
            else:
                print("Login might have failed")
                return False
            
        except Exception as e:
            print(f"Login failed with exception: {str(e)}")
            return False

    def extract_quarterly_data(self, company_url, company_name):
        try:
            print(f"Extracting quarterly data for {company_name}...")
            
            self.driver.get(company_url)
            time.sleep(3)
            
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#quarters table")))
            except:
                print(f"Could not find quarterly results table for {company_name}")
                return []
            
            table = self.driver.find_element(By.CSS_SELECTOR, "#quarters .responsive-holder table")
            
            headers = []
            header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            
            for cell in header_cells:
                header_text = cell.text.strip()
                if header_text and header_text != "":
                    headers.append(header_text)
            
            if len(headers) < 2:
                print(f"No valid headers found for {company_name}")
                return []
            
            period_headers = headers[1:]
            print(f"Found {len(period_headers)} periods for {company_name}: {period_headers[:3]}...")
            
            periods_data = {}
            for period in period_headers:
                periods_data[period] = {
                    'Company Name': company_name,
                    'Period': period,
                    'Expenses': '',
                    'Operating Profit': '',
                    'OPM %': '',
                    'Other Income': '',
                    'Interest': '',
                    'Depreciation': '',
                    'Profit Before Tax': '',
                    'Tax%': '',
                    'Net Profit': '',
                    'EPS in Rs': ''
                }
            
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            for row in rows:
                try:
                    row_html = row.get_attribute('innerHTML')
                    if ('Raw PDF' in row.text or 
                        'icon-file-pdf' in row_html or
                        'pdf' in row.text.lower()):
                        continue
                    
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 2:
                        continue
                    
                    metric_cell = cells[0]
                    metric_name = metric_cell.text.strip()
                    
                    if not metric_name or len(metric_name) < 2:
                        continue
                    
                    if '+' in metric_name:
                        metric_name = metric_name.replace('+', '').strip()
                    if '-' in metric_name:
                        metric_name = metric_name.replace('-', '').strip()
                    
                    for i, cell in enumerate(cells[1:]):
                        if i < len(period_headers):
                            period = period_headers[i]
                            value = cell.text.strip()
                            
                            if 'expenses' in metric_name.lower():
                                periods_data[period]['Expenses'] = value
                            elif 'operating profit' in metric_name.lower() and 'opm' not in metric_name.lower():
                                periods_data[period]['Operating Profit'] = value
                            elif 'opm' in metric_name.lower() or ('operating' in metric_name.lower() and '%' in metric_name):
                                periods_data[period]['OPM %'] = value
                            elif 'other income' in metric_name.lower():
                                periods_data[period]['Other Income'] = value
                            elif 'interest' in metric_name.lower() and 'other' not in metric_name.lower():
                                periods_data[period]['Interest'] = value
                            elif 'depreciation' in metric_name.lower() or 'depriciation' in metric_name.lower():
                                periods_data[period]['Depreciation'] = value
                            elif 'profit before tax' in metric_name.lower() or 'pbt' in metric_name.lower():
                                periods_data[period]['Profit Before Tax'] = value
                            elif 'tax' in metric_name.lower() and '%' in metric_name:
                                periods_data[period]['Tax%'] = value
                            elif 'net profit' in metric_name.lower():
                                periods_data[period]['Net Profit'] = value
                            elif 'eps' in metric_name.lower():
                                periods_data[period]['EPS in Rs'] = value
                
                except Exception as e:
                    print(f"Error processing row in {company_name}: {e}")
                    continue
            
            all_periods_data = list(periods_data.values())
            print(f"Extracted data for {company_name}: {len(all_periods_data)} periods")
            
            if all_periods_data:
                print(f"Sample periods: {[d['Period'] for d in all_periods_data[:3]]}")
            
            return all_periods_data
            
        except Exception as e:
            print(f"Error extracting quarterly data for {company_name}: {e}")
            return []

    def load_companies_from_csv(self, csv_file="companies_list.csv"):
        try:
            df = pd.read_csv(csv_file)
            companies = []
            for _, row in df.iterrows():
                companies.append({
                    'name': row['name'],
                    'url': row['url'],
                    'symbol': row['symbol']
                })
            print(f"Loaded {len(companies)} companies from {csv_file}")
            return companies
        except Exception as e:
            print(f"Error loading companies from CSV: {e}")
            return []

    def extract_all_quarterly_data(self, companies, start_from=0, max_companies=None):
        all_quarterly_data = []
        
        if max_companies:
            companies = companies[start_from:start_from + max_companies]
        else:
            companies = companies[start_from:]
        
        total_companies = len(companies)
        processed_count = 0
        
        print(f"Starting processing from company #{start_from + 1}")
        print(f"Total companies to process: {total_companies}")
        
        for i, company in enumerate(companies, 1):
            current_company_number = start_from + i
            print(f"\n--- Processing company {i}/{total_companies} (#{current_company_number}): {company['name']} ---")
            
            try:
                company_periods_data = self.extract_quarterly_data(company['url'], company['name'])
                
                if company_periods_data:
                    all_quarterly_data.extend(company_periods_data)
                    processed_count += 1
                    print(f"✓ Successfully extracted data for {company['name']} ({len(company_periods_data)} periods)")
                else:
                    print(f"✗ No data found for {company['name']}")
                
                if i % 50 == 0:
                    print(f"\n🎯 PROGRESS UPDATE:")
                    print(f"   Processed: {i}/{total_companies} companies ({(i/total_companies)*100:.1f}%)")
                    print(f"   Successful extractions: {processed_count}")
                    print(f"   Total data records: {len(all_quarterly_data)}")
                    print(f"   Average records per company: {len(all_quarterly_data)/processed_count if processed_count > 0 else 0:.1f}")
                
                if i % 100 == 0 and all_quarterly_data:
                    backup_filename = f"quarterly_backup_{current_company_number}.csv"
                    try:
                        df_backup = pd.DataFrame(all_quarterly_data)
                        df_backup.to_csv(backup_filename, index=False)
                        print(f"   💾 Backup saved: {backup_filename}")
                    except Exception as backup_error:
                        print(f"   ⚠️ Backup failed: {backup_error}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"✗ Error processing {company['name']}: {e}")
                continue
        
        print(f"\n🎉 Completed! Total companies processed: {processed_count}/{total_companies}")
        print(f"Total data records collected: {len(all_quarterly_data)}")
        success_rate = (processed_count / total_companies) * 100 if total_companies > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        return all_quarterly_data

    def save_quarterly_data_to_csv(self, quarterly_data, filename="quarterly_results_full.csv"):
        try:
            if quarterly_data:
                df = pd.DataFrame(quarterly_data)
                df.to_csv(filename, index=False)
                print(f"Quarterly data saved to {filename}")
                
                print(f"\n📊 FINAL STATISTICS:")
                print(f"Total data records: {len(quarterly_data):,}")
                print(f"Unique companies: {df['Company Name'].nunique():,}")
                print(f"Unique metrics: {df['Metric'].nunique()}")
                print(f"Unique periods: {df['Period'].nunique()}")
                
                periods = sorted(df['Period'].unique())
                if len(periods) > 0:
                    print(f"Period range: {periods[0]} to {periods[-1]}")
                
                print(f"\nTop 10 most common metrics:")
                top_metrics = df['Metric'].value_counts().head(10)
                for metric, count in top_metrics.items():
                    print(f"  {metric}: {count:,} records")
                
                print(f"\nFile size: {os.path.getsize(filename) / (1024*1024):.1f} MB")
                    
            else:
                print("No quarterly data to save")
                
        except Exception as e:
            print(f"Error saving quarterly data: {e}")

    def close(self):
        self.driver.quit()

def main():
    EMAIL = os.environ.get("SCREENER_EMAIL")
    PASSWORD = os.environ.get("SCREENER_PASSWORD")

    if not EMAIL or not PASSWORD:
        print("Error: Please set SCREENER_EMAIL and SCREENER_PASSWORD environment variables.")
        return

    extractor = QuarterlyExtractor()
    
    try:
        print("=== LOGGING IN ===")
        if not extractor.login(EMAIL, PASSWORD):
            print("Login failed. Exiting...")
            return
        
        print("\n=== LOADING COMPANIES ===")
        companies = extractor.load_companies_from_csv("companies_list.csv")
        
        if not companies:
            print("No companies found in CSV file")
            return
        
        print(f"Total companies to process: {len(companies)}")
        
        print("\n=== EXTRACTING QUARTERLY DATA FOR ALL COMPANIES ===")
        print("This will process all 4490+ companies. This may take several hours.")
        print("The script will save progress periodically.")
        
        # Process all companies (removed max_companies limit)
        quarterly_data = extractor.extract_all_quarterly_data(
            companies, 
            start_from=0      # Start from first company
            # max_companies parameter removed - will process all companies
        )
        
        # Save to CSV
        if quarterly_data:
            print("\n=== SAVING DATA ===")
            extractor.save_quarterly_data_to_csv(quarterly_data, "quarterly_results_full.csv")
            print(f"Successfully processed all {len(companies)} companies!")
            print(f"Total data records extracted: {len(quarterly_data)}")
        else:
            print("No quarterly data extracted")
        
    except KeyboardInterrupt:
        print("\n\n=== PROCESS INTERRUPTED ===")
        print("Saving partial data...")
        # You can add logic here to save partial data if needed
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        extractor.driver.save_screenshot("quarterly_error_screenshot.png")
    
    finally:
        print("\nClosing browser...")
        extractor.close()
        print("Process completed!")

if __name__ == "__main__":
    main()
