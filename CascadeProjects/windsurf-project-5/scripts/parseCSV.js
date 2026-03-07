const fs = require('fs');
const csv = require('csv-parser');
const path = require('path');

const products = [];
let currentProduct = null;

function parsePrice(priceStr) {
  if (!priceStr) return 0;
  const cleaned = priceStr.replace(/[$,]/g, '').trim();
  return parseFloat(cleaned) || 0;
}

function parseRating(ratingStr) {
  if (!ratingStr) return { score: 0, reviews: 0 };
  const scoreMatch = ratingStr.match(/Rated ([\d.]+)/);
  const reviewsMatch = ratingStr.match(/based on ([\d,]+)/);
  return {
    score: scoreMatch ? parseFloat(scoreMatch[1]) : 0,
    reviews: reviewsMatch ? parseInt(reviewsMatch[1].replace(/,/g, '')) : 0
  };
}

console.log('Parsing GroceryDataset.csv...');

fs.createReadStream(path.join(__dirname, '../GroceryDataset.csv'))
  .pipe(csv())
  .on('data', (row) => {
    try {
      const price = parsePrice(row.Price);
      const rating = parseRating(row.Rating);
      
      if (price > 0 && row.Title && row['Sub Category']) {
        const product = {
          category: row['Sub Category'].trim(),
          title: row.Title.trim(),
          basePrice: price,
          discount: row.Discount || 'No Discount',
          rating: rating.score,
          reviewCount: rating.reviews,
          currency: row.Currency || '$',
          features: row.Feature || '',
          description: row['Product Description'] || ''
        };
        products.push(product);
      }
    } catch (error) {
      console.error('Error parsing row:', error.message);
    }
  })
  .on('end', () => {
    console.log(`\nParsed ${products.length} products`);
    
    const categories = [...new Set(products.map(p => p.category))];
    console.log(`\nFound ${categories.length} categories:`);
    categories.forEach(cat => {
      const count = products.filter(p => p.category === cat).length;
      console.log(`  - ${cat}: ${count} products`);
    });
    
    fs.writeFileSync(
      path.join(__dirname, '../data/parsed_products.json'),
      JSON.stringify(products, null, 2)
    );
    console.log('\nSaved to data/parsed_products.json');
  })
  .on('error', (error) => {
    console.error('Error reading CSV:', error);
  });
