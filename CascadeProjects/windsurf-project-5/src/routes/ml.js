const express = require('express');
const router = express.Router();
const { getProductById, getAllProducts } = require('../database/db');
const PriceOptimizer = require('../ml/priceOptimizer');

const optimizer = new PriceOptimizer();

router.post('/train', async (req, res) => {
  try {
    const { trainingData } = req.body;
    
    if (trainingData && Array.isArray(trainingData)) {
      trainingData.forEach(data => {
        optimizer.addTrainingData(data.product, data.sales, data.revenue);
      });
    }

    const result = optimizer.trainModel();
    
    res.json({
      success: true,
      ...result
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/predict/:productId', async (req, res) => {
  try {
    const product = await getProductById(req.params.productId);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const prediction = optimizer.predictOptimalPrice(product);
    
    res.json({
      success: true,
      product: {
        id: product.id,
        title: product.title,
        category: product.category
      },
      prediction
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/simulate/:productId', async (req, res) => {
  try {
    const product = await getProductById(req.params.productId);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const scenarios = optimizer.simulateScenarios(product);
    
    res.json({
      success: true,
      product: {
        id: product.id,
        title: product.title,
        basePrice: product.base_price,
        currentPrice: product.current_price
      },
      scenarios
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/add-training-data', async (req, res) => {
  try {
    const { productId, sales, revenue } = req.body;
    
    const product = await getProductById(productId);
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    optimizer.addTrainingData(product, sales, revenue);
    
    res.json({
      success: true,
      message: 'Training data added',
      totalDataPoints: optimizer.trainingData.length
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/stats', (req, res) => {
  try {
    const stats = optimizer.getModelStats();
    
    res.json({
      success: true,
      stats
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/batch-predict', async (req, res) => {
  try {
    const { category, limit = 20 } = req.body;
    
    const products = await getAllProducts();
    let filtered = products;
    
    if (category) {
      filtered = products.filter(p => p.category === category);
    }
    
    filtered = filtered.slice(0, limit);
    
    const predictions = filtered.map(product => {
      const prediction = optimizer.predictOptimalPrice(product);
      return {
        productId: product.id,
        title: product.title,
        category: product.category,
        currentPrice: product.current_price,
        optimalPrice: prediction.optimalPrice,
        expectedIncrease: prediction.expectedIncrease,
        confidence: prediction.confidence
      };
    });

    predictions.sort((a, b) => Math.abs(b.expectedIncrease) - Math.abs(a.expectedIncrease));
    
    res.json({
      success: true,
      count: predictions.length,
      predictions
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = optimizer;
module.exports.router = router;
