const { products } = require('./data');

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
    const path = event.path.replace('/.netlify/functions/products', '');
    
    if (event.httpMethod === 'GET') {
      if (path && path !== '/') {
        const id = parseInt(path.split('/')[1]);
        const product = products.find(p => p.id === id);
        
        if (!product) {
          return {
            statusCode: 404,
            headers,
            body: JSON.stringify({ success: false, error: 'Product not found' })
          };
        }
        
        return {
          statusCode: 200,
          headers,
          body: JSON.stringify({ success: true, data: product })
        };
      }
      
      const { category, limit = 20 } = event.queryStringParameters || {};
      
      let filtered = products;
      if (category) {
        filtered = products.filter(p => p.category === category);
      }
      
      filtered = filtered.slice(0, parseInt(limit));
      
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({ success: true, data: filtered })
      };
    }
    
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ success: false, error: 'Method not allowed' })
    };
  } catch (error) {
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({ success: false, error: error.message })
    };
  }
};
