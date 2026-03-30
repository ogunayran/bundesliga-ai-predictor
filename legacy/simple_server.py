#!/usr/bin/env python3
"""Basit HTTP server - Flask olmadan direkt çalışır"""

import http.server
import socketserver
import json
import sqlite3
from urllib.parse import urlparse, parse_qs
import sys
import os

# Proje dizinine geç
os.chdir('/Users/ogunayran/CascadeProjects/windsurf-project-6')

DB_PATH = 'superlig_full.db'

# AI Predictor'ı yükle
from advanced_predictor import AdvancedSuperLigPredictor
from betting_system import BettingRecommendationSystem

predictor = AdvancedSuperLigPredictor(DB_PATH)
betting_system = BettingRecommendationSystem(DB_PATH)

# Modeli yükle
try:
    predictor.load_model('superlig_model.pkl')
    print("✅ AI Model yüklendi (Doğruluk: 57.2%)")
except Exception as e:
    print(f"⚠️  Model yüklenemedi: {e}")

class SuperLigHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Ana sayfa
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            with open('templates/index_advanced.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        
        # API endpoints
        elif parsed_path.path == '/api/stats':
            self.send_json(self.get_stats())
            return
            
        elif parsed_path.path == '/api/predictions':
            self.send_json(self.get_predictions())
            return
            
        elif parsed_path.path == '/api/safe-coupon':
            self.send_json(self.get_safe_coupon())
            return
            
        elif parsed_path.path == '/api/risky-coupon':
            self.send_json(self.get_risky_coupon())
            return
            
        elif parsed_path.path == '/api/teams':
            self.send_json(self.get_teams())
            return
        
        else:
            # Diğer dosyalar için default handler
            super().do_GET()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def get_stats(self):
        """Sistem istatistikleri"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM matches')
            total_matches = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT season) FROM matches')
            total_seasons = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM teams')
            total_teams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM matches WHERE season = "current_week"')
            current_week_matches = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_matches': total_matches,
                'total_seasons': total_seasons,
                'total_teams': total_teams,
                'current_week_matches': current_week_matches,
                'model_accuracy': 0.572
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_predictions(self):
        """Güncel hafta tahminleri - Gerçek AI modeli kullanarak"""
        try:
            # AI predictor'dan gerçek tahminleri al
            predictions = predictor.predict_upcoming_matches()
            return predictions
            
        except Exception as e:
            print(f"Tahmin hatası: {e}")
            return {'error': str(e)}
    
    def get_safe_coupon(self):
        """Güvenli kupon önerisi"""
        try:
            coupon = betting_system.generate_safe_coupon()
            return coupon
        except Exception as e:
            print(f"Güvenli kupon hatası: {e}")
            return {'error': str(e)}
    
    def get_risky_coupon(self):
        """Riskli kupon önerisi"""
        try:
            coupon = betting_system.generate_risky_coupon()
            return coupon
        except Exception as e:
            print(f"Riskli kupon hatası: {e}")
            return {'error': str(e)}
    
    def get_teams(self):
        """Takım listesi"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name FROM teams ORDER BY name')
            teams = [{'id': row[0], 'name': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            return teams
            
        except Exception as e:
            return {'error': str(e)}

PORT = 8080

print("="*70)
print("🏆 SÜPER LİG AI TAHMİN SİSTEMİ")
print("="*70)
print(f"\n✅ Server başlatılıyor: http://localhost:{PORT}")
print(f"✅ Tarayıcınızda açın: http://localhost:{PORT}")
print("\n⏹  Durdurmak için: CTRL+C")
print("="*70)

with socketserver.TCPServer(("", PORT), SuperLigHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹  Server durduruldu")
        sys.exit(0)
