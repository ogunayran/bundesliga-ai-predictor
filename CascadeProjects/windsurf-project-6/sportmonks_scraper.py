import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import time

class SportMonksScraper:
    def __init__(self, api_token=None, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'):
        self.api_token = api_token
        self.base_url = 'https://api.sportmonks.com/v3/football'
        self.db_path = db_path
        self.headers = {
            'Accept': 'application/json'
        }
        
        # Türkiye Süper Lig ID'sini bulmak için leagues endpoint'ini kullan
        # Geçici olarak boş, get_superlig_id() ile bulacağız
        self.superlig_id = None
    
    def make_request(self, endpoint, params=None):
        """SportMonks API'ye istek gönder"""
        if not self.api_token:
            print("⚠️  API token gerekli! Lütfen SportMonks API token'ı ekleyin.")
            return None
        
        url = f"{self.base_url}/{endpoint}"
        
        if params is None:
            params = {}
        
        params['api_token'] = self.api_token
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                print("❌ API token geçersiz!")
                return None
            elif response.status_code == 429:
                print("⚠️  Rate limit aşıldı, 60 saniye bekleniyor...")
                time.sleep(60)
                return self.make_request(endpoint, params)
            else:
                print(f"❌ API hatası: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ İstek hatası: {e}")
            return None
    
    def find_superlig_id(self):
        """Türkiye Süper Lig ID'sini bul"""
        data = self.make_request('leagues', {
            'filters': 'leagueCountries:462'  # 462 = Turkey
        })
        
        if data and 'data' in data:
            for league in data['data']:
                name = league.get('name', '').lower()
                if 'süper' in name or 'super' in name or 'lig' in name:
                    league_id = league.get('id')
                    print(f"✅ Süper Lig bulundu: {league.get('name')} (ID: {league_id})")
                    return league_id
        
        print("⚠️  Süper Lig ID bulunamadı, varsayılan kullanılıyor")
        return 384  # Alternatif ID
    
    def get_current_season_id(self):
        """Aktif sezon ID'sini al"""
        if not self.superlig_id:
            self.superlig_id = self.find_superlig_id()
        
        data = self.make_request('leagues', {
            'include': 'currentSeason'
        })
        
        if data and 'data' in data:
            for league in data['data']:
                if league.get('id') == self.superlig_id:
                    current_season = league.get('currentSeason')
                    if current_season:
                        return current_season.get('id')
        
        return None
    
    def get_upcoming_fixtures(self, days_ahead=7):
        """Yaklaşan maçları al"""
        if not self.superlig_id:
            self.superlig_id = self.find_superlig_id()
        
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        
        params = {
            'include': 'participants;league;venue;state;scores',
            'filters': f'fixtureLeagues:{self.superlig_id}',
            'between': f"{today.strftime('%Y-%m-%d')},{end_date.strftime('%Y-%m-%d')}"
        }
        
        data = self.make_request('fixtures', params)
        
        if not data or 'data' not in data:
            print(f"API Response: {data}")
            return []
        
        fixtures = []
        
        for fixture in data['data']:
            try:
                # Participants kontrolü - bazen string array olabiliyor
                participants = fixture.get('participants', [])
                if not isinstance(participants, list) or len(participants) < 2:
                    continue
                
                # Takım isimlerini al
                home_team = ''
                away_team = ''
                
                if isinstance(participants[0], dict):
                    home_team = participants[0].get('name', participants[0].get('meta', {}).get('location') if isinstance(participants[0].get('meta'), dict) else '')
                    away_team = participants[1].get('name', participants[1].get('meta', {}).get('location') if isinstance(participants[1].get('meta'), dict) else '')
                
                if not home_team or not away_team:
                    continue
                
                starting_at = fixture.get('starting_at', '')
                if not starting_at:
                    continue
                    
                match_datetime = datetime.fromisoformat(starting_at.replace('Z', '+00:00'))
                
                state = fixture.get('state', {})
                if isinstance(state, dict):
                    is_finished = state.get('state') == 'FT'
                else:
                    is_finished = False
                
                scores = fixture.get('scores', [])
                home_score = None
                away_score = None
                
                if is_finished and isinstance(scores, list):
                    for score in scores:
                        if isinstance(score, dict) and score.get('description') == 'CURRENT':
                            score_data = score.get('score', {})
                            if isinstance(score_data, dict):
                                home_score = score_data.get('participant', {}).get('goals') if isinstance(score_data.get('participant'), dict) else None
                                away_score = score_data.get('goals')
                
                venue_data = fixture.get('venue', {})
                venue_name = venue_data.get('name', '') if isinstance(venue_data, dict) else ''
                
                league_data = fixture.get('league', {})
                league_name = league_data.get('name', 'Süper Lig') if isinstance(league_data, dict) else 'Süper Lig'
                
                fixtures.append({
                    'fixture_id': fixture.get('id'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'match_datetime': match_datetime,
                    'home_score': home_score,
                    'away_score': away_score,
                    'is_finished': is_finished,
                    'venue': venue_name,
                    'league': league_name
                })
            except Exception as e:
                print(f"Maç parse hatası ({type(e).__name__}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        return fixtures
    
    def get_season_fixtures(self, season_id):
        """Belirli bir sezonun tüm maçlarını al"""
        params = {
            'include': 'participants;scores;state',
            'filters': f'fixtureSeasons:{season_id}'
        }
        
        data = self.make_request('fixtures', params)
        
        if not data or 'data' not in data:
            return []
        
        fixtures = []
        
        for fixture in data['data']:
            try:
                participants = fixture.get('participants', [])
                if len(participants) < 2:
                    continue
                
                home_team = participants[0].get('name', '')
                away_team = participants[1].get('name', '')
                
                starting_at = fixture.get('starting_at', '')
                match_datetime = datetime.fromisoformat(starting_at.replace('Z', '+00:00'))
                
                state = fixture.get('state', {})
                is_finished = state.get('state') == 'FT'
                
                home_score = None
                away_score = None
                
                if is_finished:
                    scores = fixture.get('scores', [])
                    for score in scores:
                        if score.get('description') == 'CURRENT':
                            score_data = score.get('score', {})
                            home_score = score_data.get('participant', {}).get('goals')
                            away_score = score_data.get('goals')
                
                fixtures.append({
                    'fixture_id': fixture.get('id'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'match_datetime': match_datetime,
                    'home_score': home_score,
                    'away_score': away_score,
                    'is_finished': is_finished
                })
            except Exception as e:
                continue
        
        return fixtures
    
    def save_fixtures_to_db(self, fixtures, season='current_week'):
        """Maçları veritabanına kaydet"""
        if not fixtures:
            print("Kaydedilecek maç bulunamadı")
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mevcut sezon maçlarını temizle
        cursor.execute("DELETE FROM matches WHERE season = ?", (season,))
        
        saved_count = 0
        
        for fixture in fixtures:
            # Takım ID'lerini bul veya oluştur
            cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                          (f'%{fixture["home_team"]}%', f'%{fixture["home_team"].upper()}%'))
            home_result = cursor.fetchone()
            
            cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                          (f'%{fixture["away_team"]}%', f'%{fixture["away_team"].upper()}%'))
            away_result = cursor.fetchone()
            
            if not home_result:
                cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)', 
                             (fixture['home_team'], fixture['home_team'].upper()))
                home_team_id = cursor.lastrowid
            else:
                home_team_id = home_result[0]
            
            if not away_result:
                cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)', 
                             (fixture['away_team'], fixture['away_team'].upper()))
                away_team_id = cursor.lastrowid
            else:
                away_team_id = away_result[0]
            
            # Maçı kaydet
            cursor.execute('''
                INSERT INTO matches 
                (season, home_team_id, away_team_id, match_date, match_datetime, 
                 home_score, away_score, stadium)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                season,
                home_team_id,
                away_team_id,
                fixture['match_datetime'].strftime('%d.%m.%Y %H:%M'),
                fixture['match_datetime'],
                fixture['home_score'],
                fixture['away_score'],
                fixture.get('venue', '')
            ))
            
            saved_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"✅ {saved_count} maç veritabanına kaydedildi")
        return saved_count
    
    def update_current_week_matches(self):
        """Bu haftanın maçlarını güncelle"""
        print("🔄 Güncel maçlar alınıyor...")
        fixtures = self.get_upcoming_fixtures(days_ahead=7)
        
        if fixtures:
            print(f"📊 {len(fixtures)} maç bulundu")
            for f in fixtures:
                status = "✅ Bitti" if f['is_finished'] else "⏳ Oynanacak"
                score = f"{f['home_score']}-{f['away_score']}" if f['is_finished'] else "vs"
                print(f"  {f['home_team']} {score} {f['away_team']} - {status}")
            
            return self.save_fixtures_to_db(fixtures, 'current_week')
        else:
            print("❌ Maç bulunamadı")
            return 0

def main():
    print("="*60)
    print("🏆 SPORTMONKS API - SÜPER LİG VERİ ÇEKME")
    print("="*60)
    
    # API token
    api_token = "a4ySbAXYz6SksIhE1WmlnGK3DuWtmjGImEWf8EvLFNPpvf9oXpQ4Ls75y9Qi"
    
    scraper = SportMonksScraper(api_token=api_token)
    scraper.update_current_week_matches()
    
    print("\n" + "="*60)
    print("✅ İşlem tamamlandı!")
    print("="*60)

if __name__ == '__main__':
    main()
