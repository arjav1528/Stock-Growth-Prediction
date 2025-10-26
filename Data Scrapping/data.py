from typing import Any
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import os
import dotenv



dotenv.load_dotenv()

def load_data():
    df = pd.read_csv('stock_list.csv')

    rows = []
    

    for index, row in df.iterrows():
        if row['symbol'] is not None:
            rows.append(row['symbol'])
        elif row['newnsecode'] is not None:
            rows.append(row['newnsecode'])
        elif row['newbsecode'] is not None:
            rows.append(row['newbsecode'])
            


    return rows

class QuarterlyDataExtractor:
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
        
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
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

    def extract_quarterly_data(self, symbol):
        try:
            print(f"Extracting quarterly data for {symbol}...")
            
            
            company_url = f"https://www.screener.in/company/{symbol}/consolidated/"
            
            self.driver.get(company_url)
            time.sleep(3)
            
         
            current_url = self.driver.current_url
            page_title = self.driver.title.lower()
            page_source = self.driver.page_source.lower()
            
           
            error_indicators = [
                "404" in current_url or "404" in page_title,
                "not found" in page_title or "not found" in page_source,
                "page not found" in page_title or "page not found" in page_source,
                "error" in page_title and ("404" in page_title or "not found" in page_title),
                "company not found" in page_source,
                "invalid company" in page_source,
                "no data available" in page_source,
                "data not available" in page_source
            ]
            
            if any(error_indicators):
                print(f"⚠️  Company {symbol} not found or no data available (404/error page)")
                return []
            
           
            if "/company/" not in current_url or symbol not in current_url:
                print(f"⚠️  Company {symbol} redirected to different page: {current_url}")
                return []
            
            try:
              
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#quarters .responsive-holder[data-result-table] table")))
            except:
               
                try:
                    
                    no_data_indicators = [
                        "no quarterly data" in page_source,
                        "quarterly results not available" in page_source,
                        "data not available" in page_source,
                        "coming soon" in page_source
                    ]
                    
                    if any(no_data_indicators):
                        print(f"⚠️  Company {symbol} exists but has no quarterly data available")
                        return []
                    else:
                        print(f"⚠️  Could not find quarterly results table for {symbol} - page may have loaded incorrectly")
                        return []
                except:
                    print(f"⚠️  Could not find quarterly results table for {symbol}")
                    return []
            
           
            table = self.driver.find_element(By.CSS_SELECTOR, "#quarters .responsive-holder[data-result-table] table")
            
            
            headers = []
            header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            
            for cell in header_cells:
                header_text = cell.text.strip()
                if header_text and header_text != "":
                    headers.append(header_text)
            
            if len(headers) < 2:
                print(f"No valid headers found for {symbol}")
                return []
            
            period_headers = headers[1:]
            print(f"Found {len(period_headers)} periods for {symbol}: {period_headers[:3]}...")
            
           
            periods_data = {}
            for period in period_headers:
                periods_data[period] = {
                    'Company Symbol': symbol,
                    'Period': period,
                    'Sales': '',
                    'Expenses': '',
                    'Operating Profit': '',
                    'OPM %': '',
                    'Other Income': '',
                    'Interest': '',
                    'Depreciation': '',
                    'Profit Before Tax': '',
                    'Tax %': '',
                    'Net Profit': '',
                    'EPS in Rs': '',
                    'PDF URL': ''
                }
            
           
            pdf_urls = self.extract_pdf_urls()
            
       
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
                    
                  
                    metric_name = metric_name.replace('+', '').strip()
                    
                   
                    for i, cell in enumerate(cells[1:]):
                        if i < len(period_headers):
                            period = period_headers[i]
                            value = cell.text.strip()
                            
                           
                            if 'sales' in metric_name.lower():
                                periods_data[period]['Sales'] = value
                            elif 'expenses' in metric_name.lower():
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
                                periods_data[period]['Tax %'] = value
                            elif 'net profit' in metric_name.lower():
                                periods_data[period]['Net Profit'] = value
                            elif 'eps' in metric_name.lower():
                                periods_data[period]['EPS in Rs'] = value
                
                except Exception as e:
                    print(f"Error processing row in {symbol}: {e}")
                    continue
            
           
            for period in periods_data:
                if period in pdf_urls:
                    periods_data[period]['PDF URL'] = pdf_urls[period]
            
            all_periods_data = list(periods_data.values())
            print(f"Extracted data for {symbol}: {len(all_periods_data)} periods")
            
            if all_periods_data:
                print(f"Sample periods: {[d['Period'] for d in all_periods_data[:3]]}")
            
            return all_periods_data
            
        except Exception as e:
            print(f"Error extracting quarterly data for {symbol}: {e}")
            return []

    def extract_pdf_urls(self):
        """Extract PDF URLs from the quarterly results table"""
        pdf_urls = {}
        try:
          
            table = self.driver.find_element(By.CSS_SELECTOR, "#quarters .responsive-holder[data-result-table] table")
            
          
            header_row = table.find_element(By.CSS_SELECTOR, "thead tr")
            header_cells = header_row.find_elements(By.TAG_NAME, "th")
            periods = []
            
            for cell in header_cells[1:]: 
                period_text = cell.text.strip()
                if period_text:
                    periods.append(period_text)
            
           
            tbody = table.find_element(By.TAG_NAME, "tbody")
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            
            for row in rows:
                try:
                    first_cell = row.find_element(By.TAG_NAME, "td")
                    if "Raw PDF" in first_cell.text:
                       
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        for i, cell in enumerate[Any](cells[1:], 1):  
                            if i <= len(periods):
                                period = periods[i-1]
                                
                               
                                pdf_links = cell.find_elements(By.CSS_SELECTOR, "a[href*='source/quarter']")
                                if pdf_links:
                                    pdf_url = pdf_links[0].get_attribute('href')
                                    if pdf_url:
                                        pdf_urls[period] = pdf_url
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting PDF URLs: {e}")
        
        return pdf_urls

    def extract_all_companies_data(self, symbols, max_companies=None):
        """Extract quarterly data for all companies"""
        all_quarterly_data = []
        failed_companies = []
        no_data_companies = []
        
        if max_companies:
            symbols = symbols[:max_companies]
        
        total_companies = len(symbols)
        processed_count = 0
        
        print(f"Starting processing of {total_companies} companies")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n--- Processing company {i}/{total_companies}: {symbol} ---")
            
            try:
                company_periods_data = self.extract_quarterly_data(symbol)
                
                if company_periods_data:
                    all_quarterly_data.extend(company_periods_data)
                    processed_count += 1
                    print(f"✓ Successfully extracted data for {symbol} ({len(company_periods_data)} periods)")
                else:
                    no_data_companies.append(symbol)
                    print(f"✗ No data found for {symbol}")
                
              
                if i % 10 == 0:
                    print(f"\n🎯 PROGRESS UPDATE:")
                    print(f"   Processed: {i}/{total_companies} companies ({(i/total_companies)*100:.1f}%)")
                    print(f"   Successful extractions: {processed_count}")
                    print(f"   No data available: {len(no_data_companies)}")
                    print(f"   Failed extractions: {len(failed_companies)}")
                    print(f"   Total data records: {len(all_quarterly_data)}")
                
           
                if i % 50 == 0 and all_quarterly_data:
                    backup_filename = f"quarterly_backup_{i}.csv"
                    try:
                        df_backup = pd.DataFrame(all_quarterly_data)
                        df_backup.to_csv(backup_filename, index=False)
                        print(f"   💾 Backup saved: {backup_filename}")
                    except Exception as backup_error:
                        print(f"   ⚠️ Backup failed: {backup_error}")
                
                time.sleep(2)  
                
            except Exception as e:
                failed_companies.append(symbol)
                print(f"✗ Error processing {symbol}: {e}")
                continue
        
        print(f"\n🎉 Completed! Total companies processed: {processed_count}/{total_companies}")
        print(f"Total data records collected: {len(all_quarterly_data)}")
        print(f"Companies with no data: {len(no_data_companies)}")
        print(f"Companies that failed: {len(failed_companies)}")
        success_rate = (processed_count / total_companies) * 100 if total_companies > 0 else 0
        print(f"Success rate: {success_rate:.1f}%")
        
        
        if no_data_companies:
            try:
                no_data_df = pd.DataFrame({'Symbol': no_data_companies, 'Reason': 'No Data Available'})
                no_data_df.to_csv('companies_no_data.csv', index=False)
                print(f"📝 Saved {len(no_data_companies)} companies with no data to 'companies_no_data.csv'")
            except Exception as e:
                print(f"⚠️ Could not save no-data companies list: {e}")
        
        if failed_companies:
            try:
                failed_df = pd.DataFrame({'Symbol': failed_companies, 'Reason': 'Extraction Failed'})
                failed_df.to_csv('companies_failed.csv', index=False)
                print(f"📝 Saved {len(failed_companies)} failed companies to 'companies_failed.csv'")
            except Exception as e:
                print(f"⚠️ Could not save failed companies list: {e}")
        
        return all_quarterly_data

    def save_quarterly_data_to_csv(self, quarterly_data, filename="quarterly_results.csv"):
        """Save quarterly data to CSV file"""
        try:
            if quarterly_data:
                df = pd.DataFrame(quarterly_data)
                df.to_csv(filename, index=False)
                print(f"Quarterly data saved to {filename}")
                
                print(f"\n📊 FINAL STATISTICS:")
                print(f"Total data records: {len(quarterly_data):,}")
                print(f"Unique companies: {df['Company Symbol'].nunique():,}")
                print(f"Unique periods: {df['Period'].nunique()}")
                
                periods = sorted(df['Period'].unique())
                if len(periods) > 0:
                    print(f"Period range: {periods[0]} to {periods[-1]}")
                
                print(f"\nFile size: {os.path.getsize(filename) / (1024*1024):.1f} MB")
                    
            else:
                print("No quarterly data to save")
                
        except Exception as e:
            print(f"Error saving quarterly data: {e}")

    def close(self):
        """Close the browser"""
        self.driver.quit()

def extract_quarterly_data_for_all_companies(max_companies=None):
    """Main function to extract quarterly data for all companies"""
    EMAIL = os.environ.get("SCREENER_EMAIL")
    PASSWORD = os.environ.get("SCREENER_PASSWORD")

    if not EMAIL or not PASSWORD:
        print("Error: Please set SCREENER_EMAIL and SCREENER_PASSWORD environment variables.")
        return

   
    symbols = load_data()
    print(f"Loaded {len(symbols)} company symbols")
    
    if max_companies:
        symbols = symbols[:max_companies]
        print(f"Processing first {max_companies} companies")

    extractor = QuarterlyDataExtractor()
    
    try:
        print("=== LOGGING IN ===")
        if not extractor.login(EMAIL, PASSWORD):
            print("Login failed. Exiting...")
            return
        
        print("\n=== EXTRACTING QUARTERLY DATA FOR ALL COMPANIES ===")
        quarterly_data = extractor.extract_all_companies_data(symbols)
        
   
        if quarterly_data:
            print("\n=== SAVING DATA ===")
            extractor.save_quarterly_data_to_csv(quarterly_data, "quarterly_results.csv")
            print(f"Successfully processed {len(symbols)} companies!")
            print(f"Total data records extracted: {len(quarterly_data)}")
        else:
            print("No quarterly data extracted")
        
    except KeyboardInterrupt:
        print("\n\n=== PROCESS INTERRUPTED ===")
        print("Saving partial data...")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        extractor.driver.save_screenshot("quarterly_error_screenshot.png")
    
    finally:
        print("\nClosing browser...")
        extractor.close()
        print("Process completed!")

def test_single_company(symbol="GODFRYPHLP"):
    """Test function to extract data for a single company"""
    EMAIL = os.environ.get("SCREENER_EMAIL")
    PASSWORD = os.environ.get("SCREENER_PASSWORD")

    if not EMAIL or not PASSWORD:
        print("Error: Please set SCREENER_EMAIL and SCREENER_PASSWORD environment variables.")
        return

    extractor = QuarterlyDataExtractor()
    
    try:
        print("=== LOGGING IN ===")
        if not extractor.login(EMAIL, PASSWORD):
            print("Login failed. Exiting...")
            return
        
        print(f"\n=== EXTRACTING QUARTERLY DATA FOR {symbol} ===")
        quarterly_data = extractor.extract_quarterly_data(symbol)
        
        if quarterly_data:
            print(f"\n=== EXTRACTED DATA ===")
            for data in quarterly_data[:3]:  
                print(f"Period: {data['Period']}")
                print(f"  Sales: {data['Sales']}")
                print(f"  Expenses: {data['Expenses']}")
                print(f"  Operating Profit: {data['Operating Profit']}")
                print(f"  Net Profit: {data['Net Profit']}")
                print(f"  PDF URL: {data['PDF URL']}")
                print()
            
  
            df = pd.DataFrame(quarterly_data)
            df.to_csv(f"test_{symbol}_quarterly_data.csv", index=False)
            print(f"Data saved to test_{symbol}_quarterly_data.csv")
        else:
            print("No quarterly data extracted")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\nClosing browser...")
        extractor.close()
        print("Test completed!")

if __name__ == "__main__":
    
    extract_quarterly_data_for_all_companies(max_companies=None)


