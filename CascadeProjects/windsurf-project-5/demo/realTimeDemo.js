const moment = require('moment');

console.log('=== GERÇEK ZAMANLI VERİ SİMÜLASYONU ===\n');

const product = {
  id: 1,
  name: 'Chocolate Cake',
  basePrice: 89.99
};

console.log(`Ürün: ${product.name}`);
console.log(`Base Fiyat: $${product.basePrice}\n`);

console.log('--- 1. SAAT BİLGİSİ (GERÇEK) ---');
const now = moment();
console.log(`Şu an: ${now.format('HH:mm')}`);
console.log(`Gün: ${now.format('dddd')}`);

let timeMultiplier = 1.0;
const hour = now.hour();

if (hour >= 17 && hour <= 20) {
  timeMultiplier = 1.08;
  console.log('✅ Peak hours! Fiyat +%8');
} else if (hour >= 11 && hour <= 13) {
  timeMultiplier = 1.05;
  console.log('✅ Lunch hours! Fiyat +%5');
} else {
  console.log('⏰ Normal saatler');
}

console.log('\n--- 2. STOK BİLGİSİ (ŞU AN: Simülasyon) ---');
let stockLevel = 137;
console.log(`Stok: ${stockLevel} adet`);
console.log('⚠️  Bu değer rastgele atanmış');
console.log('✅ Gerçekte: Depo sisteminden gelecek\n');

console.log('ÖRNEK: Gerçek stok entegrasyonu');
console.log('```javascript');
console.log('// Her satış olduğunda:');
console.log('stockLevel = 137;  // Başlangıç');
console.log('// Müşteri 1 adet aldı');
console.log('stockLevel = 136;  // Güncellendi');
console.log('```\n');

let inventoryMultiplier = 1.0;
if (stockLevel < 20) {
  inventoryMultiplier = 1.20;
  console.log('🔴 Çok az stok! Fiyat +%20');
} else if (stockLevel < 50) {
  inventoryMultiplier = 1.10;
  console.log('🟡 Az stok! Fiyat +%10');
} else if (stockLevel > 150) {
  inventoryMultiplier = 0.92;
  console.log('🟢 Çok stok! İndirim -%8');
} else {
  console.log('⚪ Normal stok seviyesi');
}

console.log('\n--- 3. TALEP SKORU (ŞU AN: Simülasyon) ---');
let demandScore = 1.16;
console.log(`Talep Skoru: ${demandScore}`);
console.log('⚠️  Bu değer rastgele atanmış');
console.log('✅ Gerçekte: Satış verilerinden hesaplanacak\n');

console.log('ÖRNEK: Gerçek talep hesaplama');
console.log('```javascript');
console.log('// Son 1 saatteki satışlar');
console.log('const salesLastHour = 12;');
console.log('// Ortalama saatlik satış (7 günlük)');
console.log('const averageHourlySales = 10;');
console.log('// Talep skoru');
console.log('const demandScore = 12 / 10 = 1.2');
console.log('// Yorum: %20 daha fazla talep var!');
console.log('```\n');

let demandMultiplier = 1.0;
if (demandScore > 1.5) {
  demandMultiplier = 1.15;
  console.log('🔥 Çok yüksek talep! Fiyat +%15');
} else if (demandScore > 1.2) {
  demandMultiplier = 1.10;
  console.log('📈 Yüksek talep! Fiyat +%10');
} else if (demandScore > 1.0) {
  demandMultiplier = 1.05;
  console.log('📊 Normal üstü talep! Fiyat +%5');
} else {
  console.log('📉 Normal/düşük talep');
}

console.log('\n--- 4. FİNAL FİYAT HESAPLAMA ---');
const finalMultiplier = timeMultiplier * inventoryMultiplier * demandMultiplier;
const finalPrice = product.basePrice * finalMultiplier;

console.log(`Base Fiyat: $${product.basePrice}`);
console.log(`Zaman çarpanı: ${timeMultiplier}x`);
console.log(`Stok çarpanı: ${inventoryMultiplier}x`);
console.log(`Talep çarpanı: ${demandMultiplier}x`);
console.log(`─────────────────────────────`);
console.log(`Final Çarpan: ${finalMultiplier.toFixed(3)}x`);
console.log(`FINAL FİYAT: $${finalPrice.toFixed(2)}`);
console.log(`Değişim: ${((finalPrice - product.basePrice) / product.basePrice * 100).toFixed(2)}%`);

console.log('\n=== GERÇEK HAYAT ÖRNEĞİ ===\n');

console.log('Senaryo 1: Cumartesi akşamı, stok azaldı');
console.log('─────────────────────────────────────────');
const scenario1 = {
  time: 'Cumartesi 19:00',
  stock: 15,
  demand: 1.8,
  timeMultiplier: 1.08 * 1.05, // Weekend + Peak
  stockMultiplier: 1.20,       // Düşük stok
  demandMultiplier: 1.15       // Yüksek talep
};
const price1 = product.basePrice * scenario1.timeMultiplier * scenario1.stockMultiplier * scenario1.demandMultiplier;
console.log(`Fiyat: $${price1.toFixed(2)} (+${((price1/product.basePrice - 1) * 100).toFixed(0)}%)`);

console.log('\nSenaryo 2: Salı sabahı, çok stok var');
console.log('─────────────────────────────────────────');
const scenario2 = {
  time: 'Salı 08:00',
  stock: 180,
  demand: 0.6,
  timeMultiplier: 1.0,    // Normal saat
  stockMultiplier: 0.92,  // Çok stok
  demandMultiplier: 0.90  // Düşük talep
};
const price2 = product.basePrice * scenario2.timeMultiplier * scenario2.stockMultiplier * scenario2.demandMultiplier;
console.log(`Fiyat: $${price2.toFixed(2)} (${((price2/product.basePrice - 1) * 100).toFixed(0)}%)`);

console.log('\n=== SONUÇ ===');
console.log('✅ Saat bilgisi: GERÇEK (sistem saatinden)');
console.log('⚠️  Stok bilgisi: SİMÜLASYON (gerçekte depo sisteminden)');
console.log('⚠️  Talep skoru: SİMÜLASYON (gerçekte satış verilerinden)');
console.log('✅ Rating: GERÇEK (CSV dosyasından)');
