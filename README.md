# NewsMonitor
NewsMonitor is a Python-based tool designed to streamline the process of collecting, analyzing, and distributing daily news updates, specifically focused on European institutions and policies. It automates repetitive tasks, saving time and ensuring more accurate and timely insights for professional use.

Key Features

Web Scraping: Extracts articles from predefined sources using BeautifulSoup and customizable selectors for specific websites.
Summarization: Uses nltk to generate concise summaries of up to 5 sentences for each article.
History Management: Tracks processed articles in a JSON file to avoid duplicates.
Email Automation: Generates an HTML email with structured news summaries and sends it via SMTP.
Document Integration: Reads URLs from a Word file (links.docx), simplifying source management.
Technologies Used
Python libraries: requests, BeautifulSoup, nltk, smtplib, docx, and json.

Setup and Execution

Add source URLs to links.docx on the desktop.
Configure sender and recipient email addresses in the code.
Run the script to collect, process, and email the day’s news.
Example Use Case
Daily monitoring of EU policy updates for internal reports, providing quick summaries for decision-making or stakeholder briefings.

Contribution
The project was entirely developed by Simone Luca Gaio to enhance workflow efficiency in tracking European developments.
