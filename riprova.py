import re
import requests
from bs4 import BeautifulSoup
from docx import Document
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import time
import json
import os
from urllib.parse import urlparse, urljoin
from nltk import download, tokenize

# Scarica le risorse necessarie di nltk
download('punkt', quiet=True)

class NewsMonitor:
    def __init__(self):
        self.sender_email = '*************'
        self.sender_password = '****************'
        self.recipient_email = '****************'
        self.history_file = 'news_history.json'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_article_content(self, article_url):
        try:
            response = requests.get(article_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')
            content = ' '.join(p.get_text().strip() for p in paragraphs if p.get_text().strip())
            return content.strip()
        except Exception as e:
            print(f"Errore nell'ottenere il contenuto dell'articolo {article_url}: {e}")
            return ""

    def summarize_text(self, text):
        sentences = tokenize.sent_tokenize(text)
        if len(sentences) >= 5:  # Riassunto esteso a 5 frasi per maggiore completezza
            return ' '.join(sentences[:5])
        return text

    def get_article_date(self, article_element, site_specific_info=None):
        date_patterns = [
            r"\b\d{1,2}/\d{1,2}/\d{4}\b",  # Formato numerico
            r"\b\d{1,2} \w+ \d{4}\b",      # Formato giorno mese anno
            r"\b\w+ \d{1,2}, \d{4}\b"      # Formato mese giorno, anno
        ]
        if site_specific_info and 'date_selector' in site_specific_info:
            date_tags = article_element.select(site_specific_info['date_selector'])
        else:
            date_tags = article_element.find_all(['time', 'span', 'div', 'p'])

        for date_tag in date_tags:
            date_text = date_tag.get_text().strip()
            if date_text:
                parsed_date = self.parse_date(date_text)
                if parsed_date:
                    return parsed_date.strftime("%d/%m/%Y")

        raw_text = article_element.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, raw_text)
            if match:
                parsed_date = self.parse_date(match.group())
                if parsed_date:
                    return parsed_date.strftime("%d/%m/%Y")

        return None

    def parse_date(self, date_str):
        date_formats = [
            "%d/%m/%Y", "%d %B %Y", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y",
            "%d.%m.%Y", "%d-%m-%Y", "%Y/%m/%d"
        ]
        for fmt in date_formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def extract_articles(self, url, site_specific_info=None):
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            domain = urlparse(url).netloc

            articles = []

            # Simula la data di oggi come il 14 novembre 2024
            today = datetime.datetime(2024, 11, 14).date()

            if site_specific_info and 'article_selector' in site_specific_info:
                article_elements = soup.select(site_specific_info['article_selector'])
            else:
                article_elements = soup.find_all(['article', 'div'])

            seen_titles = set()  # Per evitare duplicati
            for article in article_elements:
                title_elem = article.find(['h1', 'h2', 'h3'])
                date_text = self.get_article_date(article, site_specific_info)

                if date_text:
                    parsed_date = self.parse_date(date_text)
                    if parsed_date and parsed_date.date() == today:
                        if title_elem:
                            title = title_elem.get_text().strip()
                            if title in seen_titles:
                                continue  # Salta articoli con titoli duplicati
                            seen_titles.add(title)

                            link_elem = article.find('a', href=True)
                            if link_elem:
                                article_url = urljoin(url, link_elem['href'])
                                content = self.get_article_content(article_url)
                                summary = self.summarize_text(content)

                                if title and summary:
                                    articles.append({
                                        'title': title,
                                        'content': summary,
                                        'source': domain,
                                        'url': article_url,
                                        'date': date_text,
                                        'id': f"{domain}-{hash(title)}"
                                    })
            return articles
        except Exception as e:
            print(f"Errore nell'elaborazione di {url}: {e}")
            return []

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self, articles):
        history = self.load_history()
        history.extend([article['id'] for article in articles])
        history = history[-1000:]
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f)

    def filter_new_articles(self, articles):
        history = self.load_history()
        return [article for article in articles if article['id'] not in history]

    def format_email_html(self, articles):
        html = f"""
        <html>
            <body>
                <h1>Monitoraggio Europeo - {datetime.datetime.now().strftime("%d/%m/%Y")}</h1>
                <hr>
        """
        for article in articles:
            html += f"""
                <h2>{article['title']}</h2>
                <p><strong>Fonte:</strong> {article['source']}</p>
                <p><strong>Data:</strong> {article['date']}</p>
                <p>{article['content']}</p>
                <p><a href="{article['url']}">Leggi l'articolo completo</a></p>
                <hr>
            """
        html += """
            </body>
        </html>
        """
        return html

    def send_email(self, articles):
        if not articles:
            print("Nessun nuovo articolo da inviare.")
            return

        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = self.recipient_email
        msg['Subject'] = f"Monitoraggio Europeo - {datetime.datetime.now().strftime('%d/%m/%Y')}"

        body = self.format_email_html(articles)
        msg.attach(MIMEText(body, 'html'))

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            print("Email inviata con successo!")
        except Exception as e:
            print(f"Errore nell'invio dell'email: {e}")

    def run(self):
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        doc_path = os.path.join(desktop_path, 'links.docx')

        if not os.path.exists(doc_path):
            print(f"Il file {doc_path} non esiste.")
            return

        doc = Document(doc_path)
        urls = [p.text.strip() for p in doc.paragraphs if p.text.strip().startswith('http')]
        print(f"Totale URL trovati: {len(urls)}")

        all_articles = []

        for i, url in enumerate(urls, 1):
            print(f"Elaborazione di {url} ({i}/{len(urls)})")
            site_specific_info = self.get_site_specific_info(url)
            articles = self.extract_articles(url, site_specific_info)
            print(f"Articoli trovati per {url}: {len(articles)}")
            all_articles.extend(articles)

        new_articles = self.filter_new_articles(all_articles)

        if new_articles:
            self.send_email(new_articles)
            self.save_history(new_articles)
        else:
            print("Nessun nuovo articolo trovato.")

        print(f"Totale articoli trovati: {len(all_articles)}")
        print(f"Nuovi articoli: {len(new_articles)}")

    def get_site_specific_info(self, url):
        site_mapping = {
            "https://ec.europa.eu/commission/presscorner/home/en": {
                'article_selector': 'section.latest-news li',
                'date_selector': 'span.date'
            },
            # Aggiungi altre configurazioni specifiche per i siti basandoti sul file Word
        }
        for key in site_mapping:
            if key in url:
                return site_mapping[key]
        return None

if __name__ == "__main__":
    monitor = NewsMonitor()
    monitor.run()
