# Gerçek Veri Entegrasyonu Rehberi

## 🎯 Şu An Ne Var?

Sistem **simülasyon verileri** kullanıyor:
- Stok: Rastgele 50-200 arası
- Talep: Rastgele 0.8-1.2 arası
- Saat: Sistemden alıyor (gerçek)

## 🔌 Gerçek Hayatta Nasıl Olmalı?

### 1. **Stok Bilgisi** (Inventory System)

**Nereden Gelir?**
- Depo yönetim sistemi (WMS - Warehouse Management System)
- ERP sistemi (SAP, Oracle, vb.)
- Kendi veritabanınız

**Nasıl Entegre Edilir?**

```javascript
// Örnek: SAP entegrasyonu
const inventoryAPI = {
  endpoint: 'https://your-sap-system.com/api/inventory',
  apiKey: 'YOUR_API_KEY'
};

async function getStockLevel(productId) {
  const response = await fetch(
    `${inventoryAPI.endpoint}/stock/${productId}`,
    {
      headers: { 'Authorization': `Bearer ${inventoryAPI.apiKey}` }
    }
  );
  const data = await response.json();
  return data.quantity; // Gerçek stok miktarı
}
```

**Güncelleme:**
- Her satış olduğunda → Stok azalır
- Her tedarik geldiğinde → Stok artar
- Webhook ile otomatik güncelleme

---

### 2. **Talep Skoru** (Demand Score)

**Nereden Gelir?**
- POS (Kasa) sistemi satış verileri
- Web sitesi sepet verileri
- Geçmiş satış analizi

**Nasıl Hesaplanır?**

```javascript
// Son 1 saatteki satışlar / Ortalama saatlik satış
const demandScore = calculateDemand(productId);

function calculateDemand(productId) {
  const salesLastHour = getSalesCount(productId, '1 hour');
  const averageHourlySales = getAverageSales(productId, '7 days');
  
  return salesLastHour / averageHourlySales;
  // 1.0 = Normal
  // 1.5 = %50 daha fazla talep
  // 0.5 = %50 daha az talep
}
```

**Örnek Senaryolar:**
- Cumartesi öğleden sonra market dolu → Demand: 1.8
- Salı sabahı erken saatler → Demand: 0.6
- Yağmur yağıyor, herkes ekmek alıyor → Demand: 2.5

---

### 3. **Saat/Zaman Bilgisi** (Time-Based)

**Nereden Gelir?**
- Sistem saati (zaten var ✅)
- Timezone ayarları

**Kullanım:**
```javascript
const now = new Date();
const hour = now.getHours();

if (hour >= 17 && hour <= 20) {
  // Peak hours - Akşam yoğunluğu
  priceMultiplier *= 1.08;
}
```

---

### 4. **Rakip Fiyatları** (Competition)

**Nereden Gelir?**
- Web scraping (rakip siteleri)
- Fiyat karşılaştırma API'leri
- Manuel veri girişi

**Örnek API'ler:**
- Akakçe API
- Hepsiburada API
- Trendyol API

```javascript
async function getCompetitorPrice(productName) {
  const response = await fetch(
    `https://price-comparison-api.com/search?q=${productName}`
  );
  const data = await response.json();
  return data.averagePrice;
}
```

---

## 🔄 Gerçek Zamanlı Güncelleme

### Senaryo 1: Satış Olduğunda

```javascript
// POS sisteminden webhook gelir
app.post('/webhook/sale', async (req, res) => {
  const { productId, quantity } = req.body;
  
  // 1. Stoku güncelle
  await updateStockLevel(productId, -quantity);
  
  // 2. Talep skorunu yeniden hesapla
  const newDemand = await calculateDemand(productId);
  await updateDemandScore(productId, newDemand);
  
  // 3. Fiyatı otomatik güncelle
  const newPrice = await calculatePrice(productId);
  await updateProductPrice(productId, newPrice);
  
  res.json({ success: true });
});
```

### Senaryo 2: Her Saat Başı Otomatik

```javascript
// Cron job - Her saat başı çalışır
cron.schedule('0 * * * *', async () => {
  console.log('Hourly price update started...');
  
  const products = await getAllProducts();
  
  for (const product of products) {
    const newPrice = await calculatePrice(product.id, 'combined');
    await updateProductPrice(product.id, newPrice);
  }
  
  console.log('Prices updated!');
});
```

---

## 📊 Örnek Veri Akışı

```
┌─────────────────┐
│   POS Sistemi   │ ← Müşteri ürün aldı
└────────┬────────┘
         │
         ↓ (Webhook)
┌─────────────────┐
│  Dynamic Pricing│
│     System      │
└────────┬────────┘
         │
         ├→ Stok güncelle (137 → 136)
         ├→ Talep hesapla (1.0 → 1.2)
         ├→ Fiyat hesapla ($89.99 → $94.49)
         └→ Veritabanına kaydet
```

---

## 🚀 Hızlı Başlangıç

### Adım 1: Stok Entegrasyonu

```javascript
// src/integrations/inventory.js
const db = require('../database/db');

async function syncInventory() {
  // Kendi sisteminizdeki stok API'sine bağlanın
  const stockData = await yourInventorySystem.getAll();
  
  for (const item of stockData) {
    await db.updateStockLevel(item.productId, item.quantity);
  }
}

// Her 5 dakikada bir senkronize et
setInterval(syncInventory, 5 * 60 * 1000);
```

### Adım 2: Satış Takibi

```javascript
// src/integrations/sales.js
const db = require('../database/db');

async function recordSale(productId, quantity) {
  // Satışı kaydet
  await db.recordSale(productId, quantity);
  
  // Stoku azalt
  await db.updateStockLevel(productId, -quantity);
  
  // Talebi güncelle
  const demand = await calculateDemand(productId);
  await db.updateDemandScore(productId, demand);
}
```

### Adım 3: Otomatik Fiyat Güncelleme

```javascript
// src/jobs/priceUpdater.js
const cron = require('node-cron');
const PricingEngine = require('../pricing/pricingEngine');

// Her saat başı
cron.schedule('0 * * * *', async () => {
  const engine = new PricingEngine();
  const products = await db.getAllProducts();
  
  for (const product of products) {
    const pricing = engine.calculatePrice(product, 'combined');
    await db.updateProductPrice(product.id, pricing.price);
  }
});
```

---

## 🎯 Özet

**Şu an:** Simülasyon (test için)
**Gerçekte:** 
1. **Stok** → Depo sisteminizden
2. **Talep** → Satış verilerinizden
3. **Saat** → Sistem saati (zaten var)
4. **Rakip** → Web scraping veya API

**Entegrasyon Sırası:**
1. ✅ Sistem saati (zaten çalışıyor)
2. 🔄 Stok sistemi entegrasyonu
3. 🔄 POS/Satış sistemi entegrasyonu
4. 🔄 Rakip fiyat takibi (opsiyonel)

Hangi sisteminiz var? Ona göre entegrasyon kodu yazabilirim!
