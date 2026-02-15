# RAG Application - Quick Deployment Checklist

## Pre-Deployment

- [ ] Server running Ubuntu 20.04+ with public IP
- [ ] Domain name configured (DNS A record pointing to server IP)
- [ ] Python 3.10+ installed
- [ ] Node.js 18+ installed
- [ ] Nginx installed
- [ ] PM2 installed globally (`npm install -g pm2`)
- [ ] Supabase project created and configured
- [ ] SSL certificate ready (Let's Encrypt recommended)

## Installation Steps

### 1. System Setup
```bash
# Install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install python3.10 python3.10-venv python3-pip nodejs npm nginx -y
sudo npm install -g pm2

# Clone repository
cd /var/www/
sudo git clone <repo-url> rag-app
cd rag-app
sudo chown -R $USER:$USER .
```

### 2. Backend Setup
```bash
cd /var/www/rag-app/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
LANGSMITH_API_KEY=ls-your-key
LANGSMITH_PROJECT=rag-masterclass
SETTINGS_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
CORS_ORIGINS=["https://yourdomain.com"]
JINA_API_KEY=jina_key_optional
JINA_RERANK_MODEL=jina-reranker-v2-base-multilingual
JINA_RERANK_ENABLED=false
EOF

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Add the output to SETTINGS_ENCRYPTION_KEY in .env
```

### 3. Frontend Setup
```bash
cd /var/www/rag-app/frontend

# Install dependencies
npm install

# Create .env file
cat > .env << 'EOF'
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://yourdomain.com/api
EOF

# Build production bundle
npm run build
```

### 4. PM2 Configuration
```bash
cd /var/www/rag-app

# Create logs directory
mkdir -p logs

# Create ecosystem.config.js
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [
    {
      name: 'rag-backend',
      cwd: '/var/www/rag-app/backend',
      script: 'venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 8000',
      interpreter: 'none',
      env: { PYTHONUNBUFFERED: '1' },
      error_file: '/var/www/rag-app/logs/backend-error.log',
      out_file: '/var/www/rag-app/logs/backend-out.log',
      autorestart: true,
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
      autorestart: true
    }
  ]
};
EOF

# Start services
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

### 5. Nginx Configuration
```bash
# Create Nginx config
sudo tee /etc/nginx/sites-available/rag-app << 'EOF'
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/rag-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Update frontend .env to use HTTPS
cd /var/www/rag-app/frontend
sed -i 's|http://|https://|g' .env
npm run build
pm2 restart rag-frontend
```

### 7. Firewall
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

## Verification

- [ ] Backend health check: `curl http://localhost:8000/health`
- [ ] Frontend accessible: `curl http://localhost:5173`
- [ ] PM2 processes running: `pm2 list`
- [ ] Nginx running: `sudo systemctl status nginx`
- [ ] Domain accessible: Open https://yourdomain.com
- [ ] API accessible: `curl https://yourdomain.com/api/health`
- [ ] SSL certificate valid: Check browser lock icon
- [ ] Login works: Test authentication flow
- [ ] Document upload works: Test file upload
- [ ] Chat works: Test chat functionality

## Post-Deployment

### Monitor
```bash
# View all logs
pm2 logs

# Monitor resources
pm2 monit

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Update Deployment
```bash
cd /var/www/rag-app
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart rag-backend

# Frontend
cd ../frontend
npm install
npm run build
pm2 restart rag-frontend
```

### Backup Strategy
- [ ] Set up automated Supabase database backups
- [ ] Back up `.env` files securely (encrypted storage)
- [ ] Document all configuration changes
- [ ] Set up monitoring/alerting for downtime

## Common Issues

| Issue | Solution |
|-------|----------|
| Backend won't start | Check `.env` file, verify venv activation, check port 8000 |
| Frontend 404 errors | Run `npm run build` again, check `.env` variables |
| CORS errors | Update `CORS_ORIGINS` in backend `.env` |
| SSL not working | Run `sudo certbot renew`, check Nginx config |
| PM2 processes died | Check logs with `pm2 logs`, restart with `pm2 restart all` |
| Out of memory | Increase server RAM or adjust PM2 memory limit |

## Essential Commands

| Command | Description |
|---------|-------------|
| `pm2 list` | Show all running processes |
| `pm2 logs` | View logs from all processes |
| `pm2 restart all` | Restart all processes |
| `pm2 monit` | Monitor resource usage |
| `sudo nginx -t` | Test Nginx configuration |
| `sudo systemctl restart nginx` | Restart Nginx |
| `sudo certbot renew` | Renew SSL certificates |
| `pm2 save` | Save current PM2 process list |
| `pm2 startup` | Configure PM2 to start on boot |

## Environment Variables Reference

### Backend (.env)
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `LANGSMITH_API_KEY` - LangSmith API key
- `LANGSMITH_PROJECT` - LangSmith project name
- `SETTINGS_ENCRYPTION_KEY` - Fernet encryption key
- `CORS_ORIGINS` - Allowed CORS origins (JSON array)
- `JINA_API_KEY` - (Optional) Jina AI reranker key
- `JINA_RERANK_MODEL` - (Optional) Reranker model name
- `JINA_RERANK_ENABLED` - (Optional) Enable/disable reranking

### Frontend (.env)
- `VITE_SUPABASE_URL` - Supabase project URL (same as backend)
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key (same as backend)
- `VITE_API_URL` - Backend API URL (e.g., https://yourdomain.com/api)

---

**Ready to deploy?** Start with step 1 and check off each item as you go!
