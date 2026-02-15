# RAG Application - Server Deployment Guide

This guide provides complete instructions for deploying the RAG application to a production server.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Process Management](#process-management)
7. [Nginx Configuration](#nginx-configuration)
8. [SSL/HTTPS Setup](#sslhttps-setup)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

The server must have the following installed:

- **Operating System**: Ubuntu 20.04+ or similar Linux distribution
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher
- **Git**: For cloning the repository
- **Nginx**: For reverse proxy (optional but recommended)
- **PM2**: For process management (recommended)

---

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB free space
- **Network**: Public IP address with open ports 80 and 443

### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 50+ GB SSD
- **Network**: Public IP with firewall configured

---

## Installation Steps

### 1. Install System Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.10+ and pip
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install build essentials
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y

# Install Nginx (optional, for reverse proxy)
sudo apt install nginx -y

# Install PM2 globally (for process management)
sudo npm install -g pm2
```

### 2. Clone the Repository

```bash
# Clone the project
cd /var/www/
sudo git clone <your-repository-url> rag-app
cd rag-app

# Set proper permissions
sudo chown -R $USER:$USER /var/www/rag-app
```

### 3. Backend Setup

```bash
cd /var/www/rag-app/backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Frontend Setup

```bash
cd /var/www/rag-app/frontend

# Install Node.js dependencies
npm install

# Build the production bundle
npm run build
```

---

## Configuration

### 1. Backend Configuration

Create the `.env` file in the `backend` directory:

```bash
cd /var/www/rag-app/backend
nano .env
```

Add the following environment variables:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# LangSmith Configuration
LANGSMITH_API_KEY=ls-your-key
LANGSMITH_PROJECT=rag-masterclass

# Encryption Key (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
SETTINGS_ENCRYPTION_KEY=your-fernet-key

# CORS Configuration (adjust for your domain)
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]

# Reranker Configuration (Optional - Jina AI)
# Sign up at https://jina.ai/reranker for free tier (10k calls/month)
JINA_API_KEY=jina_your_api_key_here
JINA_RERANK_MODEL=jina-reranker-v2-base-multilingual
JINA_RERANK_ENABLED=true
```

**Generate Encryption Key:**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Frontend Configuration

Create the `.env` file in the `frontend` directory:

```bash
cd /var/www/rag-app/frontend
nano .env
```

Add the following environment variables:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://yourdomain.com/api
```

**Important**: After updating `.env`, rebuild the frontend:

```bash
npm run build
```

---

## Running the Application

### Option 1: Manual Start (For Testing)

#### Start Backend:
```bash
cd /var/www/rag-app/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Serve Frontend (Production):
```bash
cd /var/www/rag-app/frontend
npx serve -s dist -p 5173
```

### Option 2: Using PM2 (Recommended for Production)

#### Create PM2 Ecosystem File:

```bash
cd /var/www/rag-app
nano ecosystem.config.js
```

Add the following configuration:

```javascript
module.exports = {
  apps: [
    {
      name: 'rag-backend',
      cwd: '/var/www/rag-app/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: {
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/var/www/rag-app/logs/backend-error.log',
      out_file: '/var/www/rag-app/logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'rag-frontend',
      cwd: '/var/www/rag-app/frontend',
      script: 'npx',
      args: 'serve -s dist -p 5173',
      interpreter: 'none',
      error_file: '/var/www/rag-app/logs/frontend-error.log',
      out_file: '/var/www/rag-app/logs/frontend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,
      autorestart: true,
      watch: false
    }
  ]
};
```

#### Create logs directory:
```bash
mkdir -p /var/www/rag-app/logs
```

#### Start with PM2:
```bash
cd /var/www/rag-app
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

---

## Process Management

### PM2 Commands

```bash
# View all processes
pm2 list

# View logs
pm2 logs

# View specific app logs
pm2 logs rag-backend
pm2 logs rag-frontend

# Restart an app
pm2 restart rag-backend
pm2 restart rag-frontend

# Restart all apps
pm2 restart all

# Stop an app
pm2 stop rag-backend

# Start an app
pm2 start rag-backend

# Delete an app
pm2 delete rag-backend

# Monitor resources
pm2 monit
```

---

## Nginx Configuration

### Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/rag-app
```

Add the following configuration:

```nginx
# Frontend (React)
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Frontend static files
    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE/Streaming support
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

### Enable the site:

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/rag-app /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test automatic renewal
sudo certbot renew --dry-run
```

The Certbot will automatically configure Nginx for HTTPS.

### Update Frontend .env for HTTPS

After setting up SSL, update the frontend `.env`:

```bash
cd /var/www/rag-app/frontend
nano .env
```

Change `VITE_API_URL` to use HTTPS:
```env
VITE_API_URL=https://yourdomain.com/api
```

Rebuild frontend:
```bash
npm run build
pm2 restart rag-frontend
```

---

## Troubleshooting

### Check Service Status

```bash
# Check if services are running
pm2 list

# Check Nginx status
sudo systemctl status nginx

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check backend logs
pm2 logs rag-backend --lines 100

# Check frontend logs
pm2 logs rag-frontend --lines 100
```

### Common Issues

#### Backend won't start:
1. Check if virtual environment is activated
2. Verify `.env` file exists and has correct values
3. Check port 8000 is not already in use: `sudo lsof -i :8000`
4. Review backend logs: `pm2 logs rag-backend`

#### Frontend build fails:
1. Ensure Node.js 18+ is installed: `node --version`
2. Clear npm cache: `npm cache clean --force`
3. Delete node_modules and reinstall: `rm -rf node_modules && npm install`
4. Check `.env` file has all required variables

#### CORS errors:
1. Verify `CORS_ORIGINS` in backend `.env` includes your domain
2. Ensure frontend is using HTTPS if backend is
3. Check Nginx proxy headers are configured correctly

#### Database connection issues:
1. Verify Supabase credentials in `.env`
2. Check if Supabase service is accessible from server
3. Verify network/firewall settings

### Firewall Configuration

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Allow SSH (if not already allowed)
sudo ufw allow ssh

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

---

## Quick Commands Reference

### Start Everything:
```bash
cd /var/www/rag-app
pm2 start ecosystem.config.js
```

### Stop Everything:
```bash
pm2 stop all
```

### Restart After Code Update:
```bash
cd /var/www/rag-app

# Pull latest code
git pull

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart rag-backend

# Update frontend
cd ../frontend
npm install
npm run build
pm2 restart rag-frontend
```

### View Logs:
```bash
# All logs
pm2 logs

# Backend only
pm2 logs rag-backend

# Frontend only
pm2 logs rag-frontend
```

---

## Security Recommendations

1. **Never commit `.env` files** to version control
2. **Use strong passwords** for all services
3. **Keep dependencies updated**: Regularly run `pip list --outdated` and `npm outdated`
4. **Enable firewall**: Use `ufw` or `iptables`
5. **Regular backups**: Backup Supabase database regularly
6. **Monitor logs**: Set up log monitoring and alerting
7. **Use HTTPS**: Always use SSL certificates in production
8. **Restrict database access**: Use Row-Level Security in Supabase
9. **Keep secrets safe**: Use environment variables, never hardcode

---

## Support

For issues or questions:
- Check application logs: `pm2 logs`
- Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Review backend logs: `/var/www/rag-app/logs/backend-error.log`
- Check system resources: `pm2 monit`

---

**Last Updated**: 2026-02-15
