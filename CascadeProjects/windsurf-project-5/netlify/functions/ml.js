const { products } = require('./data');
const PriceOptimizer = require('../../src/ml/priceOptimizer');
const optimizer = new PriceOptimizer();

exports.handler = async (event, context) => {
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers, body: '' };
  }

  try {
    const path = event.path.replace('/.netlify/functions/ml', '');
    
    if (path.includes('/predict/')) {
      const productId = parseInt(path.split('/predict/')[1]);
      const product = products.find(p => p.id === productId);
      
      if (!product) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ success: false, error: 'Product not found' })
        };
      }
      
      const prediction = optimizer.predictOptimalPrice(product);
      
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          product: {
            id: product.id,
            title: product.title,
            category: product.category
          },
          prediction
        })
      };
    }
    
    if (path.includes('/simulate/')) {
      const productId = parseInt(path.split('/simulate/')[1]);
      const product = products.find(p => p.id === productId);
      
      if (!product) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ success: false, error: 'Product not found' })
        };
      }
      
      const scenarios = optimizer.simulateScenarios(product);
      
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          product: {
            id: product.id,
            title: product.title,
            basePrice: product.base_price,
            currentPrice: product.current_price
          },
          scenarios
        })
      };
    }
    
    return {
      statusCode: 404,
      headers,
      body: JSON.stringify({ success: false, error: 'Not found' })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ success: false, error: error.message })
    };
  }
};
