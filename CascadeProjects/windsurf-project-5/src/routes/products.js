const express = require('express');
const router = express.Router();
const {
  getAllProducts,
  getProductById,
  getProductsByCategory,
  updateProductPrice,
  getPriceHistory,
  getCategories,
  updateStockLevel,
  updateDemandScore
} = require('../database/db');
const PricingEngine = require('../pricing/pricingEngine');

const pricingEngine = new PricingEngine();

router.get('/', async (req, res) => {
  try {
    const { category, limit, offset } = req.query;
    let products;

    if (category) {
      products = await getProductsByCategory(category);
    } else {
      products = await getAllProducts();
    }

    if (offset) {
      products = products.slice(parseInt(offset));
    }
    if (limit) {
      products = products.slice(0, parseInt(limit));
    }

    res.json({
      success: true,
      count: products.length,
      data: products
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/categories', async (req, res) => {
  try {
    const categories = await getCategories();
    res.json({
      success: true,
      count: categories.length,
      data: categories
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/:id', async (req, res) => {
  try {
    const product = await getProductById(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    res.json({
      success: true,
      data: product
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/:id/price', async (req, res) => {
  try {
    const product = await getProductById(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const strategy = req.query.strategy || 'combined';
    const options = {
      competitorPrice: req.query.competitorPrice ? parseFloat(req.query.competitorPrice) : undefined,
      targetMargin: req.query.targetMargin ? parseFloat(req.query.targetMargin) : undefined
    };

    const pricing = pricingEngine.calculatePrice(product, strategy, options);

    res.json({
      success: true,
      data: {
        product: {
          id: product.id,
          title: product.title,
          category: product.category
        },
        pricing
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/:id/price-history', async (req, res) => {
  try {
    const limit = req.query.limit ? parseInt(req.query.limit) : 50;
    const history = await getPriceHistory(req.params.id, limit);

    res.json({
      success: true,
      count: history.length,
      data: history
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.get('/:id/simulate', async (req, res) => {
  try {
    const product = await getProductById(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const days = req.query.days ? parseInt(req.query.days) : 7;
    const simulations = pricingEngine.simulatePriceChanges(product, days);

    res.json({
      success: true,
      product: {
        id: product.id,
        title: product.title,
        basePrice: product.base_price
      },
      simulations
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.post('/:id/update-price', async (req, res) => {
  try {
    const product = await getProductById(req.params.id);
    
    if (!product) {
      return res.status(404).json({
        success: false,
        error: 'Product not found'
      });
    }

    const strategy = req.body.strategy || 'combined';
    const pricing = pricingEngine.calculatePrice(product, strategy, req.body.options || {});

    await updateProductPrice(
      req.params.id,
      pricing.price,
      strategy,
      pricing.factors || {}
    );

    res.json({
      success: true,
      data: {
        productId: req.params.id,
        oldPrice: product.current_price,
        newPrice: pricing.price,
        strategy,
        pricing
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.patch('/:id/stock', async (req, res) => {
  try {
    const { stockLevel } = req.body;
    
    if (stockLevel === undefined || stockLevel < 0) {
      return res.status(400).json({
        success: false,
        error: 'Valid stock level required'
      });
    }

    await updateStockLevel(req.params.id, stockLevel);

    res.json({
      success: true,
      data: {
        productId: req.params.id,
        stockLevel
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

router.patch('/:id/demand', async (req, res) => {
  try {
    const { demandScore } = req.body;
    
    if (demandScore === undefined || demandScore < 0) {
      return res.status(400).json({
        success: false,
        error: 'Valid demand score required'
      });
    }

    await updateDemandScore(req.params.id, demandScore);

    res.json({
      success: true,
      data: {
        productId: req.params.id,
        demandScore
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

module.exports = router;
