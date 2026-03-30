#!/usr/bin/env python3
import os
import sys
import subprocess

def check_file_exists(filepath, description):
    if os.path.exists(filepath):
        print(f"✅ {description} bulundu")
        return True
    else:
        print(f"❌ {description} bulunamadı: {filepath}")
        return False

def run_command(command, description):
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} tamamlandı")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} başarısız: {e}")
        if e.stdout:
            print(f"Çıktı: {e.stdout}")
        if e.stderr:
            print(f"Hata: {e.stderr}")
        return False

def main():
    print("="*60)
    print("🤖 SÜPER LİG AI - HIZLI BAŞLANGIÇ")
    print("="*60)
    
    # Kontroller
    print("\n📋 Ön Kontroller:")
    
    data_path = '/Users/ogunayran/Downloads/TFF_Data'
    if not check_file_exists(data_path, "TFF_Data klasörü"):
        print("\n⚠️  Lütfen önce TFF_Data klasörünü doğru konuma yerleştirin!")
        sys.exit(1)
    
    # Sezon sayısını kontrol et
    seasons = [d for d in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, d)) and '_' in d]
    print(f"✅ {len(seasons)} sezon verisi bulundu")
    
    # Adım 1: Veri Entegrasyonu
    print("\n" + "="*60)
    print("ADIM 1/3: VERİ ENTEGRASYONU")
    print("="*60)
    
    db_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'
    
    if os.path.exists(db_path):
        response = input("\n⚠️  Veritabanı zaten mevcut. Yeniden oluşturulsun mu? (e/h): ")
        if response.lower() == 'e':
            os.remove(db_path)
            print("🗑️  Eski veritabanı silindi")
    
    if not os.path.exists(db_path):
        if not run_command("python3 data_integration.py", "Veri entegrasyonu"):
            print("\n❌ Veri entegrasyonu başarısız oldu!")
            sys.exit(1)
    else:
        print("✅ Veritabanı mevcut, atlanıyor")
    
    # Adım 2: 2022-2026 Verileri
    print("\n" + "="*60)
    print("ADIM 2/3: YENİ SEZONLAR (2022-2026)")
    print("="*60)
    
    response = input("\n2022-2026 sezonları için veri toplanacak. Devam? (e/h): ")
    if response.lower() == 'e':
        run_command("python3 scraper_2022_2026.py", "Yeni sezon verilerini toplama")
        # Yeni verileri entegre et
        run_command("python3 data_integration.py", "Yeni verileri veritabanına ekleme")
    
    # Adım 3: Model Eğitimi
    print("\n" + "="*60)
    print("ADIM 3/3: AI MODEL EĞİTİMİ")
    print("="*60)
    
    model_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_model.pkl'
    
    if os.path.exists(model_path):
        response = input("\n⚠️  Model zaten mevcut. Yeniden eğitilsin mi? (e/h): ")
        if response.lower() != 'e':
            print("✅ Mevcut model kullanılacak")
        else:
            if not run_command("python3 advanced_predictor.py", "Model eğitimi (5-10 dakika sürebilir)"):
                print("\n❌ Model eğitimi başarısız oldu!")
                sys.exit(1)
    else:
        print("\n⚠️  Model bulunamadı, eğitim başlatılıyor...")
        if not run_command("python3 advanced_predictor.py", "Model eğitimi (5-10 dakika sürebilir)"):
            print("\n❌ Model eğitimi başarısız oldu!")
            sys.exit(1)
    
    # Tamamlandı
    print("\n" + "="*60)
    print("✅ KURULUM TAMAMLANDI!")
    print("="*60)
    print("\n📊 Sistem Hazır!")
    print("\nUygulamayı başlatmak için:")
    print("  python3 app_advanced.py")
    print("\nTarayıcıda açın:")
    print("  http://localhost:5000")
    print("\n" + "="*60)
    
    response = input("\nUygulamayı şimdi başlatmak ister misiniz? (e/h): ")
    if response.lower() == 'e':
        print("\n🚀 Uygulama başlatılıyor...")
        os.system("python3 app_advanced.py")

if __name__ == '__main__':
    main()
