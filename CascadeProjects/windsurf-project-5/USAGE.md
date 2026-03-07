# Kullanım Kılavuzu

## Kurulum

```bash
# Bağımlılıkları yükle
npm install

# CSV'yi parse et
npm run parse-csv

# Veritabanını oluştur ve doldur
npm run seed-db

# Sunucuyu başlat
npm start
```

## API Kullanımı

### 1. Tüm Ürünleri Listele

```bash
curl http://localhost:3000/api/products
```

Parametreler:
- `category`: Kategoriye göre filtrele
- `limit`: Maksimum ürün sayısı
- `offset`: Başlangıç noktası

### 2. Tek Ürün İçin Dinamik Fiyat Hesapla

```bash
curl http://localhost:3000/api/products/1/price?strategy=combined
```

Stratejiler:
- `combined`: Tüm faktörleri kombine eder (önerilen)
- `demand`: Sadece talep bazlı
- `time`: Sadece zaman bazlı
- `inventory`: Sadece stok bazlı
- `rating`: Sadece rating bazlı
- `competition`: Sadece rekabet bazlı

### 3. Toplu Fiyat Hesaplama

```bash
curl -X POST http://localhost:3000/api/pricing/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Bakery & Desserts",
    "strategy": "combined"
  }'
```

### 4. Fiyat Geçmişi

```bash
curl http://localhost:3000/api/products/1/price-history?limit=20
```

### 5. Fiyat Simülasyonu (7 günlük)

```bash
curl http://localhost:3000/api/products/1/simulate?days=7
```

### 6. Stok Güncelleme

```bash
curl -X PATCH http://localhost:3000/api/products/1/stock \
  -H "Content-Type: application/json" \
  -d '{"stockLevel": 25}'
```

### 7. Talep Skoru Güncelleme

```bash
curl -X PATCH http://localhost:3000/api/products/1/demand \
  -H "Content-Type: application/json" \
  -d '{"demandScore": 1.5}'
```

### 8. Tüm Fiyatları Güncelle

```bash
curl -X POST http://localhost:3000/api/pricing/update-all \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "combined",
    "category": "Bakery & Desserts"
  }'
```

### 9. Analytics

```bash
curl http://localhost:3000/api/pricing/analytics
```

## Fiyatlandırma Stratejileri Detayları

### Combined Strategy (Önerilen)

Tüm faktörleri ağırlıklı olarak kullanır:
- Talep: %30
- Stok: %25
- Zaman: %20
- Rating: %15
- Rekabet: %10

**Örnek Senaryo:**
- Yüksek talep (1.5x) → +15% fiyat artışı
- Düşük stok (30 adet) → +10% fiyat artışı
- Peak hours (18:00) → +8% fiyat artışı
- Yüksek rating (4.7/5) → +5% fiyat artışı
- **Toplam:** ~+38% fiyat artışı (ağırlıklı ortalama ile ~+12%)

### Demand-Based Strategy

Talep skoruna göre fiyatlandırma:
- Demand > 1.5 → +15%
- Demand > 1.2 → +10%
- Demand > 1.0 → +5%
- Demand < 0.7 → -10%
- Demand < 0.9 → -5%

### Time-Based Strategy

Saat ve gün bazlı fiyatlandırma:
- Peak hours (17:00-20:00) → +8%
- Lunch hours (11:00-13:00) → +5%
- Morning rush (06:00-09:00) → +3%
- Hafta sonu → +5%
- Bakery ürünleri sabah (06:00-10:00) → +10%

### Inventory-Based Strategy

Stok seviyesine göre:
- Stok < 20 → +20% (scarcity premium)
- Stok < 50 → +10%
- Stok > 150 → -8% (clearance)
- Stok > 120 → -5%

### Rating-Based Strategy

Müşteri değerlendirmelerine göre:
- Rating ≥ 4.5 + 1000+ reviews → +8%
- Rating ≥ 4.5 + 100+ reviews → +5%
- Rating ≥ 4.0 + 500+ reviews → +3%
- Rating < 3.5 → -5%

### Competition-Based Strategy

Rakip fiyatlarına göre (opsiyonel):
- Rakip fiyatı %10+ yüksek → +8%
- Rakip fiyatı %5+ yüksek → +5%
- Rakip fiyatı %10+ düşük → -5%
- Rakip fiyatı %5+ düşük → -2%

## Web Dashboard

Dashboard'a tarayıcıdan erişin:
```
http://localhost:3000
```

Özellikler:
- Gerçek zamanlı istatistikler
- Kategori bazlı filtreleme
- Strateji seçimi
- Toplu fiyat güncelleme
- Görsel fiyat karşılaştırması

## Örnek Kullanım Senaryoları

### Senaryo 1: Sabah Bakery Ürünleri

```javascript
// Sabah 08:00, Bakery kategorisi
// Yüksek talep + sabah premium
const result = await fetch('/api/products/1/price?strategy=combined');
// Beklenen: Base fiyat + %15-20 artış
```

### Senaryo 2: Düşük Stok Uyarısı

```javascript
// Stok 15'e düştü
await fetch('/api/products/1/stock', {
  method: 'PATCH',
  body: JSON.stringify({ stockLevel: 15 })
});

// Fiyat otomatik artacak (+20%)
```

### Senaryo 3: Hafta Sonu Peak Hours

```javascript
// Cumartesi 19:00
// Weekend + Peak hours kombinasyonu
// Beklenen: +13% fiyat artışı
```

## Test

```bash
npm test
```

## Geliştirme Modu

```bash
npm run dev
```

Nodemon ile otomatik yeniden başlatma aktif olur.
