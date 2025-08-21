# Project Plan: Vietnam Cafe Price Tracker

## 1. Introduction
This project aims to develop a Python application to automatically crawl and collect cafe prices across various platforms in Vietnam. The collected data will be processed into a daily report and sent to a specified Telegram channel every morning.

## 2. Core Features
*   **Cafe Price Crawling:** Automatically extract price information from selected cafe websites/platforms in Vietnam.
*   **Data Storage:** Store collected price data for historical analysis and reporting.
*   **Report Generation:** Generate a concise and informative daily report summarizing price trends or specific price points.
*   **Telegram Notification:** Send the generated report to a Telegram channel/group.
*   **Automated Scheduling:** Run the crawling, reporting, and notification tasks daily at a specific time.

## 3. Technical Stack
*   **Programming Language:** Python 3.x
*   **Web Crawling:**
    *   `requests`: For making HTTP requests to websites.
    *   `BeautifulSoup4` or `Scrapy`: For parsing HTML content and extracting data. (Consider `Scrapy` for more complex, large-scale crawling).
*   **Data Storage:**
    *   `SQLite` (for simplicity, embedded database) or `PostgreSQL` (for scalability).
    *   `SQLAlchemy` (ORM) for database interaction.
*   **Data Analysis/Reporting:**
    *   `pandas`: For data manipulation and analysis.
    *   `matplotlib` or `seaborn`: For basic data visualization (optional, if reports include charts).
*   **Telegram Integration:**
    *   `python-telegram-bot`: For interacting with the Telegram Bot API.
*   **Scheduling:**
    *   `APScheduler` or `Celery` (with a message broker like RabbitMQ/Redis for more robust scheduling). For simple daily tasks, `APScheduler` is sufficient.
*   **Environment Management:** `venv` or `conda`

## 4. High-Level Architecture

```
+-------------------+       +-------------------+       +-------------------+
|   Scheduler       | ----> |   Crawler Module  | ----> |   Data Storage    |
| (e.g., APScheduler)|       | (requests, BS4/Scrapy)|   | (SQLite/PostgreSQL)|
+-------------------+       +-------------------+       +-------------------+
         |                               ^
         |                               |
         v                               |
+-------------------+       +-------------------+
|   Report Generator| <---- |   Data Retrieval  |
| (pandas, matplotlib)|       | (SQLAlchemy)      |
+-------------------+       +-------------------+
         |
         v
+-------------------+
| Telegram Notifier |
| (python-telegram-bot)|
+-------------------+
```

## 5. Data Collection Strategy (Crawling)
*   **Identify Target Websites:** List popular cafe chains or food delivery platforms in Vietnam (e.g., Highlands Coffee, Phuc Long, GrabFood, ShopeeFood, Baemin).
*   **Analyze Website Structure:** Understand the HTML structure of price listings on each target site.
*   **Develop Parsers:** Write specific parsing logic for each website to extract cafe name, item name, price, and any other relevant details.
*   **Handle Anti-Scraping Measures:** Implement strategies for CAPTCHAs, IP blocking, or dynamic content loading (e.g., using `Selenium` if JavaScript rendering is required).
*   **Error Handling:** Gracefully handle network errors, website structure changes, or missing data.

## 6. Data Processing and Reporting
*   **Data Cleaning:** Clean and standardize collected data (e.g., currency conversion, removing extra characters).
*   **Data Aggregation:** Aggregate data to identify average prices, price ranges, or specific deals.
*   **Report Content:**
    *   Summary of price changes for key items.
    *   Comparison of prices across different cafes/platforms.
    *   Highlights of significant price drops or increases.
*   **Report Format:** Generate reports in a readable format (e.g., plain text, Markdown, or a simple image of a chart).

## 7. Notification Mechanism (Telegram)
*   **Telegram Bot Setup:** Create a new Telegram Bot via BotFather and obtain the API token.
*   **Channel/Group ID:** Get the chat ID of the Telegram channel or group where reports will be sent.
*   **Message Formatting:** Format the report content for clear display in Telegram messages.

## 8. Scheduling
*   Configure the scheduler to run the entire workflow (crawl -> process -> report -> notify) once every 24 hours, preferably in the early morning.

## 9. Future Enhancements
*   **User Configuration:** Allow users to configure target cafes, specific items to track, or notification preferences.
*   **Historical Data Analysis:** Develop a simple web interface or more advanced reports for historical price trends.
*   **Proxy Rotation:** Implement proxy rotation for more robust crawling.
*   **Machine Learning:** Predict price changes or identify optimal buying times (long-term).
*   **Dockerization:** Package the application in Docker containers for easier deployment.