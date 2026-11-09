"""Optional live browser checks. Requires Selenium and local Chrome, plus running lab."""
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]

def main():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1100')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL'})
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 40)
    checks = []
    try:
        for platform, port in [('php', 18081), ('node', 18082)]:
            driver.get(f'http://127.0.0.1:{port}/')
            wait.until(lambda d: d.find_element(By.ID, 'endpoint').text)
            def submit(sample, expected):
                driver.find_element(By.CSS_SELECTOR, f'[data-sample="{sample}"]').click()
                driver.find_element(By.ID, 'submit').click()
                wait.until(lambda d: d.find_element(By.ID, 'submit').is_enabled())
                actual = driver.find_element(By.ID, 'http-code').text
                assert actual == str(expected), (platform, sample, actual)
                checks.append(f'{platform}: {sample} HTTP {actual}')
            driver.find_element(By.ID, 'submit').click()
            assert driver.find_element(By.ID, 'form-message').text
            submit('image', 201)
            if platform == 'node':
                assert '/defended/file/' in driver.find_element(By.CSS_SELECTOR, '#file-actions a').get_attribute('href')
            submit('fake', 415)
            submit('polyglot', 201)
            result = json.loads(driver.find_element(By.ID, 'response').text)
            assert result['marker_present'] is False
            driver.save_screenshot(str(ROOT/'docs'/f'ui-{platform}-desktop.png'))
            driver.find_element(By.CSS_SELECTOR, 'input[value="vulnerable"]').click()
            submit('fake', 200 if platform == 'php' else 201)
            assert len(driver.find_elements(By.CSS_SELECTOR, '#history tr')) == 4
            driver.find_element(By.ID, 'clear-history').click()
            assert len(driver.find_elements(By.CSS_SELECTOR, '#history tr')) == 1
            driver.find_element(By.ID, 'reset').click()
            assert not driver.find_element(By.ID, 'result').is_displayed()
            driver.find_element(By.ID, 'file').send_keys(str(ROOT/'tests/payloads/marker.png'))
            driver.find_element(By.ID, 'submit').click()
            wait.until(lambda d: d.find_element(By.ID, 'submit').is_enabled())
            assert driver.find_element(By.ID, 'http-code').text == '201'
            checks.append(f'{platform}: real file selection, reset, history, validation')
            driver.set_window_size(390, 844)
            assert driver.execute_script('return document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow'
            driver.save_screenshot(str(ROOT/'docs'/f'ui-{platform}-mobile.png'))
            driver.set_window_size(1440, 1100)
            errors = [e for e in driver.get_log('browser') if e['level'] == 'SEVERE' and 'favicon' not in e['message'] and '415' not in e['message']]
            assert not errors, errors
        print(json.dumps(checks, ensure_ascii=True, indent=2))
        (ROOT/'docs/ui-browser-results.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
    finally:
        driver.quit()

if __name__ == '__main__':
    main()