// Static product data for Netlify deployment
const products = require('../../data/parsed_products.js');

// Sample products for demo
const sampleProducts = products.slice(0, 100).map((p, index) => ({
  id: index + 1,
  title: p.title,
  category: p.category,
  base_price: parseFloat(p.price) || 10.99,
  current_price: parseFloat(p.price) || 10.99,
  stock_level: Math.floor(Math.random() * 150) + 50,
  demand_score: Math.random() * 0.4 + 0.8,
  rating: parseFloat(p.rating) || 4.0,
  review_count: Math.floor(Math.random() * 500) + 10,
  description: p.description || ''
}));

module.exports = { products: sampleProducts };
