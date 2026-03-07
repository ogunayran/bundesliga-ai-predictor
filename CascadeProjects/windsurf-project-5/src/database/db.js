const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const dbDir = path.join(__dirname, '../../data');
if (!fs.existsSync(dbDir)) {
  fs.mkdirSync(dbDir, { recursive: true });
}

const dbPath = path.join(dbDir, 'grocery.db');
const db = new sqlite3.Database(dbPath);

function initDatabase() {
  return new Promise((resolve, reject) => {
    db.serialize(() => {
      db.run(`
        CREATE TABLE IF NOT EXISTS products (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          category TEXT NOT NULL,
          title TEXT NOT NULL,
          base_price REAL NOT NULL,
          current_price REAL NOT NULL,
          discount TEXT,
          rating REAL DEFAULT 0,
          review_count INTEGER DEFAULT 0,
          stock_level INTEGER DEFAULT 100,
          demand_score REAL DEFAULT 1.0,
          currency TEXT DEFAULT '$',
          features TEXT,
          description TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      db.run(`
        CREATE TABLE IF NOT EXISTS price_history (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          product_id INTEGER NOT NULL,
          price REAL NOT NULL,
          strategy TEXT,
          factors TEXT,
          timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY (product_id) REFERENCES products(id)
        )
      `);

      db.run(`
        CREATE TABLE IF NOT EXISTS categories (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT UNIQUE NOT NULL,
          seasonal_factor REAL DEFAULT 1.0,
          peak_hours TEXT,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `);

      db.run(`
        CREATE TABLE IF NOT EXISTS pricing_rules (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          category TEXT,
          condition_type TEXT NOT NULL,
          condition_value TEXT NOT NULL,
          adjustment_type TEXT NOT NULL,
          adjustment_value REAL NOT NULL,
          priority INTEGER DEFAULT 0,
          active INTEGER DEFAULT 1,
          created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
      `, (err) => {
        if (err) reject(err);
        else {
          console.log('Database initialized successfully');
          resolve();
        }
      });
    });
  });
}

function getAllProducts() {
  return new Promise((resolve, reject) => {
    db.all('SELECT * FROM products ORDER BY category, title', (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

function getProductById(id) {
  return new Promise((resolve, reject) => {
    db.get('SELECT * FROM products WHERE id = ?', [id], (err, row) => {
      if (err) reject(err);
      else resolve(row);
    });
  });
}

function getProductsByCategory(category) {
  return new Promise((resolve, reject) => {
    db.all('SELECT * FROM products WHERE category = ?', [category], (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

function updateProductPrice(id, newPrice, strategy, factors) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE products SET current_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [newPrice, id],
      function(err) {
        if (err) {
          reject(err);
        } else {
          db.run(
            'INSERT INTO price_history (product_id, price, strategy, factors) VALUES (?, ?, ?, ?)',
            [id, newPrice, strategy, JSON.stringify(factors)],
            (err) => {
              if (err) reject(err);
              else resolve({ id, newPrice });
            }
          );
        }
      }
    );
  });
}

function getPriceHistory(productId, limit = 50) {
  return new Promise((resolve, reject) => {
    db.all(
      'SELECT * FROM price_history WHERE product_id = ? ORDER BY timestamp DESC LIMIT ?',
      [productId, limit],
      (err, rows) => {
        if (err) reject(err);
        else resolve(rows);
      }
    );
  });
}

function getCategories() {
  return new Promise((resolve, reject) => {
    db.all('SELECT DISTINCT category FROM products ORDER BY category', (err, rows) => {
      if (err) reject(err);
      else resolve(rows.map(r => r.category));
    });
  });
}

function updateStockLevel(productId, newLevel) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE products SET stock_level = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [newLevel, productId],
      function(err) {
        if (err) reject(err);
        else resolve({ productId, newLevel });
      }
    );
  });
}

function updateDemandScore(productId, newScore) {
  return new Promise((resolve, reject) => {
    db.run(
      'UPDATE products SET demand_score = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
      [newScore, productId],
      function(err) {
        if (err) reject(err);
        else resolve({ productId, newScore });
      }
    );
  });
}

module.exports = {
  db,
  initDatabase,
  getAllProducts,
  getProductById,
  getProductsByCategory,
  updateProductPrice,
  getPriceHistory,
  getCategories,
  updateStockLevel,
  updateDemandScore
};
