# Server Requirements & Installation Summary

Quick reference guide for setting up the RAG application on a production server.

## Server Specifications

### Minimum Requirements
| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Ubuntu 20.04 LTS | Ubuntu 22.04 LTS |
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Storage** | 20 GB | 50+ GB SSD |
| **Network** | 1 Gbps | 1+ Gbps |

### Required Ports
| Port | Service | Purpose |
|------|---------|---------|
| 80 | HTTP | Web traffic (redirects to 443) |
| 443 | HTTPS | Secure web traffic |
| 22 | SSH | Server management |
| 8000 | Internal | Backend API (not exposed) |
| 5173 | Internal | Frontend server (not exposed) |

---

## Software Dependencies

### System Packages

| Package | Version | Installation Command | Purpose |
|---------|---------|---------------------|---------|
| **Python** | 3.10+ | `sudo apt install python3.10 python3.10-venv python3-pip` | Backend runtime |
| **Node.js** | 18.x+ | `curl -fsSL https://deb.nodesource.com/setup_18.x \| sudo -E bash - && sudo apt install nodejs` | Frontend build & runtime |
| **npm** | 9.x+ | Included with Node.js | Package manager |
| **Nginx** | Latest | `sudo apt install nginx` | Reverse proxy |
| **Git** | Latest | `sudo apt install git` | Version control |
| **Build Tools** | Latest | `sudo apt install build-essential` | Compile native modules |
| **Certbot** | Latest | `sudo apt install certbot python3-certbot-nginx` | SSL certificates |

### Global npm Packages

| Package | Version | Installation Command | Purpose |
|---------|---------|---------------------|---------|
| **PM2** | Latest | `sudo npm install -g pm2` | Process manager |
| **serve** | Latest | Auto-installed by PM2 | Serve static files |

---

## Application Dependencies

### Backend (Python)

All dependencies are listed in `backend/requirements.txt`:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Key Dependencies:**
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.0 | Web framework |
| uvicorn | 0.30.6 | ASGI server |
| supabase | 2.9.1 | Database client |
| openai | ≥2.15.0 | LLM API |
| langsmith | 0.7.3 | LLM observability |
| pydantic | 2.9.2 | Data validation |
| httpx | 0.27.2 | HTTP client |
| pypdf | 4.0.1 | PDF parsing |
| python-docx | 1.1.0 | Word document parsing |
| beautifulsoup4 | 4.12.3 | HTML parsing |

### Frontend (Node.js)

All dependencies are listed in `frontend/package.json`:

```bash
cd frontend
npm install
```

**Key Dependencies:**
| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.3.1 | UI framework |
| react-dom | 18.3.1 | React renderer |
| vite | 5.4.2 | Build tool |
| @supabase/supabase-js | 2.45.0 | Supabase client |
| react-router-dom | 6.26.0 | Routing |
| tailwindcss | 3.4.10 | CSS framework |
| typescript | 5.5.4 | Type checking |
| lucide-react | 0.446.0 | Icons |
| react-markdown | 10.1.0 | Markdown rendering |

---

## External Services Required

| Service | Type | Purpose | Sign-up URL |
|---------|------|---------|-------------|
| **Supabase** | Required | Database, Auth, Storage | https://supabase.com |
| **OpenRouter** | Required | LLM API | https://openrouter.ai |
| **LangSmith** | Required | LLM observability | https://smith.langchain.com |
| **Jina AI** | Optional | Reranking API | https://jina.ai/reranker |

### Supabase Configuration
- PostgreSQL database with pgvector extension
- Row-Level Security (RLS) policies configured
- Storage bucket for document uploads
- Authentication enabled

### API Keys Required
You'll need to obtain the following keys:

1. **Supabase** (3 keys):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

2. **LangSmith** (1 key):
   - `LANGSMITH_API_KEY`

3. **Jina AI** (Optional, 1 key):
   - `JINA_API_KEY`

4. **Encryption Key** (Generate locally):
   ```bash
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

---

## Installation Commands Summary

### Quick Install (Ubuntu 20.04+)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install build tools
sudo apt install build-essential libssl-dev libffi-dev python3-dev -y

# Install Nginx
sudo apt install nginx -y

# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Install PM2
sudo npm install -g pm2

# Clone repository
cd /var/www/
sudo git clone <your-repo-url> rag-app
cd rag-app
sudo chown -R $USER:$USER .

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install
npm run build
```

---

## Environment Variables

### Backend `.env` (8 variables)

```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
LANGSMITH_API_KEY=ls-...
LANGSMITH_PROJECT=rag-masterclass
SETTINGS_ENCRYPTION_KEY=xxx...
CORS_ORIGINS=["https://yourdomain.com"]
JINA_API_KEY=jina_...                    # Optional
JINA_RERANK_MODEL=jina-reranker-v2-base-multilingual
JINA_RERANK_ENABLED=false                # Optional
```

### Frontend `.env` (3 variables)

```env
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
VITE_API_URL=https://yourdomain.com/api
```

---

## Verification Commands

After installation, verify each component:

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check Node.js version
node --version     # Should be 18.x+

# Check npm version
npm --version      # Should be 9.x+

# Check PM2 installation
pm2 --version

# Check Nginx installation
nginx -v

# Check Certbot installation
certbot --version

# Test backend installation
cd backend
source venv/bin/activate
python -c "import fastapi, uvicorn, supabase; print('Backend dependencies OK')"

# Test frontend installation
cd frontend
npm list | grep react  # Should show React installed

# Verify build
ls -l dist/            # Should show built files
```

---

## File Structure After Installation

```
/var/www/rag-app/
├── backend/
│   ├── venv/                  # Python virtual environment
│   ├── app/                   # Application code
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Backend environment variables (create this)
├── frontend/
│   ├── node_modules/          # npm packages
│   ├── src/                   # Source code
│   ├── dist/                  # Built files (created by npm run build)
│   ├── package.json           # Frontend dependencies
│   └── .env                   # Frontend environment variables (create this)
├── logs/                      # Application logs (create this)
├── ecosystem.config.js        # PM2 configuration (create this)
├── DEPLOYMENT.md              # Full deployment guide
├── DEPLOYMENT_CHECKLIST.md    # Quick checklist
└── SERVER_REQUIREMENTS.md     # This file
```

---

## Storage Requirements Breakdown

| Component | Size | Description |
|-----------|------|-------------|
| Base OS | 5 GB | Ubuntu system files |
| Python + venv | 500 MB | Python runtime + packages |
| Node.js + npm | 200 MB | Node runtime |
| node_modules | 1-2 GB | Frontend dependencies |
| Application Code | 50 MB | Source code |
| Build Output | 5-10 MB | Frontend dist files |
| Logs | 1 GB | Application logs (grows over time) |
| Documents Storage | Variable | User-uploaded files (in Supabase) |
| **Total** | ~10 GB | Before user data |

**Recommendation**: Start with 50 GB to allow for growth.

---

## Network Requirements

### Bandwidth
- **Minimum**: 10 Mbps up/down
- **Recommended**: 100+ Mbps

### Firewall Rules (UFW)
```bash
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable
```

### DNS Configuration
Point your domain to the server:
```
A Record:     yourdomain.com    →  Your-Server-IP
A Record:     www.yourdomain.com →  Your-Server-IP
```

---

## Security Checklist

- [ ] Change default SSH port (optional but recommended)
- [ ] Disable root SSH login
- [ ] Set up SSH key authentication
- [ ] Enable UFW firewall
- [ ] Install fail2ban for brute force protection
- [ ] Keep system updated: `sudo apt update && sudo apt upgrade`
- [ ] Use strong passwords for all services
- [ ] Enable 2FA on Supabase, GitHub, etc.
- [ ] Regular backups of database and uploaded files
- [ ] Monitor logs regularly
- [ ] Set up SSL/TLS certificates (Let's Encrypt)
- [ ] Configure Content Security Policy headers

---

## Performance Optimization

### System Tuning
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize sysctl for web server
sudo tee -a /etc/sysctl.conf << EOF
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
EOF
sudo sysctl -p
```

### Nginx Optimization
Add to Nginx config:
```nginx
client_max_body_size 50M;        # Allow larger file uploads
gzip on;                         # Enable compression
gzip_types text/plain text/css application/json application/javascript;
```

---

## Backup Strategy

### What to Backup
1. **Database**: Supabase (automated backups available)
2. **Environment files**: `.env` files (store securely, encrypted)
3. **Uploaded documents**: Supabase Storage bucket
4. **Application code**: Git repository (already backed up)
5. **Nginx config**: `/etc/nginx/sites-available/rag-app`
6. **PM2 config**: `ecosystem.config.js`

### Backup Commands
```bash
# Backup .env files (encrypt before storing!)
tar -czf env-backup-$(date +%Y%m%d).tar.gz backend/.env frontend/.env

# Backup Nginx config
sudo cp /etc/nginx/sites-available/rag-app nginx-config-backup.conf

# Backup PM2 config
cp ecosystem.config.js pm2-config-backup.js
```

---

## Monitoring Recommendations

### Application Monitoring
- Use PM2 built-in monitoring: `pm2 monit`
- Set up PM2 logs rotation: `pm2 install pm2-logrotate`
- Monitor LangSmith dashboard for LLM traces

### Server Monitoring
- Install monitoring tools: `htop`, `iotop`, `nethogs`
- Set up uptime monitoring (UptimeRobot, Pingdom, etc.)
- Configure log rotation: `/etc/logrotate.d/`

### Alerts
- Set up email alerts for PM2 process crashes
- Monitor disk space: `df -h`
- Monitor memory usage: `free -h`
- Check SSL certificate expiry: `sudo certbot certificates`

---

## Cost Estimates (Monthly)

| Service | Tier | Estimated Cost |
|---------|------|----------------|
| **VPS/Server** | 2 CPU, 4 GB RAM | $10-20 |
| **Domain** | .com/.net | $10-15/year (~$1/month) |
| **Supabase** | Free tier (500 MB, 2 GB transfer) | $0 (or $25+ for Pro) |
| **OpenRouter** | Pay-per-use | Variable ($5-50+) |
| **LangSmith** | Developer tier | $0 (or $39+ for Team) |
| **Jina AI Reranker** | Free tier (10k calls/month) | $0 (or paid plans) |
| **Total** | Basic setup | **$15-35/month** |

*Costs may vary based on usage and provider. LLM API costs depend on usage volume.*

---

## Support & Documentation

- **Full Guide**: See `DEPLOYMENT.md`
- **Quick Start**: See `DEPLOYMENT_CHECKLIST.md`
- **Changes Made**: See `CLEANUP_SUMMARY.md`
- **Project Instructions**: See `CLAUDE.md`

---

**Ready to deploy?** Follow `DEPLOYMENT_CHECKLIST.md` for step-by-step instructions!
