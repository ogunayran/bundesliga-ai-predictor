const moment = require('moment');

class PricingEngine {
  constructor() {
    this.strategies = {
      demand: this.demandBasedPricing.bind(this),
      time: this.timeBasedPricing.bind(this),
      inventory: this.inventoryBasedPricing.bind(this),
      rating: this.ratingBasedPricing.bind(this),
      competition: this.competitionBasedPricing.bind(this),
      combined: this.combinedPricing.bind(this)
    };
  }

  demandBasedPricing(product, options = {}) {
    const demandScore = product.demand_score || 1.0;
    let multiplier = 1.0;

    if (demandScore > 1.5) {
      multiplier = 1.15;
    } else if (demandScore > 1.2) {
      multiplier = 1.10;
    } else if (demandScore > 1.0) {
      multiplier = 1.05;
    } else if (demandScore < 0.7) {
      multiplier = 0.90;
    } else if (demandScore < 0.9) {
      multiplier = 0.95;
    }

    return {
      price: product.base_price * multiplier,
      multiplier,
      factor: 'demand',
      details: `Demand score: ${demandScore.toFixed(2)}`
    };
  }

  timeBasedPricing(product, options = {}) {
    const now = moment();
    const hour = now.hour();
    const dayOfWeek = now.day();
    let multiplier = 1.0;
    const factors = [];

    factors.push(`Current time: ${now.format('HH:mm')}`);

    if (hour >= 17 && hour <= 21) {
      multiplier *= 1.12;
      factors.push('🔥 Peak evening hours (+12%)');
    } else if (hour >= 11 && hour <= 14) {
      multiplier *= 1.08;
      factors.push('🍽️ Lunch hours (+8%)');
    } else if (hour >= 6 && hour <= 9) {
      multiplier *= 1.06;
      factors.push('☀️ Morning rush (+6%)');
    } else if (hour >= 22 || hour <= 5) {
      multiplier *= 0.92;
      factors.push('🌙 Late night discount (-8%)');
    }

    if (dayOfWeek === 6 || dayOfWeek === 0) {
      multiplier *= 1.08;
      factors.push('📅 Weekend premium (+8%)');
    }

    if (product.category && product.category.includes('Bakery')) {
      if (hour >= 6 && hour <= 10) {
        multiplier *= 1.12;
        factors.push('🥐 Bakery morning premium (+12%)');
      } else if (hour >= 20) {
        multiplier *= 0.85;
        factors.push('🥖 Bakery late discount (-15%)');
      }
    }

    if (product.category && product.category.includes('Meat')) {
      if (hour >= 16 && hour <= 19) {
        multiplier *= 1.10;
        factors.push('🥩 Dinner prep time (+10%)');
      }
    }

    return {
      price: product.base_price * multiplier,
      multiplier,
      factor: 'time',
      details: factors.join(' | ')
    };
  }

  inventoryBasedPricing(product, options = {}) {
    const stockLevel = product.stock_level || 100;
    let multiplier = 1.0;
    let reason = '';

    if (stockLevel < 20) {
      multiplier = 1.20;
      reason = 'Very low stock (scarcity premium)';
    } else if (stockLevel < 50) {
      multiplier = 1.10;
      reason = 'Low stock';
    } else if (stockLevel > 150) {
      multiplier = 0.92;
      reason = 'Overstock (clearance discount)';
    } else if (stockLevel > 120) {
      multiplier = 0.95;
      reason = 'High stock';
    } else {
      reason = 'Normal stock level';
    }

    return {
      price: product.base_price * multiplier,
      multiplier,
      factor: 'inventory',
      details: `Stock: ${stockLevel} units - ${reason}`
    };
  }

  ratingBasedPricing(product, options = {}) {
    const rating = product.rating || 0;
    const reviewCount = product.review_count || 0;
    let multiplier = 1.0;

    if (rating >= 4.5 && reviewCount > 1000) {
      multiplier = 1.08;
    } else if (rating >= 4.5 && reviewCount > 100) {
      multiplier = 1.05;
    } else if (rating >= 4.0 && reviewCount > 500) {
      multiplier = 1.03;
    } else if (rating < 3.5) {
      multiplier = 0.95;
    }

    return {
      price: product.base_price * multiplier,
      multiplier,
      factor: 'rating',
      details: `Rating: ${rating}/5 (${reviewCount} reviews)`
    };
  }

  competitionBasedPricing(product, options = {}) {
    let competitorPrice = options.competitorPrice;
    
    if (!competitorPrice) {
      const variance = 0.85 + Math.random() * 0.30;
      competitorPrice = product.base_price * variance;
    }
    
    let multiplier = 1.0;
    const priceDiff = (competitorPrice - product.base_price) / product.base_price;
    const factors = [];

    if (priceDiff > 0.15) {
      multiplier = 1.12;
      factors.push('💰 Competitor much higher (+12%)');
    } else if (priceDiff > 0.08) {
      multiplier = 1.08;
      factors.push('💵 Competitor higher (+8%)');
    } else if (priceDiff > 0.03) {
      multiplier = 1.04;
      factors.push('📊 Slightly above market (+4%)');
    } else if (priceDiff < -0.15) {
      multiplier = 0.92;
      factors.push('⚠️ Competitor much lower (-8%)');
    } else if (priceDiff < -0.08) {
      multiplier = 0.96;
      factors.push('📉 Competitor lower (-4%)');
    } else {
      factors.push('⚖️ Competitive pricing');
    }

    factors.push(`Competitor: $${competitorPrice.toFixed(2)}`);

    return {
      price: product.base_price * multiplier,
      multiplier,
      factor: 'competition',
      details: factors.join(' | ')
    };
  }

  combinedPricing(product, options = {}) {
    const weights = options.weights || {
      demand: 0.25,
      time: 0.25,
      inventory: 0.25,
      rating: 0.10,
      competition: 0.15
    };

    const results = {
      demand: this.demandBasedPricing(product, options),
      time: this.timeBasedPricing(product, options),
      inventory: this.inventoryBasedPricing(product, options),
      rating: this.ratingBasedPricing(product, options),
      competition: this.competitionBasedPricing(product, options)
    };

    let finalMultiplier = 0;
    const factors = [];

    for (const [strategy, weight] of Object.entries(weights)) {
      if (results[strategy]) {
        finalMultiplier += (results[strategy].multiplier - 1) * weight;
        factors.push({
          strategy,
          weight,
          multiplier: results[strategy].multiplier,
          details: results[strategy].details
        });
      }
    }

    finalMultiplier += 1;

    const minPrice = product.base_price * 0.70;
    const maxPrice = product.base_price * 1.50;
    let finalPrice = product.base_price * finalMultiplier;
    
    finalPrice = Math.max(minPrice, Math.min(maxPrice, finalPrice));

    return {
      price: parseFloat(finalPrice.toFixed(2)),
      basePrice: product.base_price,
      multiplier: parseFloat(finalMultiplier.toFixed(4)),
      factor: 'combined',
      factors,
      priceChange: finalPrice - product.base_price,
      priceChangePercent: ((finalPrice - product.base_price) / product.base_price * 100).toFixed(2)
    };
  }

  calculatePrice(product, strategy = 'combined', options = {}) {
    if (!this.strategies[strategy]) {
      throw new Error(`Unknown pricing strategy: ${strategy}`);
    }

    const result = this.strategies[strategy](product, options);
    
    result.price = parseFloat(result.price.toFixed(2));
    result.timestamp = new Date().toISOString();
    result.productId = product.id;
    result.strategy = strategy;

    return result;
  }

  calculateBulkPricing(products, strategy = 'combined', options = {}) {
    return products.map(product => this.calculatePrice(product, strategy, options));
  }

  simulatePriceChanges(product, days = 7) {
    const simulations = [];
    const now = moment();

    for (let i = 0; i < days * 24; i++) {
      const simulatedTime = now.clone().add(i, 'hours');
      
      const simulatedProduct = {
        ...product,
        demand_score: 0.8 + Math.random() * 0.6,
        stock_level: Math.max(10, product.stock_level - Math.floor(Math.random() * 5))
      };

      const originalMoment = moment;
      moment.now = () => simulatedTime.valueOf();

      const pricing = this.calculatePrice(simulatedProduct, 'combined');
      
      moment.now = originalMoment.now;

      simulations.push({
        timestamp: simulatedTime.toISOString(),
        hour: simulatedTime.hour(),
        dayOfWeek: simulatedTime.day(),
        price: pricing.price,
        demandScore: simulatedProduct.demand_score,
        stockLevel: simulatedProduct.stock_level
      });
    }

    return simulations;
  }
}

module.exports = PricingEngine;
