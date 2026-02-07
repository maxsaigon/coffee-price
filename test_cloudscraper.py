
import cloudscraper
import logging

logging.basicConfig(level=logging.DEBUG)

def test_cloudscraper():
    print("Testing cloudscraper...")
    scraper = cloudscraper.create_scraper()
    url = 'https://www.investing.com/commodities/london-coffee'
    try:
        response = scraper.get(url)
        print(f"Status: {response.status_code}")
        print(f"Length: {len(response.text)}")
        if "instrument-price-last" in response.text or "pid-8830-last" in response.text:
            print("Found price element!")
        else:
            print("Price element NOT found.")
            # Save for inspection
            with open("cloudscraper_debug.html", "w") as f:
                f.write(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_cloudscraper()
