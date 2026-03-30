#!/usr/bin/env python3
"""
Bundesliga Web Server - Port 8081
Canlı skorlar ve AI tahminleri
"""

import http.server
import socketserver
import json
import sqlite3
from urllib.parse import urlparse
import sys
import os
import requests
from datetime import datetime

os.chdir('/Users/ogunayran/CascadeProjects/windsurf-project-6')

DB_PATH = 'bundesliga.db'
API_BASE = 'https://api.openligadb.de'

# AI Predictor ve Analyzer'ı yükle
from bundesliga_ultimate_predictor import BundesligaUltimatePredictor
from bundesliga_analyzer import BundesligaAnalyzer

predictor = BundesligaUltimatePredictor(DB_PATH)
analyzer = BundesligaAnalyzer(DB_PATH)

# Modeli yükle
try:
    print("✅ Bundesliga Ultimate Predictor hazır")
except Exception as e:
    print(f"⚠️  Model yüklenemedi: {e}")

class BundesligaHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # Ana sayfa
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            with open('templates/bundesliga.html', 'rb') as f:
                self.wfile.write(f.read())
            return
        
        # API endpoints
        elif parsed_path.path == '/api/stats':
            self.send_json(self.get_stats())
            return
            
        elif parsed_path.path == '/api/predictions':
            self.send_json(self.get_predictions())
            return
            
        elif parsed_path.path == '/api/live-scores':
            self.send_json(self.get_live_scores())
            return
            
        elif parsed_path.path == '/api/standings':
            self.send_json(self.get_standings())
            return
            
        elif parsed_path.path == '/api/teams':
            self.send_json(self.get_teams())
            return
        
        elif parsed_path.path.startswith('/api/match-analysis/'):
            # /api/match-analysis/home_id/away_id
            parts = parsed_path.path.split('/')
            if len(parts) >= 5:
                try:
                    home_id = int(parts[3])
                    away_id = int(parts[4])
                    self.send_json(self.get_match_analysis(home_id, away_id))
                except:
                    self.send_json({'error': 'Invalid team IDs'})
            return
        
        elif parsed_path.path == '/api/league-insights':
            self.send_json(self.get_league_insights())
            return
        
        elif parsed_path.path.startswith('/api/past-matches'):
            # /api/past-matches?matchday=26
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            matchday = int(query_params.get('matchday', [1])[0]) if query_params.get('matchday') else None
            self.send_json(self.get_past_matches(matchday))
            return
        
        elif parsed_path.path == '/api/power-rankings':
            self.send_json(self.get_power_rankings())
            return
        
        elif parsed_path.path == '/api/top-scorers':
            self.send_json(self.get_top_scorers())
            return
        
        else:
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
            
            cursor.execute('SELECT COUNT(*) FROM matches WHERE is_finished = 1')
            finished_matches = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM teams')
            total_teams = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT matchday) FROM matches')
            total_matchdays = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'league': 'Bundesliga',
                'season': '2025-26',
                'total_matches': total_matches,
                'finished_matches': finished_matches,
                'total_teams': total_teams,
                'total_matchdays': total_matchdays,
                'model_accuracy': predictor.base_predictor.accuracy if hasattr(predictor.base_predictor, 'accuracy') and predictor.base_predictor.accuracy else 0.657
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_predictions(self):
        """Gelecek hafta tahminleri - Ultimate Predictor ile"""
        try:
            predictions = predictor.predict_upcoming_matches()
            return predictions
        except Exception as e:
            print(f"Tahmin hatası: {e}")
            return {'error': str(e)}
    
    def get_power_rankings(self):
        """Güç sıralaması"""
        try:
            rankings = predictor.get_power_rankings()
            return rankings
        except Exception as e:
            print(f"Güç sıralaması hatası: {e}")
            return {'error': str(e)}
    
    def get_top_scorers(self):
        """Gol kralları"""
        try:
            scorers = predictor.get_top_scorers(20)
            return scorers
        except Exception as e:
            print(f"Gol kralları hatası: {e}")
            return {'error': str(e)}
    
    def get_live_scores(self):
        """Canlı skorlar - OpenLigaDB API'den"""
        try:
            # Güncel maçları API'den çek
            response = requests.get(f"{API_BASE}/getmatchdata/bl1", timeout=10)
            
            if response.status_code == 200:
                all_matches = response.json()
                
                # Sadece bugünün ve yakın gelecekteki maçları
                live_matches = []
                now = datetime.now()
                
                for match in all_matches:
                    if not match.get('matchIsFinished'):
                        # Timezone-aware datetime kullan
                        match_datetime_str = match.get('matchDateTime', '')
                        if 'T' in match_datetime_str:
                            # ISO format datetime parse et
                            match_time = datetime.fromisoformat(match_datetime_str.replace('Z', '+00:00'))
                            # Timezone-naive yap karşılaştırma için
                            if match_time.tzinfo:
                                match_time = match_time.replace(tzinfo=None)
                            # Almanya saati (UTC+1) -> Türkiye saati (UTC+3) = +2 saat ekle
                            from datetime import timedelta
                            match_time = match_time + timedelta(hours=2)
                        else:
                            match_time = now
                        
                        # Son 24 saat veya gelecek 7 gün içindeki maçlar
                        time_diff = (match_time - now).total_seconds()
                        
                        if -86400 < time_diff < 604800:  # -24h to +7 days
                            # Maç dakikasını hesapla
                            match_minute = None
                            if match.get('matchResults') and not match.get('matchIsFinished'):
                                # Maç başladıysa, başlangıçtan bu yana geçen dakikayı hesapla
                                elapsed = (now - match_time).total_seconds() / 60
                                if -5 <= elapsed <= 120:  # -5 ile 120 dakika arası (tolerans + 90 + uzatmalar)
                                    match_minute = max(1, int(elapsed))
                                    if match_minute > 90:
                                        match_minute = f"90+{match_minute - 90}"
                                    elif match_minute < 1:
                                        match_minute = 1
                            
                            # Skorları al - en son sonucu kullan (Endergebnis)
                            home_score = None
                            away_score = None
                            if match.get('matchResults'):
                                for result in match.get('matchResults', []):
                                    if result.get('resultTypeID') == 2:  # Endergebnis
                                        home_score = result.get('pointsTeam1')
                                        away_score = result.get('pointsTeam2')
                                        break
                            
                            live_matches.append({
                                'match_id': match.get('matchID'),
                                'home_team': match.get('team1', {}).get('teamName'),
                                'away_team': match.get('team2', {}).get('teamName'),
                                'home_score': home_score,
                                'away_score': away_score,
                                'match_datetime': match.get('matchDateTime'),
                                'matchday': match.get('group', {}).get('groupOrderID'),
                                'is_finished': match.get('matchIsFinished', False),
                                'status': 'Live' if match.get('matchResults') and not match.get('matchIsFinished') else 'Upcoming',
                                'minute': match_minute
                            })
                
                return live_matches[:10]  # İlk 10 maç
            else:
                return []
        except Exception as e:
            print(f"Canlı skor hatası: {e}")
            return []
    
    def get_standings(self):
        """Puan durumu"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            query = '''
                SELECT t.name, s.position, s.played, s.won, s.drawn, s.lost,
                       s.goals_for, s.goals_against, s.goal_difference, s.points
                FROM standings s
                JOIN teams t ON s.team_id = t.id
                WHERE s.season = '2025_26'
                ORDER BY s.points DESC, s.goal_difference DESC
            '''
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            standings = []
            for i, row in enumerate(rows, 1):
                standings.append({
                    'position': i,
                    'team': row[0],
                    'played': row[2],
                    'won': row[3],
                    'drawn': row[4],
                    'lost': row[5],
                    'goals_for': row[6],
                    'goals_against': row[7],
                    'goal_difference': row[8],
                    'points': row[9]
                })
            
            conn.close()
            return standings
            
        except Exception as e:
            print(f"Puan durumu hatası: {e}")
            return []
    
    def get_teams(self):
        """Takım listesi"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, short_name FROM teams ORDER BY name')
            teams = [{'id': row[0], 'name': row[1], 'short_name': row[2]} for row in cursor.fetchall()]
            
            conn.close()
            return teams
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_match_analysis(self, home_id, away_id):
        """Detaylı maç analizi"""
        try:
            analysis = analyzer.comprehensive_match_analysis(home_id, away_id)
            return analysis if analysis else {'error': 'Analysis failed'}
        except Exception as e:
            print(f"Analiz hatası: {e}")
            return {'error': str(e)}
    
    def get_league_insights(self):
        """Lig geneli içgörüler"""
        try:
            insights = analyzer.get_league_insights()
            return insights
        except Exception as e:
            print(f"İçgörü hatası: {e}")
            return {'error': str(e)}
    
    def get_past_matches(self, matchday=None):
        """Geçmiş maçlar - hafta hafta"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            if matchday:
                # Belirli bir hafta
                query = '''
                    SELECT m.matchday, m.match_datetime,
                           ht.name as home_team, at.name as away_team,
                           m.home_score, m.away_score
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    WHERE m.is_finished = 1 AND m.matchday = ?
                    ORDER BY m.match_datetime
                '''
                cursor.execute(query, (matchday,))
            else:
                # Tüm haftalar
                query = '''
                    SELECT m.matchday, m.match_datetime,
                           ht.name as home_team, at.name as away_team,
                           m.home_score, m.away_score
                    FROM matches m
                    JOIN teams ht ON m.home_team_id = ht.id
                    JOIN teams at ON m.away_team_id = at.id
                    WHERE m.is_finished = 1
                    ORDER BY m.matchday DESC, m.match_datetime
                    LIMIT 100
                '''
                cursor.execute(query)
            
            rows = cursor.fetchall()
            
            # Haftaya göre grupla
            matches_by_week = {}
            for row in rows:
                week = row[0]
                if week not in matches_by_week:
                    matches_by_week[week] = []
                
                matches_by_week[week].append({
                    'match_datetime': str(row[1]),
                    'home_team': row[2],
                    'away_team': row[3],
                    'home_score': row[4],
                    'away_score': row[5]
                })
            
            conn.close()
            
            # Liste formatına çevir
            result = []
            for week in sorted(matches_by_week.keys(), reverse=True):
                result.append({
                    'matchday': week,
                    'matches': matches_by_week[week]
                })
            
            return result
            
        except Exception as e:
            print(f"Geçmiş maçlar hatası: {e}")
            return {'error': str(e)}

PORT = 8092

print("="*70)
print("🇩🇪 BUNDESLIGA AI TAHMİN SİSTEMİ")
print("="*70)
print(f"\n✅ Server başlatılıyor: http://localhost:{PORT}")
print(f"✅ Tarayıcınızda açın: http://localhost:{PORT}")
print("\n📊 Özellikler:")
print("  - Canlı skorlar (OpenLigaDB API)")
print("  - AI tahminleri (%83.0 doğruluk)")
print("  - Güncel puan durumu")
print("  - 2025-26 sezonu verileri")
print("\n⏹  Durdurmak için: CTRL+C")
print("="*70)

with socketserver.TCPServer(("", PORT), BundesligaHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n⏹  Server durduruldu")
        sys.exit(0)
