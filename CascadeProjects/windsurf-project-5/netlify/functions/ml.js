const { getProductById } = require('../../src/database/db');
const mlRouter = require('../../src/routes/ml');

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
      const productId = path.split('/predict/')[1];
      const product = await getProductById(productId);
      
      if (!product) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ success: false, error: 'Product not found' })
        };
      }
      
      const prediction = mlRouter.predictOptimalPrice(product);
      
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
      const productId = path.split('/simulate/')[1];
      const product = await getProductById(productId);
      
      if (!product) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ success: false, error: 'Product not found' })
        };
      }
      
      const scenarios = mlRouter.simulateScenarios(product);
      
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
