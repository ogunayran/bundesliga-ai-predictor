const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const { initDatabase } = require('./database/db');
const productsRouter = require('./routes/products');
const pricingRouter = require('./routes/pricing');
const analyticsRouter = require('./routes/analytics');
const mlRouter = require('./routes/ml').router;
const abTestRouter = require('./routes/abtest');
const emailService = require('./services/emailReports');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, '../public')));

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../public/index.html'));
});

app.get('/api', (req, res) => {
  res.json({
    success: true,
    message: 'Grocery Dynamic Pricing API',
    version: '1.0.0',
    endpoints: {
      products: {
        'GET /api/products': 'Tüm ürünleri listele',
        'GET /api/products/:id': 'Ürün detayı',
        'GET /api/products/:id/price': 'Dinamik fiyat hesapla',
        'GET /api/products/:id/price-history': 'Fiyat geçmişi',
        'GET /api/products/:id/simulate': 'Fiyat simülasyonu',
        'POST /api/products/:id/update-price': 'Fiyatı güncelle',
        'PATCH /api/products/:id/stock': 'Stok güncelle',
        'PATCH /api/products/:id/demand': 'Talep skoru güncelle',
        'GET /api/products/categories': 'Kategorileri listele'
      },
      pricing: {
        'POST /api/pricing/calculate': 'Toplu fiyat hesaplama',
        'POST /api/pricing/update-all': 'Tüm fiyatları güncelle',
        'GET /api/pricing/strategies': 'Fiyatlandırma stratejileri',
        'GET /api/pricing/analytics': 'Fiyatlandırma analitiği'
      }
    }
  });
});

app.use('/api/products', productsRouter);
app.use('/api/pricing', pricingRouter);
app.use('/api/analytics', analyticsRouter);
app.use('/api/ml', mlRouter);
app.use('/api/abtest', abTestRouter);

app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: err.message
  });
});

app.use((req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found'
  });
});

async function startServer() {
  try {
    await initDatabase();
    console.log('✓ Database initialized');

    app.listen(PORT, () => {
      console.log(`\n🚀 Server running on http://localhost:${PORT}`);
      console.log(`📊 API Documentation: http://localhost:${PORT}/api`);
      console.log(`🎨 Dashboard: http://localhost:${PORT}`);
      console.log(`📈 Analytics: http://localhost:${PORT}/analytics.html`);
      console.log('\n🤖 New Features:');
      console.log('  - Machine Learning: /api/ml/*');
      console.log('  - A/B Testing: /api/abtest/*');
      console.log('  - Email Reports: Configure in .env');
      console.log('\n💡 To enable email reports, add to .env:');
      console.log('  EMAIL_SERVICE=gmail');
      console.log('  EMAIL_USER=your@email.com');
      console.log('  EMAIL_PASS=your_password');
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();
