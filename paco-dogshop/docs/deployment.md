# Deployment Guide: AWS Lightsail

## Prerequisites
- AWS account with Lightsail access
- Domain name (pacodogshop.com) configured
- Node.js 20+ on the Lightsail instance

## Steps

### 1. Create a Lightsail Instance
- Go to AWS Lightsail console
- Create a new instance: **OS Only > Ubuntu 22.04**
- Choose plan: $5/month (1 GB RAM) is sufficient for this project
- Name: `paco-dogshop`

### 2. Connect to Instance
```bash
ssh -i your-key.pem ubuntu@your-instance-ip
```

### 3. Install Node.js
```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 4. Clone and Setup
```bash
git clone https://github.com/jose-pinedadelgado/paco-dogshop.git
cd paco-dogshop
npm install --production
cp .env.example .env
# Edit .env with production values
```

### 5. Setup Database
```bash
npm run db:migrate
npm run db:seed
```

### 6. Process Manager (PM2)
```bash
sudo npm install -g pm2
pm2 start src/app.js --name paco-dogshop
pm2 startup
pm2 save
```

### 7. Nginx Reverse Proxy
```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/pacodogshop`:
```nginx
server {
    listen 80;
    server_name pacodogshop.com www.pacodogshop.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/pacodogshop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d pacodogshop.com -d www.pacodogshop.com
```

### 9. DNS Configuration
Point your domain to the Lightsail static IP:
- A record: `pacodogshop.com` -> `<static-ip>`
- A record: `www.pacodogshop.com` -> `<static-ip>`

## Updating
```bash
cd paco-dogshop
git pull
npm install --production
npm run db:migrate
pm2 restart paco-dogshop
```
