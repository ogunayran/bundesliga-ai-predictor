const nodemailer = require('nodemailer');
const cron = require('node-cron');
const { getAllProducts, db } = require('../database/db');

class EmailReportService {
  constructor() {
    this.transporter = null;
    this.recipients = [];
    this.enabled = false;
  }

  configure(config) {
    if (!config.email || !config.password) {
      console.log('⚠️  Email configuration missing. Email reports disabled.');
      return false;
    }

    this.transporter = nodemailer.createTransport({
      service: config.service || 'gmail',
      auth: {
        user: config.email,
        pass: config.password
      }
    });

    this.recipients = config.recipients || [config.email];
    this.enabled = true;

    console.log('✅ Email service configured');
    return true;
  }

  async generateDailyReport() {
    try {
      const products = await getAllProducts();
      
      const stats = {
        totalProducts: products.length,
        avgPrice: products.reduce((sum, p) => sum + p.current_price, 0) / products.length,
        lowStock: products.filter(p => p.stock_level < 20).length,
        highDemand: products.filter(p => p.demand_score > 1.3).length,
        priceChanges: 0
      };

      const priceChanges = await new Promise((resolve, reject) => {
        db.all(
          `SELECT COUNT(*) as count FROM price_history 
           WHERE timestamp >= datetime('now', '-1 day')`,
          [],
          (err, rows) => {
            if (err) reject(err);
            else resolve(rows[0].count);
          }
        );
      });

      stats.priceChanges = priceChanges;

      const topProducts = products
        .sort((a, b) => b.demand_score - a.demand_score)
        .slice(0, 5);

      const lowStockProducts = products
        .filter(p => p.stock_level < 20)
        .slice(0, 5);

      const html = this.generateDailyReportHTML(stats, topProducts, lowStockProducts);

      return {
        subject: `📊 Günlük Fiyatlandırma Raporu - ${new Date().toLocaleDateString('tr-TR')}`,
        html,
        stats
      };
    } catch (error) {
      console.error('Error generating daily report:', error);
      throw error;
    }
  }

  generateDailyReportHTML(stats, topProducts, lowStockProducts) {
    return `
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
          .container { max-width: 600px; margin: 0 auto; padding: 20px; }
          .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; }
          .stats { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0; }
          .stat-box { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
          .stat-value { font-size: 2em; font-weight: bold; color: #667eea; }
          .stat-label { color: #666; font-size: 0.9em; margin-top: 5px; }
          .section { margin: 30px 0; }
          .section-title { font-size: 1.3em; color: #667eea; margin-bottom: 15px; border-bottom: 2px solid #667eea; padding-bottom: 10px; }
          .product-item { background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
          .product-name { font-weight: bold; color: #333; }
          .product-details { color: #666; font-size: 0.9em; margin-top: 5px; }
          .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }
          .footer { text-align: center; color: #666; font-size: 0.9em; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>🛒 Günlük Fiyatlandırma Raporu</h1>
            <p>${new Date().toLocaleDateString('tr-TR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>

          <div class="stats">
            <div class="stat-box">
              <div class="stat-value">${stats.totalProducts}</div>
              <div class="stat-label">Toplam Ürün</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">$${stats.avgPrice.toFixed(2)}</div>
              <div class="stat-label">Ortalama Fiyat</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">${stats.priceChanges}</div>
              <div class="stat-label">Fiyat Değişimi</div>
            </div>
            <div class="stat-box">
              <div class="stat-value">${stats.highDemand}</div>
              <div class="stat-label">Yüksek Talep</div>
            </div>
          </div>

          ${stats.lowStock > 0 ? `
          <div class="alert">
            <strong>⚠️ Uyarı:</strong> ${stats.lowStock} ürünün stoğu kritik seviyede!
          </div>
          ` : ''}

          <div class="section">
            <h2 class="section-title">🔥 En Yüksek Talep Gören Ürünler</h2>
            ${topProducts.map(p => `
              <div class="product-item">
                <div class="product-name">${p.title.substring(0, 60)}...</div>
                <div class="product-details">
                  Kategori: ${p.category} | Fiyat: $${p.current_price.toFixed(2)} | Talep: ${p.demand_score.toFixed(2)} | Stok: ${p.stock_level}
                </div>
              </div>
            `).join('')}
          </div>

          ${lowStockProducts.length > 0 ? `
          <div class="section">
            <h2 class="section-title">📦 Düşük Stoklu Ürünler</h2>
            ${lowStockProducts.map(p => `
              <div class="product-item">
                <div class="product-name">${p.title.substring(0, 60)}...</div>
                <div class="product-details">
                  Kategori: ${p.category} | Fiyat: $${p.current_price.toFixed(2)} | Stok: <strong style="color: #dc3545;">${p.stock_level}</strong>
                </div>
              </div>
            `).join('')}
          </div>
          ` : ''}

          <div class="footer">
            <p>Bu rapor otomatik olarak oluşturulmuştur.</p>
            <p>Dynamic Pricing System © ${new Date().getFullYear()}</p>
          </div>
        </div>
      </body>
      </html>
    `;
  }

  async sendReport(report) {
    if (!this.enabled || !this.transporter) {
      console.log('⚠️  Email service not configured. Report not sent.');
      return { success: false, message: 'Email service not configured' };
    }

    try {
      const info = await this.transporter.sendMail({
        from: this.transporter.options.auth.user,
        to: this.recipients.join(', '),
        subject: report.subject,
        html: report.html
      });

      console.log('✅ Email report sent:', info.messageId);
      return { success: true, messageId: info.messageId };
    } catch (error) {
      console.error('❌ Error sending email:', error);
      return { success: false, error: error.message };
    }
  }

  async sendDailyReport() {
    const report = await this.generateDailyReport();
    return await this.sendReport(report);
  }

  scheduleDailyReport(hour = 9, minute = 0) {
    if (!this.enabled) {
      console.log('⚠️  Email service not configured. Daily reports not scheduled.');
      return false;
    }

    cron.schedule(`${minute} ${hour} * * *`, async () => {
      console.log(`📧 Sending daily report at ${hour}:${minute}...`);
      await this.sendDailyReport();
    });

    console.log(`✅ Daily reports scheduled for ${hour}:${String(minute).padStart(2, '0')} every day`);
    return true;
  }

  scheduleWeeklyReport(dayOfWeek = 1, hour = 9, minute = 0) {
    if (!this.enabled) {
      console.log('⚠️  Email service not configured. Weekly reports not scheduled.');
      return false;
    }

    cron.schedule(`${minute} ${hour} * * ${dayOfWeek}`, async () => {
      console.log(`📧 Sending weekly report...`);
      await this.sendDailyReport();
    });

    const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
    console.log(`✅ Weekly reports scheduled for ${days[dayOfWeek]} at ${hour}:${String(minute).padStart(2, '0')}`);
    return true;
  }
}

const emailService = new EmailReportService();

module.exports = emailService;
