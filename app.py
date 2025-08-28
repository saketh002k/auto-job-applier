from flask import Flask, render_template, request, redirect, url_for, flash
from threading import Thread, Event
import os, time, sqlite3
from scraper import LinkedInBot

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_now")
DB = "jobs.db"
BOT_THREAD = None
STOP_EVENT = Event()
bot = None

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        link TEXT UNIQUE,
        hr_email TEXT,
        status TEXT,
        applied_at TEXT
    )""")
    conn.commit()
    conn.close()

@app.route("/")
def index():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, title, company, location, link, hr_email, status, applied_at FROM jobs ORDER BY id DESC")
    jobs = c.fetchall()
    conn.close()
    running = BOT_THREAD is not None and BOT_THREAD.is_alive()
    return render_template("index.html", jobs=jobs, running=running)

@app.route("/start", methods=["POST"])
def start_bot():
    global BOT_THREAD, bot, STOP_EVENT
    if BOT_THREAD and BOT_THREAD.is_alive():
        flash("Bot is already running", "warning")
        return redirect(url_for("index"))
    # load config from form or env
    keyword = request.form.get("keyword") or os.environ.get("JOB_KEYWORD","Waiter")
    location = request.form.get("location") or os.environ.get("JOB_LOCATION","Hyderabad")
    interval = int(request.form.get("interval") or os.environ.get("SCRAPE_INTERVAL","300"))
    resume_path = "resume.pdf"
    # create bot instance
    bot = LinkedInBot(keyword=keyword, location=location, resume_path=resume_path, db_path=DB)
    STOP_EVENT.clear()
    BOT_THREAD = Thread(target=bot.run_forever, args=(interval, STOP_EVENT), daemon=True)
    BOT_THREAD.start()
    flash("Bot started", "success")
    return redirect(url_for("index"))

@app.route("/stop", methods=["POST"])
def stop_bot():
    global BOT_THREAD, STOP_EVENT, bot
    if BOT_THREAD and BOT_THREAD.is_alive():
        STOP_EVENT.set()
        BOT_THREAD.join(timeout=10)
        flash("Bot stopped", "info")
    else:
        flash("Bot is not running", "warning")
    return redirect(url_for("index"))

@app.route("/apply_manual/<int:job_id>", methods=["POST"])
def apply_manual(job_id):
    # trigger send for a specific job from DB
    import sender
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, title, company, location, link, hr_email FROM jobs WHERE id=?", (job_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        flash("Job not found", "danger")
        return redirect(url_for("index"))
    _, title, company, location, link, hr_email = row
    if not hr_email:
        flash("No HR email for this job", "warning")
        return redirect(url_for("index"))
    sent = sender.send_application(hr_email, title, company, resume_path="resume.pdf")
    if sent:
        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("UPDATE jobs SET status=?, applied_at=? WHERE id=?", ("applied", time.strftime('%Y-%m-%d %H:%M:%S'), job_id))
        conn.commit(); conn.close()
        flash("Application sent manually", "success")
    else:
        flash("Failed to send application", "danger")
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
