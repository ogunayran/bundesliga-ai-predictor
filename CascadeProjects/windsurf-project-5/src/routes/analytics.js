const express = require('express');
const router = express.Router();
const { db } = require('../database/db');

router.get('/price-trends', async (req, res) => {
  try {
    const { productId, days = 7 } = req.query;
    
    const query = productId 
      ? `SELECT 
          DATE(timestamp) as date,
          AVG(price) as avg_price,
          MIN(price) as min_price,
          MAX(price) as max_price,
          COUNT(*) as price_changes
         FROM price_history 
         WHERE product_id = ? 
         AND timestamp >= datetime('now', '-${days} days')
         GROUP BY DATE(timestamp)
         ORDER BY date DESC`
      : `SELECT 
          DATE(timestamp) as date,
          AVG(price) as avg_price,
          MIN(price) as min_price,
          MAX(price) as max_price,
          COUNT(*) as price_changes
         FROM price_history 
         WHERE timestamp >= datetime('now', '-${days} days')
         GROUP BY DATE(timestamp)
         ORDER BY date DESC`;

    const params = productId ? [productId] : [];

    db.all(query, params, (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }
      
      res.json({
        success: true,
        days,
        data: rows
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/category-performance', async (req, res) => {
  try {
    const query = `
      SELECT 
        p.category,
        COUNT(DISTINCT p.id) as product_count,
        AVG(p.current_price) as avg_price,
        AVG(p.base_price) as avg_base_price,
        AVG((p.current_price - p.base_price) / p.base_price * 100) as avg_markup,
        SUM(CASE WHEN p.stock_level < 20 THEN 1 ELSE 0 END) as low_stock_count,
        AVG(p.demand_score) as avg_demand
      FROM products p
      GROUP BY p.category
      ORDER BY avg_demand DESC
    `;

    db.all(query, [], (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }
      
      res.json({
        success: true,
        data: rows.map(row => ({
          ...row,
          avg_price: parseFloat(row.avg_price.toFixed(2)),
          avg_base_price: parseFloat(row.avg_base_price.toFixed(2)),
          avg_markup: parseFloat(row.avg_markup.toFixed(2)),
          avg_demand: parseFloat(row.avg_demand.toFixed(2))
        }))
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/hourly-stats', async (req, res) => {
  try {
    const query = `
      SELECT 
        strftime('%H', timestamp) as hour,
        AVG(price) as avg_price,
        COUNT(*) as price_changes
      FROM price_history 
      WHERE timestamp >= datetime('now', '-7 days')
      GROUP BY hour
      ORDER BY hour
    `;

    db.all(query, [], (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }
      
      res.json({
        success: true,
        data: rows.map(row => ({
          hour: parseInt(row.hour),
          avg_price: parseFloat(row.avg_price.toFixed(2)),
          price_changes: row.price_changes
        }))
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/top-products', async (req, res) => {
  try {
    const { metric = 'demand', limit = 10 } = req.query;
    
    let orderBy = 'demand_score DESC';
    if (metric === 'price') orderBy = 'current_price DESC';
    if (metric === 'rating') orderBy = 'rating DESC';
    if (metric === 'reviews') orderBy = 'review_count DESC';

    const query = `
      SELECT 
        id, title, category, base_price, current_price, 
        rating, review_count, stock_level, demand_score
      FROM products
      ORDER BY ${orderBy}
      LIMIT ?
    `;

    db.all(query, [parseInt(limit)], (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }
      
      res.json({
        success: true,
        metric,
        data: rows
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/export/csv', async (req, res) => {
  try {
    const { category } = req.query;
    
    const query = category
      ? 'SELECT * FROM products WHERE category = ?'
      : 'SELECT * FROM products';
    
    const params = category ? [category] : [];

    db.all(query, params, (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }

      const headers = Object.keys(rows[0] || {});
      let csv = headers.join(',') + '\n';
      
      rows.forEach(row => {
        const values = headers.map(header => {
          const value = row[header];
          if (typeof value === 'string' && value.includes(',')) {
            return `"${value}"`;
          }
          return value;
        });
        csv += values.join(',') + '\n';
      });

      res.setHeader('Content-Type', 'text/csv');
      res.setHeader('Content-Disposition', `attachment; filename=products_${Date.now()}.csv`);
      res.send(csv);
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
