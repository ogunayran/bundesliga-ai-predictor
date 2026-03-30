#!/bin/bash

echo "=================================="
echo "Süper Lig AI - Kurulum Scripti"
echo "=================================="

# 1. Veritabanını oluştur ve mevcut verileri yükle
echo ""
echo "1/4 - Veritabanı oluşturuluyor ve 1990-2021 verileri yükleniyor..."
python3 data_integration.py

if [ $? -ne 0 ]; then
    echo "HATA: Veri entegrasyonu başarısız!"
    exit 1
fi

# 2. 2022-2026 verilerini topla
echo ""
echo "2/4 - 2022-2026 sezonları için veri toplanıyor..."
python3 scraper_2022_2026.py

# 3. AI modelini eğit
echo ""
echo "3/4 - AI modeli eğitiliyor (bu işlem 5-10 dakika sürebilir)..."
python3 advanced_predictor.py

if [ $? -ne 0 ]; then
    echo "HATA: Model eğitimi başarısız!"
    exit 1
fi

# 4. Tamamlandı
echo ""
echo "=================================="
echo "✅ Kurulum tamamlandı!"
echo "=================================="
echo ""
echo "Uygulamayı başlatmak için:"
echo "  python3 app_advanced.py"
echo ""
echo "Tarayıcıda açın:"
echo "  http://localhost:5000"
echo ""
echo "=================================="
