# Grocery Dynamic Pricing System

Gelişmiş dinamik fiyatlandırma sistemi - GroceryDataset.csv verisi üzerine kurulu.

## Özellikler

- **Çoklu Fiyatlandırma Stratejileri**
  - Talep bazlı (Demand-based)
  - Zaman bazlı (Time-based) 
  - Stok bazlı (Inventory-based)
  - Rating bazlı (Rating-based)
  - Rekabet bazlı (Competition-based)

- **Real-time Fiyat Hesaplama**
- **Fiyat Geçmişi Takibi**
- **Analytics & Raporlama**
- **REST API**

## Kurulum

```bash
npm install
npm run parse-csv
npm run seed-db
npm start
```

## API Endpoints

- `GET /api/products` - Tüm ürünleri listele
- `GET /api/products/:id` - Ürün detayı
- `GET /api/products/:id/price` - Dinamik fiyat hesapla
- `GET /api/categories` - Kategorileri listele
- `POST /api/pricing/calculate` - Toplu fiyat hesaplama
- `GET /api/analytics/price-history/:id` - Fiyat geçmişi

## Fiyatlandırma Stratejileri

Sistem aşağıdaki faktörleri kullanarak dinamik fiyat hesaplar:

1. **Talep**: Yüksek talep = %5-15 artış
2. **Stok Seviyesi**: Düşük stok = %10-20 artış
3. **Zaman**: Peak hours = %5-10 artış
4. **Rating**: Yüksek rating = %5 premium
5. **Sezon**: Sezonluk ürünler için özel fiyatlandırma
