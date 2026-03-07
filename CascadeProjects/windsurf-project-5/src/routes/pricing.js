const express = require('express');
const router = express.Router();
const { getAllProducts, getProductsByCategory, updateProductPrice } = require('../database/db');
const PricingEngine = require('../pricing/pricingEngine');

const pricingEngine = new PricingEngine();

router.post('/calculate', async (req, res) => {
  try {
    const { productIds, category, strategy = 'combined', options = {} } = req.body;
    let products;

    if (productIds && Array.isArray(productIds)) {
      const allProducts = await getAllProducts();
      products = allProducts.filter(p => productIds.includes(p.id));
    } else if (category) {
      products = await getProductsByCategory(category);
    } else {
      products = await getAllProducts();
    }

    const results = pricingEngine.calculateBulkPricing(products, strategy, options);

    res.json({
      success: true,
      count: results.length,
      strategy,
      data: results
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/update-all', async (req, res) => {
  try {
    const { category, strategy = 'combined', options = {} } = req.body;
    let products;

    if (category) {
      products = await getProductsByCategory(category);
    } else {
      products = await getAllProducts();
    }

    const results = [];
    for (const product of products) {
      const pricing = pricingEngine.calculatePrice(product, strategy, options);
      await updateProductPrice(product.id, pricing.price, strategy, pricing.factors || {});
      results.push({
        productId: product.id,
        title: product.title,
        oldPrice: product.current_price,
        newPrice: pricing.price,
        change: pricing.price - product.current_price
      });
    }

    res.json({
      success: true,
      count: results.length,
      strategy,
      data: results
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/strategies', (req, res) => {
  res.json({
    success: true,
    data: {
      strategies: [
        {
          name: 'demand',
          description: 'Talep bazlı fiyatlandırma - Yüksek talep = fiyat artışı',
          factors: ['demand_score']
        },
        {
          name: 'time',
          description: 'Zaman bazlı fiyatlandırma - Peak hours ve hafta sonu',
          factors: ['hour', 'day_of_week', 'category']
        },
        {
          name: 'inventory',
          description: 'Stok bazlı fiyatlandırma - Düşük stok = fiyat artışı',
          factors: ['stock_level']
        },
        {
          name: 'rating',
          description: 'Rating bazlı fiyatlandırma - Yüksek rating = premium',
          factors: ['rating', 'review_count']
        },
        {
          name: 'competition',
          description: 'Rekabet bazlı fiyatlandırma - Rakip fiyatlarına göre',
          factors: ['competitor_price']
        },
        {
          name: 'combined',
          description: 'Kombine strateji - Tüm faktörleri ağırlıklı olarak kullanır',
          factors: ['all'],
          weights: {
            demand: 0.30,
            time: 0.20,
            inventory: 0.25,
            rating: 0.15,
            competition: 0.10
          }
        }
      ]
    }
  });
});

router.get('/analytics', async (req, res) => {
  try {
    const products = await getAllProducts();
    
    const analytics = {
      totalProducts: products.length,
      averageBasePrice: 0,
      averageCurrentPrice: 0,
      averageDiscount: 0,
      priceRanges: {
        under10: 0,
        '10to50': 0,
        '50to100': 0,
        over100: 0
      },
      byCategory: {}
    };

    let totalBase = 0;
    let totalCurrent = 0;

    products.forEach(p => {
      totalBase += p.base_price;
      totalCurrent += p.current_price;

      if (p.current_price < 10) analytics.priceRanges.under10++;
      else if (p.current_price < 50) analytics.priceRanges['10to50']++;
      else if (p.current_price < 100) analytics.priceRanges['50to100']++;
      else analytics.priceRanges.over100++;

      if (!analytics.byCategory[p.category]) {
        analytics.byCategory[p.category] = {
          count: 0,
          avgPrice: 0,
          totalPrice: 0
        };
      }
      analytics.byCategory[p.category].count++;
      analytics.byCategory[p.category].totalPrice += p.current_price;
    });

    analytics.averageBasePrice = (totalBase / products.length).toFixed(2);
    analytics.averageCurrentPrice = (totalCurrent / products.length).toFixed(2);
    analytics.averageDiscount = (((totalBase - totalCurrent) / totalBase) * 100).toFixed(2);

    Object.keys(analytics.byCategory).forEach(cat => {
      const catData = analytics.byCategory[cat];
      catData.avgPrice = (catData.totalPrice / catData.count).toFixed(2);
      delete catData.totalPrice;
    });

    res.json({
      success: true,
      data: analytics
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;
