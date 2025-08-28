import os, time, sqlite3, base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, WebDriverException
import traceback
from sender import send_application

class LinkedInBot:
    def __init__(self, keyword="Waiter", location="Hyderabad", resume_path="resume.pdf", db_path="jobs.db"):
        self.keyword = keyword
        self.location = location
        self.resume_path = resume_path
        self.db_path = db_path
        # LinkedIn credentials via env
        self.email = os.environ.get("LINKEDIN_EMAIL")
        self.password = os.environ.get("LINKEDIN_PASSWORD")
        if not self.email or not self.password:
            raise Exception("Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD env variables before running the bot.")
        # selenium setup
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        # path to chromedriver - can be provided via env CHROMEDRIVER_PATH
        chromedriver_path = os.environ.get("CHROMEDRIVER_PATH","/usr/bin/chromedriver")
        self.driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)

    def login(self):
        driver = self.driver
        driver.get("https://www.linkedin.com/login")
        time.sleep(2)
        email_el = driver.find_element(By.ID, "username")
        pw_el = driver.find_element(By.ID, "password")
        email_el.send_keys(self.email)
        pw_el.send_keys(self.password)
        pw_el.send_keys(Keys.RETURN)
        time.sleep(3)

    def search_jobs(self):
        driver = self.driver
        # build search URL for LinkedIn jobs
        q = self.keyword.replace(" ", "%20")
        loc = self.location.replace(" ", "%20")
        url = f"https://www.linkedin.com/jobs/search/?keywords={q}&location={loc}"
        driver.get(url)
        time.sleep(3)
        jobs = []
        # scroll and collect job cards
        for _ in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        cards = driver.find_elements(By.CSS_SELECTOR, "ul.jobs-search__results-list li")
        for card in cards[:20]:
            try:
                link_el = card.find_element(By.CSS_SELECTOR, "a.result-card__full-card-link")
                link = link_el.get_attribute("href")
            except Exception:
                link = None
            try:
                title = card.find_element(By.CSS_SELECTOR, "h3").text
            except Exception:
                title = ""
            try:
                company = card.find_element(By.CSS_SELECTOR, ".result-card__subtitle").text
            except Exception:
                company = ""
            try:
                location = card.find_element(By.CSS_SELECTOR, ".result-card__meta").text
            except Exception:
                location = ""
            jobs.append({"title": title, "company": company, "location": location, "link": link})
        return jobs

    def extract_hr_email_from_job(self, job_link):
        driver = self.driver
        try:
            driver.get(job_link)
            time.sleep(2)
            # naive extraction: look for mailto: or common patterns on page
            page = driver.page_source
            import re
            m = re.search(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", page)
            if m:
                return m.group(1)
            # fallback: look for '@' in page and pick first candidate
            emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", page)
            if emails:
                return emails[0]
        except Exception as e:
            print("extract email error", e)
        return None

    def save_job(self, job):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT OR IGNORE INTO jobs (title, company, location, link, hr_email, status) VALUES (?, ?, ?, ?, ?, ?)", 
                      (job.get("title"), job.get("company"), job.get("location"), job.get("link"), job.get("hr_email"), "new"))
            conn.commit()
        finally:
            conn.close()

    def run_once(self):
        try:
            self.login()
        except Exception as e:
            print("Login failed:", e)
            return
        jobs = self.search_jobs()
        for j in jobs:
            if not j.get("link"):
                continue
            # check if already exist in DB
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("SELECT id FROM jobs WHERE link=?", (j["link"],))
            exists = c.fetchone()
            conn.close()
            if exists:
                continue
            # extract email
            hr = self.extract_hr_email_from_job(j["link"])
            j["hr_email"] = hr
            self.save_job(j)
            # if email found, send application
            if hr:
                try:
                    sent = send_application(hr, j.get("title") or "Waiter", j.get("company") or "", resume_path=self.resume_path)
                    if sent:
                        conn = sqlite3.connect(self.db_path)
                        c = conn.cursor()
                        c.execute("UPDATE jobs SET status=?, hr_email=?, applied_at=? WHERE link=?", ("applied", hr, time.strftime('%Y-%m-%d %H:%M:%S'), j["link"]))
                        conn.commit(); conn.close()
                except Exception as e:
                    print("send failed", e)

    def run_forever(self, interval=300, stop_event=None):
        try:
            while True:
                if stop_event and stop_event.is_set():
                    break
                try:
                    self.run_once()
                except Exception as e:
                    print("run_once error", e)
                    traceback.print_exc()
                # sleep until next cycle
                for _ in range(int(interval)):
                    if stop_event and stop_event.is_set():
                        break
                    time.sleep(1)
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass
