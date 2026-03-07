const fs = require('fs');
const path = require('path');
const { db, initDatabase } = require('../src/database/db');

async function seedDatabase() {
  try {
    console.log('Initializing database...');
    await initDatabase();

    const productsPath = path.join(__dirname, '../data/parsed_products.json');
    
    if (!fs.existsSync(productsPath)) {
      console.error('parsed_products.json not found. Run "npm run parse-csv" first.');
      process.exit(1);
    }

    const products = JSON.parse(fs.readFileSync(productsPath, 'utf8'));
    console.log(`Loading ${products.length} products...`);

    const stmt = db.prepare(`
      INSERT INTO products (
        category, title, base_price, current_price, discount, 
        rating, review_count, stock_level, demand_score, 
        currency, features, description
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    let inserted = 0;
    for (const product of products) {
      const stockLevel = Math.floor(Math.random() * 150) + 50;
      const demandScore = 0.8 + Math.random() * 0.4;
      
      stmt.run(
        product.category,
        product.title,
        product.basePrice,
        product.basePrice,
        product.discount,
        product.rating,
        product.reviewCount,
        stockLevel,
        demandScore,
        product.currency,
        product.features,
        product.description,
        (err) => {
          if (err) {
            console.error('Error inserting product:', err.message);
          }
        }
      );
      inserted++;
      
      if (inserted % 100 === 0) {
        console.log(`Inserted ${inserted} products...`);
      }
    }

    stmt.finalize((err) => {
      if (err) {
        console.error('Error finalizing:', err);
      } else {
        console.log(`\n✓ Successfully seeded ${inserted} products`);
        
        db.all('SELECT category, COUNT(*) as count FROM products GROUP BY category', (err, rows) => {
          if (!err) {
            console.log('\nProducts by category:');
            rows.forEach(row => {
              console.log(`  ${row.category}: ${row.count}`);
            });
          }
          db.close();
        });
      }
    });

  } catch (error) {
    console.error('Error seeding database:', error);
    process.exit(1);
  }
}

seedDatabase();
