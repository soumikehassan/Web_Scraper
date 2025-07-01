"""
Power Grid Scraper - First 11 Columns Version
Extracts only the first 11 columns and saves data as CSV file
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
from datetime import datetime

def scrape_first_11_columns():
    """Scrape first 11 columns and save as CSV"""
    
    # Setup Chrome options
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    # Remove headless for first test to see what's happening
    # options.add_argument("--headless")
    
    driver = None
    all_data = []
    headers = []
    
    try:
        # Initialize driver
        print("Starting browser...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        # Navigate to website
        url = "https://erp.powergrid.gov.bd/w/generations/view_generations_bn"
        print(f"Navigating to: {url}")
        driver.get(url)
        
        # Wait a bit for page to load
        time.sleep(5)
        
        # Check if page loaded successfully
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Look for table
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("✓ Table found!")
        
        # Get table headers (first 11 only)
        try:
            header_row = table.find_element(By.TAG_NAME, "tr")
            
            # Try th elements first
            th_elements = header_row.find_elements(By.TAG_NAME, "th")
            if th_elements:
                headers = [th.text.strip() for th in th_elements[:11]]  # First 11 headers
            else:
                # Try td elements in first row
                td_elements = header_row.find_elements(By.TAG_NAME, "td")
                headers = [td.text.strip() for td in td_elements[:11]]  # First 11 headers
            
            print(f"Headers (first 11): {headers}")
            print(f"Number of columns to extract: {len(headers)}")
            
        except Exception as e:
            print(f"Could not extract headers: {e}")
            # Create default headers if extraction fails
            headers = [f"Column_{i+1}" for i in range(11)]
        
        page_count = 0
        max_pages = 100  # Safety limit
        
        while page_count < max_pages:
            page_count += 1
            print(f"\n--- Processing Page {page_count} ---")
            
            # Wait for table to be present
            try:
                table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            except:
                print("Table not found on this page, stopping...")
                break
            
            # Get all data rows (skip header row)
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            page_data = []
            
            for i, row in enumerate(rows):
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 11:  # Ensure row has at least 11 columns
                    # Extract only first 11 columns
                    row_data = [cell.text.strip() for cell in cells[:11]]
                    if any(row_data):  # Only add non-empty rows
                        page_data.append(row_data)
                        all_data.append(row_data)
            
            print(f"✓ Extracted {len(page_data)} rows from page {page_count}")
            print(f"Total rows collected so far: {len(all_data)}")
            
            # Show sample of first few rows from this page
            if page_data:
                print("Sample rows from this page:")
                for j, row in enumerate(page_data[:3]):  # Show first 3 rows
                    print(f"  Row {j+1}: {row}")
            
            # Look for next button and try to click it
            next_button = None
            pagination_selectors = [
                "//a[contains(text(), 'Next')]",
                "//a[contains(text(), 'next')]",
                "//a[contains(text(), 'পরবর্তী')]",  # Bengali for 'Next'
                "//a[contains(@class, 'next')]",
                "//button[contains(text(), 'Next')]",
                "//a[@rel='next']",
                "//a[contains(@class, 'page-link') and contains(text(), '>')]",
                "//li[contains(@class, 'next')]/a",
                f"//a[contains(text(), '{page_count + 1}')]"  # Try clicking next page number
            ]
            
            for selector in pagination_selectors:
                try:
                    next_button = driver.find_element(By.XPATH, selector)
                    if next_button.is_enabled() and next_button.is_displayed():
                        print(f"✓ Found next button: '{next_button.text.strip()}'")
                        break
                    else:
                        next_button = None
                except:
                    continue
            
            if next_button:
                try:
                    # Scroll to button and click
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    next_button.click()
                    
                    # Wait for page to load
                    time.sleep(3)
                    print("✓ Clicked next button, waiting for new page...")
                    
                except Exception as e:
                    print(f"❌ Could not click next button: {e}")
                    break
            else:
                print("❌ No more pages found or next button not available")
                break
        
        # Save data to CSV
        if all_data:
            # Ensure all rows have exactly 11 columns
            cleaned_data = []
            for row in all_data:
                if len(row) >= 11:
                    cleaned_data.append(row[:11])  # Take first 11 columns
                elif len(row) > 0:
                    # Pad with empty strings if row has fewer than 11 columns
                    padded_row = row + [''] * (11 - len(row))
                    cleaned_data.append(padded_row)
            
            # Create DataFrame with first 11 columns
            df = pd.DataFrame(cleaned_data, columns=headers[:11] if len(headers) >= 11 else headers + [f'Col_{i}' for i in range(len(headers), 11)])
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"power_grid_data_11cols_{timestamp}.csv"
            
            # Save to CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            print(f"\n✓ SUCCESS!")
            print(f"✓ Total pages processed: {page_count}")
            print(f"✓ Total rows extracted: {len(cleaned_data)}")
            print(f"✓ Data saved to: {filename}")
            print(f"✓ Columns saved: {len(df.columns)}")
            
            # Show data summary
            print(f"\nData Summary:")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("\nFirst 5 rows:")
            print(df.head().to_string())
            
            # Show last 5 rows
            print("\nLast 5 rows:")
            print(df.tail().to_string())
            
            return True, filename, len(cleaned_data)
            
        else:
            print("❌ No data extracted!")
            return False, None, 0
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        return False, None, 0
        
    finally:
        if driver:
            print("\nClosing browser...")
            driver.quit()

def quick_test_11_columns():
    """Quick test to scrape first page with first 11 columns only"""
    
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    driver = None
    try:
        print("Starting quick test for first 11 columns...")
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 10)
        
        url = "https://erp.powergrid.gov.bd/w/generations/view_generations_bn"
        print(f"Navigating to: {url}")
        driver.get(url)
        time.sleep(5)
        
        # Find table
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        print("✓ Table found!")
        
        # Get headers (first 11)
        header_row = table.find_element(By.TAG_NAME, "tr")
        th_elements = header_row.find_elements(By.TAG_NAME, "th")
        if th_elements:
            headers = [th.text.strip() for th in th_elements[:11]]
        else:
            td_elements = header_row.find_elements(By.TAG_NAME, "td")
            headers = [td.text.strip() for td in td_elements[:11]]
        
        print(f"Headers (first 11): {headers}")
        
        # Get sample data (first 10 rows, first 11 columns)
        rows = table.find_elements(By.TAG_NAME, "tr")[1:11]  # First 10 data rows
        data = []
        
        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 11:
                row_data = [cell.text.strip() for cell in cells[:11]]  # First 11 columns
                data.append(row_data)
                print(f"Row {i+1}: {row_data}")
        
        # Save sample
        if data:
            df = pd.DataFrame(data, columns=headers)
            filename = "power_grid_sample_11cols.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"✓ Sample saved to {filename}")
            return True
        
        return False
        
    except Exception as e:
        print(f"Test error: {e}")
        return False
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("Power Grid Scraper - First 11 Columns")
    print("=" * 45)
    
    choice = input("\nChoose option:\n1. Quick test (first page, 11 columns)\n2. Full scrape (all pages, 11 columns)\nEnter choice (1 or 2): ")
    
    if choice == "1":
        success = quick_test_11_columns()
        if success:
            print("\n✓ Quick test completed successfully!")
        else:
            print("\n❌ Quick test failed.")
    
    elif choice == "2":
        print("\nStarting full scrape...")
        success, filename, row_count = scrape_first_11_columns()
        if success:
            print(f"\n🎉 SCRAPING COMPLETED SUCCESSFULLY!")
            print(f"📁 File: {filename}")
            print(f"📊 Rows: {row_count}")
            print(f"📋 Columns: 11")
        else:
            print("\n❌ Scraping failed.")
    
    else:
        print("Invalid choice. Running quick test...")
        quick_test_11_columns()
