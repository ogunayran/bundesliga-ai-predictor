const express = require('express');
const router = express.Router();
const { db } = require('../database/db');
const { v4: uuidv4 } = require('uuid');

db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS ab_tests (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      product_id INTEGER,
      category TEXT,
      variant_a_price REAL NOT NULL,
      variant_b_price REAL NOT NULL,
      variant_a_views INTEGER DEFAULT 0,
      variant_b_views INTEGER DEFAULT 0,
      variant_a_sales INTEGER DEFAULT 0,
      variant_b_sales INTEGER DEFAULT 0,
      variant_a_revenue REAL DEFAULT 0,
      variant_b_revenue REAL DEFAULT 0,
      status TEXT DEFAULT 'active',
      start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
      end_date DATETIME,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);
});

router.post('/create', (req, res) => {
  try {
    const { name, productId, category, variantAPrice, variantBPrice, duration = 7 } = req.body;
    
    if (!name || (!productId && !category) || !variantAPrice || !variantBPrice) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields'
      });
    }

    const testId = uuidv4();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + duration);

    const query = `
      INSERT INTO ab_tests (
        id, name, product_id, category, 
        variant_a_price, variant_b_price, end_date
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
    `;

    db.run(
      query,
      [testId, name, productId || null, category || null, variantAPrice, variantBPrice, endDate.toISOString()],
      function(err) {
        if (err) {
          return res.status(500).json({ success: false, error: err.message });
        }

        res.json({
          success: true,
          testId,
          message: 'A/B test created successfully',
          test: {
            id: testId,
            name,
            productId,
            category,
            variantAPrice,
            variantBPrice,
            duration: `${duration} days`,
            endDate: endDate.toISOString()
          }
        });
      }
    );
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/list', (req, res) => {
  try {
    const { status = 'active' } = req.query;
    
    const query = status === 'all' 
      ? 'SELECT * FROM ab_tests ORDER BY created_at DESC'
      : 'SELECT * FROM ab_tests WHERE status = ? ORDER BY created_at DESC';
    
    const params = status === 'all' ? [] : [status];

    db.all(query, params, (err, rows) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }

      res.json({
        success: true,
        count: rows.length,
        tests: rows
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.get('/:testId', (req, res) => {
  try {
    db.get('SELECT * FROM ab_tests WHERE id = ?', [req.params.testId], (err, row) => {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }

      if (!row) {
        return res.status(404).json({ success: false, error: 'Test not found' });
      }

      const conversionA = row.variant_a_views > 0 ? (row.variant_a_sales / row.variant_a_views * 100) : 0;
      const conversionB = row.variant_b_views > 0 ? (row.variant_b_sales / row.variant_b_views * 100) : 0;
      const revenuePerViewA = row.variant_a_views > 0 ? (row.variant_a_revenue / row.variant_a_views) : 0;
      const revenuePerViewB = row.variant_b_views > 0 ? (row.variant_b_revenue / row.variant_b_views) : 0;

      let winner = 'Henüz belirsiz';
      if (row.variant_a_views > 30 && row.variant_b_views > 30) {
        if (revenuePerViewA > revenuePerViewB * 1.1) {
          winner = 'Variant A (Mevcut Fiyat)';
        } else if (revenuePerViewB > revenuePerViewA * 1.1) {
          winner = 'Variant B (Test Fiyatı)';
        } else {
          winner = 'Berabere';
        }
      }

      res.json({
        success: true,
        test: row,
        analysis: {
          variantA: {
            views: row.variant_a_views,
            sales: row.variant_a_sales,
            revenue: parseFloat(row.variant_a_revenue.toFixed(2)),
            conversionRate: parseFloat(conversionA.toFixed(2)),
            revenuePerView: parseFloat(revenuePerViewA.toFixed(2))
          },
          variantB: {
            views: row.variant_b_views,
            sales: row.variant_b_sales,
            revenue: parseFloat(row.variant_b_revenue.toFixed(2)),
            conversionRate: parseFloat(conversionB.toFixed(2)),
            revenuePerView: parseFloat(revenuePerViewB.toFixed(2))
          },
          winner,
          improvement: revenuePerViewB > revenuePerViewA 
            ? `+${((revenuePerViewB - revenuePerViewA) / revenuePerViewA * 100).toFixed(1)}%`
            : `-${((revenuePerViewA - revenuePerViewB) / revenuePerViewB * 100).toFixed(1)}%`
        }
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/:testId/record', (req, res) => {
  try {
    const { variant, action, amount = 0 } = req.body;
    
    if (!['A', 'B'].includes(variant) || !['view', 'sale'].includes(action)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid variant or action'
      });
    }

    let updateQuery = '';
    if (action === 'view') {
      updateQuery = variant === 'A' 
        ? 'UPDATE ab_tests SET variant_a_views = variant_a_views + 1 WHERE id = ?'
        : 'UPDATE ab_tests SET variant_b_views = variant_b_views + 1 WHERE id = ?';
    } else {
      updateQuery = variant === 'A'
        ? 'UPDATE ab_tests SET variant_a_sales = variant_a_sales + 1, variant_a_revenue = variant_a_revenue + ? WHERE id = ?'
        : 'UPDATE ab_tests SET variant_b_sales = variant_b_sales + 1, variant_b_revenue = variant_b_revenue + ? WHERE id = ?';
    }

    const params = action === 'sale' ? [amount, req.params.testId] : [req.params.testId];

    db.run(updateQuery, params, function(err) {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }

      res.json({
        success: true,
        message: `${action} recorded for variant ${variant}`
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.post('/:testId/stop', (req, res) => {
  try {
    db.run(
      'UPDATE ab_tests SET status = ?, end_date = CURRENT_TIMESTAMP WHERE id = ?',
      ['completed', req.params.testId],
      function(err) {
        if (err) {
          return res.status(500).json({ success: false, error: err.message });
        }

        res.json({
          success: true,
          message: 'Test stopped successfully'
        });
      }
    );
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

router.delete('/:testId', (req, res) => {
  try {
    db.run('DELETE FROM ab_tests WHERE id = ?', [req.params.testId], function(err) {
      if (err) {
        return res.status(500).json({ success: false, error: err.message });
      }

      res.json({
        success: true,
        message: 'Test deleted successfully'
      });
    });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
