const { products } = require('./data');
const pricingEngine = require('../../src/pricing/pricingEngine');

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
    const path = event.path.replace('/.netlify/functions/pricing', '');
    
    if (path.includes('/product/')) {
      const productId = parseInt(path.split('/product/')[1].split('/')[0]);
      const { strategy = 'combined' } = event.queryStringParameters || {};
      
      const product = products.find(p => p.id === productId);
      if (!product) {
        return {
          statusCode: 404,
          headers,
          body: JSON.stringify({ success: false, error: 'Product not found' })
        };
      }
      
      const pricing = pricingEngine.calculatePrice(product, strategy);
      
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          data: { product, pricing }
        })
      };
    }
    
    if (path === '/strategies') {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          data: {
            strategies: [
              { name: 'demand', description: 'Talep bazlı fiyatlandırma' },
              { name: 'time', description: 'Zaman bazlı fiyatlandırma' },
              { name: 'inventory', description: 'Stok bazlı fiyatlandırma' },
              { name: 'rating', description: 'Değerlendirme bazlı fiyatlandırma' },
              { name: 'competition', description: 'Rekabet bazlı fiyatlandırma' },
              { name: 'combined', description: 'Kombine strateji' }
            ]
          }
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
