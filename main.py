import requests
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import csv
import os
from selenium.webdriver.remote.remote_connection import RemoteConnection


def init_driver():
    driver = webdriver.Chrome()
    driver.set_page_load_timeout(10)
    options = webdriver.ChromeOptions() 
    options.add_argument('--blink-settings=imagesEnabled=false')  
    options.add_argument('--headless=new')  
    options.add_argument('--ignore-certificate-errors')  
    options.add_argument('--ignore-ssl-errors=yes')     
    options.add_argument('--disable-web-security')      
    options.add_argument('--allow-running-insecure-content')   
    options.add_argument('ignore-certificate-errors')
    options.add_argument('ignore-ssl-errors')
    options.add_argument('--enable-unsafe-swiftshader')
    options.add_argument('--disable-webgl') 
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.page_load_strategy = 'none'
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(10)
    driver.set_script_timeout(10)
    RemoteConnection.set_timeout(10)
    return driver



def diff_analysis(description):
    diff_keywords = {
        'Beginner': ['beginner', 'basic', 'novice', 'starter', 'easy', '7a', 'chapter 7'],
        'Intermediate': ['intermediate', 'medium', 'moderate', 'vanilla celeste', 'completed Farewell', 'actual farewell'],
        'Advanced': ['advanced'],
        'Expert': ['expert'],
        'Grandmaster': ['grandmaster', 'gm'],
        'GM+' : ['gm+', 'very challenging', 'chaotic', 'grandmaster+'],
    }
    found_words = set()
    description_lower = description.lower()
    for difficulty, keywords in diff_keywords.items():
        for keyword in keywords:
            if keyword.lower() in description_lower:
                found_words.add(difficulty)
    if not found_words:
        found_words.add('No difficulty available')
    return found_words


def extract_urls(base_url):
    urls = []
    current_page = 1
    headers = {  
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',  
        'Accept': 'application/json',  
        'Referer': 'https://gamebanana.com'  
    }  

    while True:
        try:
            api_url = f"{base_url}&_nPage={current_page}"  
            print(f"\nTrying to fetch page {current_page}")   
            response = requests.get(api_url, headers=headers)
            time.sleep(1)
            data = response.json()
            if len(data.get("_aRecords")) == 0:
                break
            for item in data['_aRecords']:
                if '_sProfileUrl' in item:
                    url = item['_sProfileUrl']
                    urls.append(url)
            current_page += 1
        except Exception as e:
            print(f"Error get page {current_page}:{str(e)}")
            break
    return urls


def extract_data(driver, url, errors):
    try:
        url_count = 0
        print(f"Processing {url}")
        url_count +=1
        if url_count % 30 == 0:
            print("Restarting browser...")  
            driver.quit()  
            driver = init_driver()  
        driver.execute_script("window.location.href='about:blank'")
        driver.get(url)
        print("get success")
        time.sleep(1)

        try:  
            alert = driver.switch_to.alert  
            alert.dismiss()  
        except:  
            pass  

        try:
            print("Trying XPATH")
            element = driver.find_element(By.XPATH, '//*[@id="ItemProfileModule"]/div/article')
        except Exception as e:
            try:
                element = driver.find_element(By.CLASS_NAME, 'RichText')  
                print(f"XPATH failed, trying CLASS_NAME: {str(e)}")
            except Exception as e:
                print(f"Both XPATH and CLASS_NAME failed: {str(e)}")
        description = element.get_attribute('textContent')
        print(f"success: {driver.title}.replace(' [Celeste] [Mods]', '')")
        result = {
            'url': url,
            'title': driver.title.replace(' [Celeste] [Mods]', ''),
            'description': description,
            'diffculties': list(diff_analysis(description))
        }
        return result
    
    except Exception as e:
        print(f"Error processing {url}: {str(e)}")
        error = {
            'url': url,
            'error': str(e),
        }
        errors[url] = error
        return None
    


def save_urls_to_csv(urls, filename = 'urls.csv'):
    df = pd.DataFrame(urls, columns=['url'])
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"URLs saved to {filename}")
    



def save_to_csv(results, filename = 'gamebanana_data.csv'):
    csv_data = []
    for result in results:
        if result:
            csv_data.append({
                'url': result['url'],
                'title': result['title'],
                'description': result['description'],
                'diffculties': '|'.join(result['diffculties'])
            })
    df = pd.DataFrame(csv_data)
    df.to_csv(filename, index=False, encoding='utf-8',
              quoting=csv.QUOTE_ALL, escapechar='\\',
              doublequote=True)
    print(f"Data saved to {filename}")



def save_errors_to_csv(errors, filename = 'errors.csv'):
    error_rows = []  
    for url, error_info in errors.items():  
        error_rows.append({  
            'url': url,  
            'error_message': error_info['error']  
        })  
    df = pd.DataFrame.from_dict(error_rows) 
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Errors saved to {filename}")


def retry_failed_urls(driver, results, errors, max_retries=5):  
    error_file = 'errors.csv'
    error_df = pd.read_csv(error_file)
    retry_urls = error_df['url'].tolist()
    if not retry_urls:
        print('No failed URLs found')
        return
    print(f'Found {len(retry_urls)} failed URLs')

    for i in range(max_retries):
        remaining_urls = []
        for url in retry_urls:
            result = extract_data(driver, url, errors)  
            if result:  
                error_df = error_df[error_df['url'] != url]
                error_df.to_csv(error_file, index=False)
                print(f"success: {url}")  
                results.append(result)
                if url in errors:
                    del errors[url]
            else:  
                print(f"failed: {url}")  
                remaining_urls.append(url)
        retry_urls = remaining_urls
        if not retry_urls:
            print('All URLs processed successfully')
            break  
        elif i < max_retries - 1:
            print(f'maximum retries reached, {len(retry_urls)} URLs still have errors')
    if errors:
        save_errors_to_csv(errors, 'data.csv')
        
    return driver, results, errors
    




def main():
    base_url = "https://gamebanana.com/apiv11/Mod/Index?_nPerpage=15&_aFilters%5BGeneric_Category%5D=6801"
    driver = init_driver()
    results = []
    errors = {}
    only_retry = input("Retry failed URLs only? (y/n): ")
    if only_retry.lower() == 'y':
        driver, retry_results, retry_errors = retry_failed_urls(driver, results, errors)
        save_to_csv(retry_results)
        errors.update(retry_errors)
        return

    url_complete = input("URL search complete? (y/n): ")
    if url_complete.lower() == 'n':
        urls = extract_urls(base_url)
        print(f"Found {len(urls)} urls")
        save_urls_to_csv(urls) 
    elif url_complete.lower() == 'y':
        urls = pd.read_csv('urls.csv')['url'].tolist() 
    else:
        print("Invalid input")
        return

    for url in urls:
        result = extract_data(driver, url, errors)
        if result:
            results.append(result)
    save_to_csv(results)
    save_errors_to_csv(errors)
    print("\nProcessing Summary:")  
    print(f"Total URLs processed: {len(results)}")  
    print(f"Total URLs with errors: {len(errors)}")
    if len(errors) > 0:
        print("Failed URLs:")
        for url in errors:
            print(url)
        if os.path.exists('errors.csv'):  
            print("Found failed URLs, starting retry...")  
            driver, retry_results, retry_errors = retry_failed_urls(driver)  
            save_to_csv(retry_results)    
            errors.update(retry_errors) 
    else:
        print("All URLs processed successfully.") 
    driver.quit()



if __name__ == "__main__":
    main()