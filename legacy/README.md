# Süper Lig İddia Botu

Türkiye Süper Lig maçları için tahminler ve analizler sunan akıllı bahis botu.

## Özellikler

- 🤖 **Makine Öğrenmesi Tahminleri**: RandomForest algoritması ile maç sonuçlarını tahmin etme
- 📊 **Canlı Veri Analizi**: Takım formları, gol istatistikleri ve başa baş maçlar
- 🎯 **Güven Oranları**: Her tahmin için yüzde bazında güven skoru
- 📈 **Puan Durumu**: Güncel Süper Lig sıralaması
- 🎨 **Modern Arayüz**: Bootstrap 5 ile responsive ve şık tasarım
- 🔄 **Otomatik Güncelleme**: 5 dakikada bir verileri otomatik yenileme

## Kurulum

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Veritabanını başlatın ve örnek verileri yükleyin:
```bash
python data_collector.py
```

3. Uygulamayı çalıştırın:
```bash
python app.py
```

4. Tarayıcıda açın: `http://localhost:5000`

## Proje Yapısı

```
├── app.py              # Flask ana uygulama dosyası
├── data_collector.py   # Veri toplama ve veritabanı işlemleri
├── predictor.py        # Makine öğrenmesi tahmin motoru
├── templates/
│   └── index.html     # Ana web arayüzü
├── requirements.txt    # Python bağımlılıkları
├── superlig.db        # SQLite veritabanı
└── README.md          # Proje dokümantasyonu
```

## Tahmin Algoritması

Bot şu faktörleri dikkate alarak tahmin yapar:

- **Takım Puanları**: Güncel lig sıralaması ve puan durumu
- **Gol Farkı**: Atılan ve yenilen gollerin dengesi
- **Takım Formu**: Son 5 maçtaki performans
- **Gol İstatistikleri**: Ortalama atan ve yenilen goller
- **Başa Baş Maçlar**: İki takım arasındaki geçmiş maç sonuçları

## API Endpoints

- `GET /` - Ana sayfa
- `GET /api/predictions` - Güncel tahminler
- `GET /api/standings` - Puan durumu
- `GET /api/matches` - Yaklaşan maçlar

## Veritabanı Şeması

### Teams Tablosu
- id, name, founded_year, stadium, capacity

### Matches Tablosu  
- id, home_team_id, away_team_id, match_date, home_score, away_score
- home_goals, away_goals, home_shots, away_shots
- home_possession, away_possession, season, match_day

### Standings Tablosu
- id, team_id, season, match_day, position, played
- won, drawn, lost, goals_for, goals_against, goal_difference, points

## Güven Seviyeleri

- 🟢 **Yüksek Güven (70%+)**: Güçlü istatistiksel dayanak
- 🟡 **Orta Güven (50-70%)**: Dengeli tahminler  
- 🔴 **Düşük Güven (<50%)**: Belirsiz maçlar

## Geliştirme

### Yeni Özellikler Ekleme
1. `data_collector.py`'ye yeni veri kaynakları ekleyin
2. `predictor.py`'de yeni özellikler (features) tanımlayın
3. `templates/index.html`'de arayüzü güncelleyin

### Model İyileştirme
- Daha fazla veri toplama
- Farklı ML algoritmaları deneme
- Feature engineering geliştirme

## Lisans

Bu proje eğitim amaçlıdır ve gerçek bahis için kullanılmamalıdır.

## Katkı

Hata raporları ve feature requests için GitHub issues kullanabilirsiniz.
