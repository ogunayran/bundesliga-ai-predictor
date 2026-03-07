# 🚀 Deployment Guide - Grocery Dynamic Pricing System

## 📋 İçindekiler
- [Docker ile Deployment](#docker-ile-deployment)
- [Production Deployment](#production-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)

---

## 🐳 Docker ile Deployment

### Ön Gereksinimler
- Docker (v20.10+)
- Docker Compose (v2.0+)

### Hızlı Başlangıç

#### 1. Basit Deployment (Sadece Uygulama)
```bash
# Docker image oluştur
docker build -t grocery-pricing:latest .

# Container'ı çalıştır
docker run -d \
  --name grocery-pricing \
  -p 3000:3000 \
  -v $(pwd)/data:/app/data \
  grocery-pricing:latest

# Uygulamaya eriş
open http://localhost:3000
```

#### 2. Docker Compose ile Deployment (Önerilen)
```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları izle
docker-compose logs -f

# Servisleri durdur
docker-compose down

# Servisleri yeniden başlat
docker-compose restart
```

#### 3. Production Deployment (Nginx ile)
```bash
# Nginx ile birlikte başlat
docker-compose --profile production up -d

# Nginx üzerinden eriş
open http://localhost
```

### Environment Variables

`.env` dosyası oluştur:
```bash
cp .env.example .env
```

Düzenle:
```env
NODE_ENV=production
PORT=3000

# Email (Opsiyonel)
EMAIL_SERVICE=gmail
EMAIL_USER=your@email.com
EMAIL_PASS=your_app_password
```

### Docker Komutları

```bash
# Container durumunu kontrol et
docker ps

# Container loglarını gör
docker logs grocery-pricing-app

# Container'a bağlan
docker exec -it grocery-pricing-app sh

# Container'ı yeniden başlat
docker restart grocery-pricing-app

# Container'ı durdur ve sil
docker stop grocery-pricing-app
docker rm grocery-pricing-app

# Image'ı sil
docker rmi grocery-pricing:latest

# Tüm verileri temizle
docker-compose down -v
```

---

## 🌐 Production Deployment

### 1. AWS EC2 Deployment

#### EC2 Instance Oluştur
```bash
# t2.micro veya t3.small önerilen
# Ubuntu 22.04 LTS
```

#### Sunucuya Bağlan
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

#### Docker Kur
```bash
# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Docker Compose kur
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Uygulamayı Deploy Et
```bash
# Kodu klonla
git clone your-repo-url
cd grocery-dynamic-pricing

# Environment değişkenlerini ayarla
cp .env.example .env
nano .env

# Deploy et
docker-compose --profile production up -d
```

#### Firewall Ayarları
```bash
# AWS Security Group'ta portları aç
# - 80 (HTTP)
# - 443 (HTTPS)
# - 22 (SSH)
```

### 2. DigitalOcean Deployment

#### Droplet Oluştur
```bash
# Docker Droplet seç (Ubuntu + Docker pre-installed)
# $6/month plan yeterli
```

#### Deploy
```bash
# SSH ile bağlan
ssh root@your-droplet-ip

# Kodu klonla ve deploy et
git clone your-repo-url
cd grocery-dynamic-pricing
docker-compose up -d
```

### 3. Heroku Deployment

#### Heroku CLI Kur
```bash
brew install heroku/brew/heroku
heroku login
```

#### Deploy
```bash
# Heroku app oluştur
heroku create grocery-pricing-app

# Container Registry kullan
heroku container:login

# Build ve push
heroku container:push web
heroku container:release web

# Uygulamayı aç
heroku open
```

### 4. Google Cloud Run Deployment

```bash
# Google Cloud SDK kur
gcloud init

# Container Registry'ye push
gcloud builds submit --tag gcr.io/PROJECT_ID/grocery-pricing

# Cloud Run'a deploy
gcloud run deploy grocery-pricing \
  --image gcr.io/PROJECT_ID/grocery-pricing \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 🔒 SSL/HTTPS Kurulumu

### Let's Encrypt ile Ücretsiz SSL

```bash
# Certbot kur
sudo apt-get update
sudo apt-get install certbot

# SSL sertifikası al
sudo certbot certonly --standalone -d your-domain.com

# Nginx config'i güncelle
# nginx/nginx.conf dosyasındaki HTTPS bölümünü aktif et

# Nginx'i yeniden başlat
docker-compose restart nginx
```

### SSL Otomatik Yenileme
```bash
# Crontab ekle
sudo crontab -e

# Her gün saat 2'de kontrol et
0 2 * * * certbot renew --quiet && docker-compose restart nginx
```

---

## 📊 Monitoring & Maintenance

### Health Check
```bash
# Container sağlık durumu
docker ps

# API health check
curl http://localhost:3000/api

# Detaylı health check
docker inspect --format='{{.State.Health.Status}}' grocery-pricing-app
```

### Logs
```bash
# Tüm loglar
docker-compose logs

# Sadece app logları
docker-compose logs app

# Son 100 satır
docker-compose logs --tail=100 app

# Canlı takip
docker-compose logs -f app
```

### Backup

#### Database Backup
```bash
# Manuel backup
docker exec grocery-pricing-app sqlite3 /app/data/grocery.db ".backup /app/data/backup.db"
docker cp grocery-pricing-app:/app/data/backup.db ./backups/

# Otomatik backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec grocery-pricing-app sqlite3 /app/data/grocery.db ".backup /app/data/backup_$DATE.db"
docker cp grocery-pricing-app:/app/data/backup_$DATE.db ./backups/
find ./backups -name "backup_*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# Crontab'a ekle (her gün saat 3'te)
0 3 * * * /path/to/backup.sh
```

### Updates

```bash
# Kodu güncelle
git pull

# Image'ı yeniden oluştur
docker-compose build

# Servisleri yeniden başlat (zero-downtime)
docker-compose up -d --no-deps --build app

# Eski image'ları temizle
docker image prune -f
```

### Performance Monitoring

```bash
# Resource kullanımı
docker stats grocery-pricing-app

# Disk kullanımı
docker system df

# Container detayları
docker inspect grocery-pricing-app
```

---

## 🔧 Troubleshooting

### Container Başlamıyor
```bash
# Logları kontrol et
docker-compose logs app

# Port kullanımda mı?
lsof -i :3000

# Container'ı yeniden oluştur
docker-compose down
docker-compose up -d --force-recreate
```

### Database Hataları
```bash
# Database dosyasını kontrol et
ls -la data/

# Yeni database oluştur
docker exec grocery-pricing-app node scripts/seedDatabase.js
```

### Memory Issues
```bash
# Memory limiti ayarla (docker-compose.yml)
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

---

## 📈 Scaling

### Horizontal Scaling
```bash
# Birden fazla instance çalıştır
docker-compose up -d --scale app=3

# Load balancer ekle (nginx)
# nginx.conf'ta upstream'e birden fazla server ekle
```

### Vertical Scaling
```bash
# Daha güçlü sunucu kullan
# EC2: t2.micro → t2.small → t2.medium
# Memory ve CPU artır
```

---

## 🌍 Domain Bağlama

### DNS Ayarları
```bash
# A Record ekle
Type: A
Name: @
Value: YOUR_SERVER_IP
TTL: 3600

# www subdomain
Type: CNAME
Name: www
Value: your-domain.com
TTL: 3600
```

### Nginx Config Güncelle
```nginx
server_name your-domain.com www.your-domain.com;
```

---

## 💰 Maliyet Tahmini

### AWS EC2
- **t2.micro** (Free Tier): $0/month (1 yıl)
- **t3.small**: ~$15/month
- **t3.medium**: ~$30/month

### DigitalOcean
- **Basic Droplet**: $6/month
- **Professional**: $12/month

### Heroku
- **Free**: $0/month (sınırlı)
- **Hobby**: $7/month
- **Standard**: $25/month

### Google Cloud Run
- **Pay-as-you-go**: ~$5-20/month (kullanıma göre)

---

## 📞 Support

Sorun yaşarsan:
1. Logları kontrol et: `docker-compose logs`
2. Health check yap: `curl http://localhost:3000/api`
3. Container'ı yeniden başlat: `docker-compose restart`

**Dashboard:** http://your-domain.com
**Analytics:** http://your-domain.com/analytics.html
**API Docs:** http://your-domain.com/api

---

## ✅ Deployment Checklist

- [ ] `.env` dosyası oluşturuldu
- [ ] Email ayarları yapıldı (opsiyonel)
- [ ] Docker ve Docker Compose kuruldu
- [ ] Firewall portları açıldı (80, 443)
- [ ] SSL sertifikası alındı
- [ ] Domain DNS ayarları yapıldı
- [ ] Backup script kuruldu
- [ ] Monitoring ayarlandı
- [ ] Health check çalışıyor
- [ ] Test edildi ve çalışıyor ✅

**Başarıyla deploy edildi! 🎉**
