class PriceOptimizer {
  constructor() {
    this.trainingData = [];
    this.weights = {
      demand: 0.3,
      stock: 0.25,
      rating: 0.15,
      time: 0.2,
      competition: 0.1
    };
    this.learningRate = 0.01;
    this.priceMemory = new Map();
    this.performanceHistory = [];
    this.categoryPatterns = new Map();
  }

  normalize(value, min, max) {
    if (max === min) return 0.5;
    return (value - min) / (max - min);
  }

  addTrainingData(product, actualSales, revenue) {
    this.trainingData.push({
      features: {
        demand: product.demand_score || 1.0,
        stock: product.stock_level || 100,
        rating: product.rating || 0,
        reviewCount: product.review_count || 0,
        basePrice: product.base_price,
        currentPrice: product.current_price,
        hour: new Date().getHours(),
        dayOfWeek: new Date().getDay(),
        category: product.category
      },
      outcome: {
        sales: actualSales,
        revenue: revenue,
        conversionRate: actualSales > 0 ? revenue / actualSales : 0
      }
    });

    if (this.trainingData.length > 1000) {
      this.trainingData.shift();
    }
    
    const performance = actualSales / (product.demand_score || 1.0);
    if (!this.priceMemory.has(product.id)) {
      this.priceMemory.set(product.id, []);
    }
    
    const history = this.priceMemory.get(product.id);
    history.push({
      price: product.current_price,
      performance,
      timestamp: Date.now()
    });
    
    if (history.length > 50) {
      history.shift();
    }
    
    this.performanceHistory.push({
      productId: product.id,
      category: product.category,
      price: product.current_price,
      sales: actualSales,
      revenue,
      timestamp: Date.now()
    });
    
    if (this.performanceHistory.length > 500) {
      this.performanceHistory.shift();
    }
  }

  predictOptimalPrice(product) {
    const basePrice = product.base_price;
    const candidates = [];
    
    const categoryPattern = this.categoryPatterns.get(product.category) || { avgMultiplier: 1.0, volatility: 0.1 };
    const historicalPerformance = this.priceMemory.get(product.id) || [];

    for (let multiplier = 0.7; multiplier <= 1.5; multiplier += 0.05) {
      const testPrice = basePrice * multiplier;
      const demandScore = this.scorePricePoint(product, testPrice);
      const profitMargin = (testPrice - basePrice * 0.6) / testPrice;
      const categoryAlignment = 1 - Math.abs(multiplier - categoryPattern.avgMultiplier) * 0.5;
      
      const historicalBonus = historicalPerformance.length > 0
        ? historicalPerformance.filter(h => Math.abs(h.price - testPrice) < testPrice * 0.1)
            .reduce((sum, h) => sum + h.performance, 0) / historicalPerformance.length
        : 0;
      
      const compositeScore = (
        demandScore * 0.4 +
        profitMargin * 100 * 0.3 +
        categoryAlignment * 0.2 +
        historicalBonus * 0.1
      );
      
      candidates.push({
        price: parseFloat(testPrice.toFixed(2)),
        multiplier: parseFloat(multiplier.toFixed(2)),
        score: compositeScore,
        expectedRevenue: compositeScore * testPrice,
        expectedSales: demandScore * 100,
        profitMargin: parseFloat((profitMargin * 100).toFixed(1)),
        confidence: this.calculateConfidence(product)
      });
    }

    candidates.sort((a, b) => b.expectedRevenue - a.expectedRevenue);
    
    this.updateCategoryPattern(product.category, candidates[0].multiplier);

    return {
      optimalPrice: candidates[0].price,
      currentPrice: product.current_price,
      basePrice: product.base_price,
      expectedIncrease: ((candidates[0].price - product.current_price) / product.current_price * 100).toFixed(2),
      confidence: candidates[0].confidence,
      profitMargin: candidates[0].profitMargin,
      expectedSales: parseFloat(candidates[0].expectedSales.toFixed(1)),
      alternatives: candidates.slice(0, 5),
      reasoning: this.explainPrediction(product, candidates[0]),
      categoryInsight: this.getCategoryInsight(product.category)
    };
  }
  
  updateCategoryPattern(category, multiplier) {
    if (!this.categoryPatterns.has(category)) {
      this.categoryPatterns.set(category, { avgMultiplier: multiplier, volatility: 0.1, count: 1 });
    } else {
      const pattern = this.categoryPatterns.get(category);
      pattern.avgMultiplier = (pattern.avgMultiplier * pattern.count + multiplier) / (pattern.count + 1);
      pattern.count++;
      this.categoryPatterns.set(category, pattern);
    }
  }
  
  getCategoryInsight(category) {
    const pattern = this.categoryPatterns.get(category);
    if (!pattern || pattern.count < 5) {
      return 'Kategori için yeterli veri yok';
    }
    
    if (pattern.avgMultiplier > 1.2) {
      return `${category} kategorisi premium fiyatlandırmaya uygun (+${((pattern.avgMultiplier - 1) * 100).toFixed(0)}%)`;
    } else if (pattern.avgMultiplier < 0.9) {
      return `${category} kategorisi indirimli fiyatlandırma gerektiriyor (${((1 - pattern.avgMultiplier) * 100).toFixed(0)}%)`;
    } else {
      return `${category} kategorisi standart fiyatlandırma ile iyi performans gösteriyor`;
    }
  }

  scorePricePoint(product, testPrice) {
    const priceElasticity = this.calculatePriceElasticity(product);
    const demandScore = product.demand_score || 1.0;
    const stockLevel = product.stock_level || 100;
    const rating = product.rating || 0;
    const reviewCount = product.review_count || 0;
    
    const priceRatio = testPrice / product.base_price;
    
    let demandImpact = demandScore;
    const priceDeviation = priceRatio - 1;
    
    if (priceRatio > 1.0) {
      const elasticityFactor = Math.pow(priceElasticity, 1.5);
      demandImpact *= Math.exp(-priceDeviation * elasticityFactor);
    } else if (priceRatio < 1.0) {
      demandImpact *= (1 + Math.abs(priceDeviation) * 0.8);
    }

    let stockImpact = 1.0;
    const stockRatio = stockLevel / 100;
    if (stockLevel < 20) {
      stockImpact = 1.4 + (20 - stockLevel) * 0.02;
    } else if (stockLevel > 150) {
      stockImpact = 0.75 - (stockLevel - 150) * 0.001;
    } else {
      stockImpact = 1.0 + (100 - stockLevel) * 0.002;
    }

    let ratingImpact = 1.0;
    if (rating >= 4.5 && reviewCount > 50) {
      ratingImpact = 1.15 + (rating - 4.5) * 0.1;
    } else if (rating >= 4.0 && reviewCount > 20) {
      ratingImpact = 1.08;
    } else if (rating < 3.5 && rating > 0) {
      ratingImpact = 0.85 - (3.5 - rating) * 0.05;
    }

    const hour = new Date().getHours();
    const dayOfWeek = new Date().getDay();
    let timeImpact = 1.0;
    
    if (hour >= 17 && hour <= 20) {
      timeImpact = 1.2;
    } else if (hour >= 12 && hour <= 14) {
      timeImpact = 1.1;
    } else if (hour >= 22 || hour <= 5) {
      timeImpact = 0.75;
    } else if (hour >= 6 && hour <= 9) {
      timeImpact = 1.05;
    }
    
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      timeImpact *= 1.1;
    }

    const crossFactorBonus = this.calculateCrossFactorBonus(
      demandScore, stockLevel, rating, priceRatio
    );

    const score = demandImpact * stockImpact * ratingImpact * timeImpact * (1 + crossFactorBonus);
    
    return Math.max(0, score);
  }
  
  calculateCrossFactorBonus(demand, stock, rating, priceRatio) {
    let bonus = 0;
    
    if (demand > 1.3 && stock < 30) {
      bonus += 0.15;
    }
    
    if (rating >= 4.5 && priceRatio > 1.1) {
      bonus += 0.1;
    }
    
    if (demand < 0.8 && stock > 150) {
      bonus -= 0.1;
    }
    
    return bonus;
  }

  calculatePriceElasticity(product) {
    if (this.trainingData.length < 10) {
      return 0.5;
    }

    const relevantData = this.trainingData
      .filter(d => d.features.basePrice >= product.base_price * 0.8 && 
                   d.features.basePrice <= product.base_price * 1.2)
      .slice(-20);

    if (relevantData.length < 5) {
      return 0.5;
    }

    let totalElasticity = 0;
    let count = 0;

    for (let i = 1; i < relevantData.length; i++) {
      const prev = relevantData[i - 1];
      const curr = relevantData[i];

      const priceChange = (curr.features.currentPrice - prev.features.currentPrice) / prev.features.currentPrice;
      const salesChange = (curr.outcome.sales - prev.outcome.sales) / (prev.outcome.sales || 1);

      if (Math.abs(priceChange) > 0.01) {
        const elasticity = Math.abs(salesChange / priceChange);
        totalElasticity += elasticity;
        count++;
      }
    }

    return count > 0 ? totalElasticity / count : 0.5;
  }

  calculateConfidence(product) {
    const dataPoints = this.trainingData.filter(d => 
      d.features.basePrice >= product.base_price * 0.8 && 
      d.features.basePrice <= product.base_price * 1.2
    ).length;

    if (dataPoints === 0) return 0.3;
    if (dataPoints < 10) return 0.5;
    if (dataPoints < 50) return 0.7;
    if (dataPoints < 100) return 0.85;
    return 0.95;
  }

  explainPrediction(product, prediction) {
    const reasons = [];
    
    const priceChange = ((prediction.price - product.base_price) / product.base_price * 100);
    
    if (priceChange > 10) {
      reasons.push(`🔥 Yüksek talep ve düşük stok nedeniyle +${priceChange.toFixed(1)}% artış öneriliyor`);
    } else if (priceChange < -10) {
      reasons.push(`📉 Düşük talep veya fazla stok nedeniyle ${priceChange.toFixed(1)}% indirim öneriliyor`);
    } else {
      reasons.push(`⚖️ Mevcut fiyat optimal seviyeye yakın`);
    }

    if (product.demand_score > 1.3) {
      reasons.push('📈 Talep çok yüksek, fiyat artırılabilir');
    } else if (product.demand_score < 0.7) {
      reasons.push('📊 Talep düşük, fiyat indirimi satışları artırabilir');
    }

    if (product.stock_level < 30) {
      reasons.push('⚠️ Stok azalıyor, premium fiyatlandırma uygun');
    } else if (product.stock_level > 150) {
      reasons.push('📦 Fazla stok var, hızlı satış için indirim öneriliyor');
    }

    if (product.rating >= 4.5 && product.review_count > 100) {
      reasons.push('⭐ Yüksek rating, müşteriler daha yüksek fiyat ödeyebilir');
    }

    return reasons.join(' | ');
  }

  trainModel() {
    if (this.trainingData.length < 20) {
      return {
        success: false,
        message: 'Yeterli veri yok (minimum 20 veri noktası gerekli)',
        dataPoints: this.trainingData.length
      };
    }

    const iterations = 100;
    let totalError = 0;

    for (let i = 0; i < iterations; i++) {
      let iterationError = 0;

      this.trainingData.forEach(data => {
        const predicted = this.scorePricePoint(
          { ...data.features, base_price: data.features.basePrice, current_price: data.features.currentPrice },
          data.features.currentPrice
        );
        
        const actual = data.outcome.sales / 100;
        const error = actual - predicted;
        iterationError += Math.abs(error);

        this.weights.demand += this.learningRate * error * data.features.demand;
        this.weights.stock += this.learningRate * error * (data.features.stock / 100);
        this.weights.rating += this.learningRate * error * (data.features.rating / 5);
      });

      totalError = iterationError / this.trainingData.length;
    }

    return {
      success: true,
      message: 'Model başarıyla eğitildi',
      dataPoints: this.trainingData.length,
      averageError: totalError.toFixed(4),
      weights: this.weights
    };
  }

  getModelStats() {
    return {
      trainingDataSize: this.trainingData.length,
      weights: this.weights,
      learningRate: this.learningRate,
      lastTrainingDate: this.trainingData.length > 0 
        ? new Date().toISOString() 
        : null
    };
  }

  simulateScenarios(product) {
    const scenarios = [
      { name: 'Mevcut Fiyat', multiplier: 1.0 },
      { name: 'Agresif Artış', multiplier: 1.25 },
      { name: 'Hafif Artış', multiplier: 1.10 },
      { name: 'Hafif İndirim', multiplier: 0.90 },
      { name: 'Agresif İndirim', multiplier: 0.75 }
    ];

    return scenarios.map(scenario => {
      const testPrice = product.base_price * scenario.multiplier;
      const score = this.scorePricePoint(product, testPrice);
      
      return {
        scenario: scenario.name,
        price: parseFloat(testPrice.toFixed(2)),
        multiplier: scenario.multiplier,
        expectedSales: parseFloat((score * 100).toFixed(1)),
        expectedRevenue: parseFloat((score * testPrice * 100).toFixed(2)),
        profitMargin: ((testPrice - product.base_price * 0.6) / testPrice * 100).toFixed(1)
      };
    });
  }
}

module.exports = PriceOptimizer;
