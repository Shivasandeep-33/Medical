# Deployment Guide for MediSync AI

This guide details multiple deployment options ranging from free 1-click cloud platforms to Docker containers and traditional VPS hosting.

---

## 🌟 Option 1: Free Cloud Hosting (Render.com) — *Recommended & Easiest*

Render provides a free tier that deploys Python web applications directly from your GitHub repository.

### Steps:
1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for MediSync AI"
   git remote add origin https://github.com/YOUR_USERNAME/medisync-ai.git
   git branch -M main
   git push -u origin main
   ```
2. Go to **[Render.com](https://render.com)** and sign in.
3. Click **"New +"** -> **"Web Service"**.
4. Connect your GitHub repository.
5. Set the following settings:
   - **Name**: `medisync-ai`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt reportlab && python create_sample_pdfs.py`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. (Optional) In **Environment Variables**, add:
   - `GEMINI_API_KEY`: *(Your Google Gemini API Key, optional)*
7. Click **"Deploy Web Service"**.
8. Render will deploy your application and give you a public live URL (e.g. `https://medisync-ai.onrender.com`).

---

## 🚂 Option 2: Railway.app (1-Click Deploy)

1. Go to **[Railway.app](https://railway.app)**.
2. Click **"New Project"** -> **"Deploy from GitHub repo"**.
3. Select your repository.
4. Railway automatically detects the `Procfile` or `Dockerfile`.
5. Under service settings, click **"Generate Domain"** to get your public live URL.

---

## 🐳 Option 3: Docker & Docker Compose (Any Cloud / Server)

If you have Docker installed on your server, AWS EC2, DigitalOcean Droplet, or local machine:

### Using Docker Compose:
```bash
docker compose up -d --build
```
Your app will be live at `http://YOUR_SERVER_IP:8000`.

### Using standard Docker:
```bash
# Build the image
docker build -t medisync-ai .

# Run the container
docker run -d -p 8000:8000 --name medisync-container medisync-ai
```

---

## ☁️ Option 4: Google Cloud Run (Serverless)

Google Cloud Run automatically scales containers from 0 to many requests and offers a generous free tier.

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

# Build and deploy directly to Cloud Run
gcloud run deploy medisync-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000
```
GCP will output a live HTTPS URL (e.g. `https://medisync-ai-xxxx-uc.a.run.app`).

---

## 🐧 Option 5: Ubuntu / Debian Linux VPS (Nginx + Systemd)

If deploying to a traditional Linux Virtual Private Server:

### 1. Install system prerequisites:
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx git
```

### 2. Clone repository & create virtual environment:
```bash
cd /var/www
git clone https://github.com/YOUR_USERNAME/medisync-ai.git
cd medisync-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt reportlab
python create_sample_pdfs.py
```

### 3. Create Systemd Service (`/etc/systemd/system/medisync.service`):
```ini
[Unit]
Description=MediSync AI Web Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/medisync-ai
ExecStart=/var/www/medisync-ai/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start medisync
sudo systemctl enable medisync
```

### 4. Configure Nginx Reverse Proxy (`/etc/nginx/sites-available/medisync`):
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/medisync /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔒 Production Checklist

- [ ] **HTTPS / SSL**: Use Let's Encrypt (`sudo certbot --nginx -d yourdomain.com`) on VPS or rely on Render/Railway/Cloud Run automatic SSL.
- [ ] **API Keys**: Provide `GEMINI_API_KEY` as an environment variable in your production dashboard.
- [ ] **File Persistence**: If running in Docker, ensure `./data` is mounted to retain patient records between container restarts.
