# 🚀 Netlify Deployment Guide

## ✅ Ücretsiz Netlify'a Deploy Et!

### Yöntem 1: Netlify CLI (En Hızlı)

```bash
# 1. Netlify CLI kur
npm install -g netlify-cli

# 2. Netlify'a login ol
netlify login

# 3. Deploy et!
netlify deploy --prod

# Site URL'i alacaksın: https://your-site.netlify.app
```

### Yöntem 2: GitHub + Netlify (Otomatik Deploy)

#### Adım 1: GitHub'a Push
```bash
# Git repo oluştur
git init
git add .
git commit -m "Initial commit"

# GitHub'a push
git remote add origin https://github.com/your-username/grocery-pricing.git
git push -u origin main
```

#### Adım 2: Netlify'da Site Oluştur
1. https://app.netlify.com adresine git
2. "New site from Git" tıkla
3. GitHub repo'nu seç
4. Build ayarları:
   - **Build command**: `npm install && node scripts/seedDatabase.js`
   - **Publish directory**: `public`
   - **Functions directory**: `netlify/functions`

5. "Deploy site" tıkla!

#### Adım 3: Environment Variables (Opsiyonel)
Netlify dashboard → Site settings → Environment variables

```
EMAIL_SERVICE=gmail
EMAIL_USER=your@email.com
EMAIL_PASS=your_password
```

### Yöntem 3: Netlify Drop (Drag & Drop)

1. https://app.netlify.com/drop adresine git
2. Proje klasörünü sürükle-bırak
3. Deploy edildi! 🎉

---

## 🔧 Netlify Özellikleri

### ✅ Ücretsiz Plan İçeriği:
- 100 GB bandwidth/ay
- 300 build dakikası/ay
- HTTPS otomatik
- Custom domain
- Serverless functions (125,000 request/ay)
- Form handling
- Identity & authentication

### 📊 Limitler:
- Serverless function timeout: 10 saniye
- Function size: 50 MB
- Concurrent builds: 1

---

## 🌐 Custom Domain Bağlama

### Adım 1: Domain Al
- Namecheap, GoDaddy, veya Google Domains'den domain al

### Adım 2: Netlify'da Ayarla
1. Netlify dashboard → Domain settings
2. "Add custom domain" tıkla
3. Domain'i gir: `your-domain.com`

### Adım 3: DNS Ayarları
Domain sağlayıcında A record ekle:
```
Type: A
Name: @
Value: 75.2.60.5
TTL: 3600
```

CNAME record:
```
Type: CNAME
Name: www
Value: your-site.netlify.app
TTL: 3600
```

### Adım 4: SSL Aktif Et
Netlify otomatik Let's Encrypt SSL sertifikası verir!

---

## 🚀 Deployment Sonrası

### Site URL'leri:
- **Dashboard**: https://your-site.netlify.app
- **Analytics**: https://your-site.netlify.app/analytics.html
- **API**: https://your-site.netlify.app/.netlify/functions/products

### Test Et:
```bash
# Products API
curl https://your-site.netlify.app/.netlify/functions/products

# ML Prediction
curl https://your-site.netlify.app/.netlify/functions/ml/predict/1

# Pricing
curl https://your-site.netlify.app/.netlify/functions/pricing/product/1?strategy=combined
```

---

## 🔄 Otomatik Deploy

Her GitHub push'ta otomatik deploy olur!

```bash
git add .
git commit -m "Update features"
git push

# Netlify otomatik deploy eder!
```

### Deploy Preview:
- Her PR için otomatik preview URL
- Test et, merge et, production'a geç!

---

## 📊 Monitoring

### Netlify Analytics
- Sayfa görüntüleme
- Bandwidth kullanımı
- Function invocations
- Build süreleri

### Logs
```bash
# Netlify CLI ile logları gör
netlify functions:log
```

---

## 🐛 Troubleshooting

### Build Hatası
```bash
# Local'de test et
netlify dev

# Build'i local'de çalıştır
netlify build
```

### Function Timeout
- Netlify free plan: 10 saniye limit
- Uzun işlemler için background functions kullan

### Database
- SQLite Netlify'da çalışmaz (read-only filesystem)
- Alternatif: FaunaDB, Supabase, MongoDB Atlas (ücretsiz)

---

## 💰 Maliyet

### Ücretsiz Plan:
- **Maliyet**: $0/ay
- **Bandwidth**: 100 GB/ay
- **Build**: 300 dakika/ay
- **Functions**: 125,000 request/ay

### Pro Plan ($19/ay):
- **Bandwidth**: 400 GB/ay
- **Build**: 1000 dakika/ay
- **Functions**: 2,000,000 request/ay
- **Background functions**: Evet
- **Analytics**: Gelişmiş

---

## ✅ Deployment Checklist

- [ ] `netlify.toml` oluşturuldu
- [ ] Serverless functions eklendi
- [ ] API URL'leri güncellendi
- [ ] GitHub repo oluşturuldu
- [ ] Netlify'a bağlandı
- [ ] Build başarılı
- [ ] Site canlı
- [ ] Custom domain bağlandı (opsiyonel)
- [ ] SSL aktif
- [ ] Test edildi ✅

---

## 🎉 Başarıyla Deploy Edildi!

**Site URL**: https://your-site.netlify.app

Artık dünya çapında erişilebilir! 🌍

### Paylaş:
- Dashboard: https://your-site.netlify.app
- Analytics: https://your-site.netlify.app/analytics.html

**Tebrikler! 🎊**
