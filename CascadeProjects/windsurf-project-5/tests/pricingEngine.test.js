const PricingEngine = require('../src/pricing/pricingEngine');

describe('PricingEngine', () => {
  let engine;
  let mockProduct;

  beforeEach(() => {
    engine = new PricingEngine();
    mockProduct = {
      id: 1,
      title: 'Test Product',
      category: 'Bakery & Desserts',
      base_price: 50.00,
      current_price: 50.00,
      rating: 4.5,
      review_count: 1000,
      stock_level: 100,
      demand_score: 1.0
    };
  });

  test('should create pricing engine with all strategies', () => {
    expect(engine.strategies).toBeDefined();
    expect(engine.strategies.demand).toBeDefined();
    expect(engine.strategies.time).toBeDefined();
    expect(engine.strategies.inventory).toBeDefined();
    expect(engine.strategies.rating).toBeDefined();
    expect(engine.strategies.competition).toBeDefined();
    expect(engine.strategies.combined).toBeDefined();
  });

  test('demand-based pricing should increase price for high demand', () => {
    mockProduct.demand_score = 1.6;
    const result = engine.calculatePrice(mockProduct, 'demand');
    expect(result.price).toBeGreaterThan(mockProduct.base_price);
    expect(result.multiplier).toBeGreaterThan(1.0);
  });

  test('demand-based pricing should decrease price for low demand', () => {
    mockProduct.demand_score = 0.6;
    const result = engine.calculatePrice(mockProduct, 'demand');
    expect(result.price).toBeLessThan(mockProduct.base_price);
    expect(result.multiplier).toBeLessThan(1.0);
  });

  test('inventory-based pricing should increase price for low stock', () => {
    mockProduct.stock_level = 15;
    const result = engine.calculatePrice(mockProduct, 'inventory');
    expect(result.price).toBeGreaterThan(mockProduct.base_price);
    expect(result.multiplier).toBeGreaterThan(1.0);
  });

  test('inventory-based pricing should decrease price for high stock', () => {
    mockProduct.stock_level = 160;
    const result = engine.calculatePrice(mockProduct, 'inventory');
    expect(result.price).toBeLessThan(mockProduct.base_price);
    expect(result.multiplier).toBeLessThan(1.0);
  });

  test('rating-based pricing should add premium for high ratings', () => {
    mockProduct.rating = 4.8;
    mockProduct.review_count = 5000;
    const result = engine.calculatePrice(mockProduct, 'rating');
    expect(result.price).toBeGreaterThan(mockProduct.base_price);
  });

  test('combined pricing should use all factors', () => {
    const result = engine.calculatePrice(mockProduct, 'combined');
    expect(result.factors).toBeDefined();
    expect(result.factors.length).toBeGreaterThan(0);
    expect(result.basePrice).toBe(mockProduct.base_price);
    expect(result.priceChange).toBeDefined();
    expect(result.priceChangePercent).toBeDefined();
  });

  test('combined pricing should respect min/max bounds', () => {
    mockProduct.demand_score = 3.0;
    mockProduct.stock_level = 5;
    const result = engine.calculatePrice(mockProduct, 'combined');
    expect(result.price).toBeLessThanOrEqual(mockProduct.base_price * 1.5);
    expect(result.price).toBeGreaterThanOrEqual(mockProduct.base_price * 0.7);
  });

  test('should calculate bulk pricing for multiple products', () => {
    const products = [mockProduct, { ...mockProduct, id: 2 }, { ...mockProduct, id: 3 }];
    const results = engine.calculateBulkPricing(products, 'combined');
    expect(results.length).toBe(3);
    results.forEach(result => {
      expect(result.price).toBeDefined();
      expect(result.strategy).toBe('combined');
    });
  });

  test('should throw error for unknown strategy', () => {
    expect(() => {
      engine.calculatePrice(mockProduct, 'unknown');
    }).toThrow('Unknown pricing strategy: unknown');
  });

  test('calculated price should have correct format', () => {
    const result = engine.calculatePrice(mockProduct, 'combined');
    expect(result.price).toEqual(expect.any(Number));
    expect(result.timestamp).toBeDefined();
    expect(result.productId).toBe(mockProduct.id);
    expect(result.strategy).toBe('combined');
  });
});
