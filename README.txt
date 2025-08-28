Auto Job Applier - LinkedIn (Merged Final)

Overview:
- This project automates searching LinkedIn jobs (keyword+location), extracts HR emails when available, and automatically sends your resume using Gmail API.
- It also provides a mobile-friendly Flask dashboard to monitor jobs and control the bot.

Important legal & safety note:
- Automating actions on LinkedIn may violate LinkedIn's Terms of Service. Use this only for personal use and at your own risk. LinkedIn may block or restrict accounts that use automation.
- This tool will NOT bypass any authentication or security mechanisms. Do not use it for scraping private data or performing abusive actions.

Files:
- app.py -- Flask web app + dashboard + bot control
- scraper.py -- LinkedIn scraper using Selenium
- sender.py -- Gmail send helper (uses token.json from OAuth flow)
- templates/index.html -- Dashboard UI
- requirements.txt -- Python packages
- README has setup details below

Setup (local testing):
1. Install Chrome and ChromeDriver. Make sure chromedriver is compatible with your Chrome version.
   - On Linux, chromedriver path commonly at /usr/bin/chromedriver
   - Or install via package manager or download from https://chromedriver.chromium.org/

2. Create virtualenv & install packages:
   python -m venv env
   source env/bin/activate   # Windows: env\\Scripts\\activate
   pip install -r requirements.txt

3. Place your resume.pdf inside the project folder (named exactly resume.pdf).

4. Provide LinkedIn credentials via environment variables:
   export LINKEDIN_EMAIL="your_email"
   export LINKEDIN_PASSWORD="your_password"
   export CHROMEDRIVER_PATH="/path/to/chromedriver"  # optional if chromedriver is on PATH
   export SECRET_KEY="some-secret"

5. Create Gmail OAuth credentials (Web client) in Google Cloud Console, download credentials.json, place in project root.
   - Run the Flask app and visit http://localhost:5000/authorize to complete OAuth flow (this will create token.json).

6. Run the app:
   python app.py
   Open http://localhost:5000 on your machine, then open same URL on your mobile after deployment.

Deployment recommendations:
- Use a VPS (DigitalOcean) or a server with GUI Chrome support for headless Chrome. Render and Railway may require extra setup to run headless Chromium.
- Configure the environment variables on the server (LINKEDIN_EMAIL, LINKEDIN_PASSWORD, SECRET_KEY, CHROMEDRIVER_PATH).
- Do NOT commit credentials.json, token.json, or resume.pdf to public repos. Use environment vars or secret managers.

How it works:
- The bot logs into LinkedIn with provided credentials, searches for jobs, saves new jobs to SQLite DB, attempts to extract an email from the job page, and if found sends your resume via Gmail API automatically.
- The dashboard shows saved jobs and allows manual send if needed.

Limitations & notes:
- LinkedIn often does not provide HR emails; many listings require applying via LinkedIn's apply flow. This bot attempts a simple heuristic to find emails on the job page, but success is not guaranteed.
- Running 24/7 requires a reliable server and handling of potential captchas or blocks from LinkedIn.
- Use delays and reasonable scraping intervals to reduce risk of being blocked.



=== AUTOMATION & DEPLOYMENT FILES INCLUDED ===

This package includes Dockerfile, docker-compose.yml, setup.sh (for VPS), Procfile (for PaaS), and systemd service example.

What you still must do manually (compulsory):
- Provide credentials.json (Google OAuth Web client) and place in project root OR set CREDENTIALS_JSON env var on host.
- Place resume.pdf in project root.
- Set environment variables: LINKEDIN_EMAIL, LINKEDIN_PASSWORD, SECRET_KEY, TEST_RECEIVER.
- In Google Cloud Console add the deployed domain or server IP + /oauth2callback as redirect URI.

Automation steps (recommended):
1) Upload this project to your server (scp or git).
2) Make sure resume.pdf and credentials.json are uploaded.
3) Run: sudo bash setup.sh
4) The script installs Docker and runs docker compose; the app will be available at port 5000.

Notes:
- If your provider uses a firewall, open port 5000 or set up a reverse proxy (nginx) and enable HTTPS.
- For production, use a domain + HTTPS and add that redirect_uri to Google OAuth client.
