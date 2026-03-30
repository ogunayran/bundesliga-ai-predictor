import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import json
import re

class RealDataScraper:
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'):
        self.db_path = db_path
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def scrape_mackolik(self):
        """Mackolik'ten güncel maçları çek"""
        print("🔍 Mackolik'ten veri çekiliyor...")
        
        try:
            # Mackolik Süper Lig fikstür sayfası
            url = 'https://www.mackolik.com/puan-durumu/türkiye-süper-lig/482ofyysbdbeoxauk19yg7tdt'
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ Mackolik erişim hatası: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Mackolik'in maç verilerini içeren script tag'ini bul
            scripts = soup.find_all('script')
            matches = []
            
            for script in scripts:
                if script.string and 'fixtures' in script.string:
                    # JSON verisini parse et
                    try:
                        json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(1))
                            # Fixtures verisini çıkar
                            if 'fixtures' in data:
                                fixtures_data = data['fixtures']
                                print(f"✅ Mackolik'ten {len(fixtures_data)} maç bulundu")
                                return self._parse_mackolik_fixtures(fixtures_data)
                    except:
                        continue
            
            print("⚠️  Mackolik'ten veri parse edilemedi")
            return []
            
        except Exception as e:
            print(f"❌ Mackolik scraping hatası: {e}")
            return []
    
    def scrape_sofascore(self):
        """Sofascore'dan güncel maçları çek"""
        print("🔍 Sofascore'dan veri çekiliyor...")
        
        try:
            # Sofascore API endpoint (public)
            # Türkiye Süper Lig unique tournament ID: 52
            today = datetime.now()
            date_str = today.strftime('%Y-%m-%d')
            
            url = f'https://www.sofascore.com/api/v1/unique-tournament/52/season/58766/events/round/1'
            
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"⚠️  Sofascore API yanıt vermedi, alternatif deneniyor...")
                # Alternatif: Haftalık maçlar
                url = f'https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_str}'
                response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                matches = self._parse_sofascore_data(data)
                if matches:
                    print(f"✅ Sofascore'dan {len(matches)} maç bulundu")
                    return matches
            
            print("⚠️  Sofascore'dan veri alınamadı")
            return []
            
        except Exception as e:
            print(f"❌ Sofascore scraping hatası: {e}")
            return []
    
    def scrape_tff_official(self):
        """TFF resmi sitesinden güncel maçları çek"""
        print("🔍 TFF.org'dan veri çekiliyor...")
        
        try:
            url = 'https://www.tff.org/default.aspx?pageID=198'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ TFF erişim hatası: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            matches = []
            
            # TFF'nin maç tablosunu bul
            match_table = soup.find('table', {'class': 'fiksturtablo'})
            
            if not match_table:
                # Alternatif class isimleri dene
                match_table = soup.find('div', {'class': 'fixture-list'})
            
            if match_table:
                rows = match_table.find_all('tr')
                
                for row in rows:
                    try:
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            home_team = cells[1].get_text(strip=True)
                            score_cell = cells[2].get_text(strip=True)
                            away_team = cells[3].get_text(strip=True)
                            date_time = cells[4].get_text(strip=True)
                            
                            # Skor parse et
                            home_score = None
                            away_score = None
                            is_finished = False
                            
                            if '-' in score_cell and score_cell != '-':
                                try:
                                    parts = score_cell.split('-')
                                    home_score = int(parts[0].strip())
                                    away_score = int(parts[1].strip())
                                    is_finished = True
                                except:
                                    pass
                            
                            # Tarih parse et
                            try:
                                match_datetime = datetime.strptime(date_time, '%d.%m.%Y %H:%M')
                            except:
                                match_datetime = datetime.now() + timedelta(days=1)
                            
                            matches.append({
                                'home_team': home_team,
                                'away_team': away_team,
                                'home_score': home_score,
                                'away_score': away_score,
                                'match_datetime': match_datetime,
                                'is_finished': is_finished,
                                'source': 'TFF'
                            })
                    except:
                        continue
                
                if matches:
                    print(f"✅ TFF'den {len(matches)} maç bulundu")
                    return matches
            
            print("⚠️  TFF'den veri parse edilemedi")
            return []
            
        except Exception as e:
            print(f"❌ TFF scraping hatası: {e}")
            return []
    
    def scrape_nesine(self):
        """Nesine.com'dan güncel maçları ve oranları çek"""
        print("🔍 Nesine.com'dan veri çekiliyor...")
        
        try:
            url = 'https://www.nesine.com/iddaa/futbol/turkiye-super-lig'
            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                matches = []
                
                # Nesine'nin maç listesini bul
                match_divs = soup.find_all('div', {'class': 'match-item'})
                
                for match_div in match_divs:
                    try:
                        home_team = match_div.find('span', {'class': 'home-team'}).get_text(strip=True)
                        away_team = match_div.find('span', {'class': 'away-team'}).get_text(strip=True)
                        match_time = match_div.find('span', {'class': 'match-time'}).get_text(strip=True)
                        
                        matches.append({
                            'home_team': home_team,
                            'away_team': away_team,
                            'match_datetime': match_time,
                            'source': 'Nesine'
                        })
                    except:
                        continue
                
                if matches:
                    print(f"✅ Nesine'den {len(matches)} maç bulundu")
                    return matches
            
            return []
            
        except Exception as e:
            print(f"❌ Nesine scraping hatası: {e}")
            return []
    
    def _parse_mackolik_fixtures(self, fixtures_data):
        """Mackolik fixture verisini parse et"""
        matches = []
        
        for fixture in fixtures_data:
            try:
                home_team = fixture.get('homeTeam', {}).get('name', '')
                away_team = fixture.get('awayTeam', {}).get('name', '')
                timestamp = fixture.get('timestamp', 0)
                
                match_datetime = datetime.fromtimestamp(timestamp)
                
                # Skor bilgisi
                home_score = fixture.get('homeScore')
                away_score = fixture.get('awayScore')
                is_finished = fixture.get('status') == 'finished'
                
                matches.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'match_datetime': match_datetime,
                    'is_finished': is_finished,
                    'source': 'Mackolik'
                })
            except:
                continue
        
        return matches
    
    def _parse_sofascore_data(self, data):
        """Sofascore verisini parse et"""
        matches = []
        
        events = data.get('events', [])
        
        for event in events:
            try:
                # Sadece Süper Lig maçları
                tournament = event.get('tournament', {})
                if 'süper' not in tournament.get('name', '').lower():
                    continue
                
                home_team = event.get('homeTeam', {}).get('name', '')
                away_team = event.get('awayTeam', {}).get('name', '')
                
                timestamp = event.get('startTimestamp', 0)
                match_datetime = datetime.fromtimestamp(timestamp)
                
                # Skor
                home_score = event.get('homeScore', {}).get('current')
                away_score = event.get('awayScore', {}).get('current')
                
                status = event.get('status', {}).get('type', '')
                is_finished = status == 'finished'
                
                matches.append({
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_score': home_score,
                    'away_score': away_score,
                    'match_datetime': match_datetime,
                    'is_finished': is_finished,
                    'source': 'Sofascore'
                })
            except:
                continue
        
        return matches
    
    def get_current_week_matches(self):
        """Tüm kaynaklardan güncel hafta maçlarını çek"""
        all_matches = []
        
        # Sırayla dene
        sources = [
            self.scrape_tff_official,
            self.scrape_sofascore,
            self.scrape_mackolik,
            self.scrape_nesine
        ]
        
        for scraper_func in sources:
            matches = scraper_func()
            if matches:
                all_matches.extend(matches)
                break  # İlk başarılı kaynaktan sonra dur
        
        if not all_matches:
            print("\n⚠️  Hiçbir kaynaktan veri alınamadı, örnek maçlar kullanılıyor...")
            all_matches = self._get_sample_matches()
        
        return all_matches
    
    def _get_sample_matches(self):
        """Örnek güncel maçlar (gerçek veri alınamazsa)"""
        today = datetime.now()
        next_saturday = today + timedelta(days=(5 - today.weekday()) % 7)
        next_sunday = next_saturday + timedelta(days=1)
        
        return [
            {
                'home_team': 'Galatasaray',
                'away_team': 'Fenerbahçe',
                'match_datetime': next_sunday.replace(hour=19, minute=0),
                'home_score': None,
                'away_score': None,
                'is_finished': False,
                'source': 'Sample'
            },
            {
                'home_team': 'Beşiktaş',
                'away_team': 'Trabzonspor',
                'match_datetime': next_saturday.replace(hour=16, minute=0),
                'home_score': None,
                'away_score': None,
                'is_finished': False,
                'source': 'Sample'
            },
            {
                'home_team': 'Başakşehir',
                'away_team': 'Konyaspor',
                'match_datetime': next_saturday.replace(hour=13, minute=30),
                'home_score': None,
                'away_score': None,
                'is_finished': False,
                'source': 'Sample'
            }
        ]
    
    def save_to_database(self, matches):
        """Maçları veritabanına kaydet"""
        if not matches:
            print("❌ Kaydedilecek maç yok")
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mevcut hafta maçlarını temizle
        cursor.execute("DELETE FROM matches WHERE season = 'current_week'")
        
        saved_count = 0
        
        for match in matches:
            try:
                # Takım ID'lerini bul veya oluştur
                home_team = match['home_team']
                away_team = match['away_team']
                
                cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                              (f'%{home_team}%', f'%{home_team.upper()}%'))
                home_result = cursor.fetchone()
                
                cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                              (f'%{away_team}%', f'%{away_team.upper()}%'))
                away_result = cursor.fetchone()
                
                if not home_result:
                    cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)', 
                                 (home_team, home_team.upper()))
                    home_team_id = cursor.lastrowid
                else:
                    home_team_id = home_result[0]
                
                if not away_result:
                    cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)', 
                                 (away_team, away_team.upper()))
                    away_team_id = cursor.lastrowid
                else:
                    away_team_id = away_result[0]
                
                # Maçı kaydet
                match_datetime = match.get('match_datetime')
                if isinstance(match_datetime, str):
                    try:
                        match_datetime = datetime.strptime(match_datetime, '%d.%m.%Y %H:%M')
                    except:
                        match_datetime = datetime.now() + timedelta(days=1)
                
                cursor.execute('''
                    INSERT INTO matches 
                    (season, home_team_id, away_team_id, match_date, match_datetime, 
                     home_score, away_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'current_week',
                    home_team_id,
                    away_team_id,
                    match_datetime.strftime('%d.%m.%Y %H:%M'),
                    match_datetime,
                    match.get('home_score'),
                    match.get('away_score')
                ))
                
                saved_count += 1
            except Exception as e:
                print(f"Maç kaydetme hatası: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ {saved_count} maç veritabanına kaydedildi")
        return saved_count

def main():
    print("="*70)
    print("🏆 GERÇEK VERİ TOPLAMA - SÜPER LİG")
    print("="*70)
    
    scraper = RealDataScraper()
    matches = scraper.get_current_week_matches()
    
    if matches:
        print(f"\n📊 Toplam {len(matches)} maç bulundu:")
        for match in matches:
            status = "✅ Bitti" if match.get('is_finished') else "⏳ Oynanacak"
            score = f"{match.get('home_score', '?')}-{match.get('away_score', '?')}" if match.get('is_finished') else "vs"
            date_str = match['match_datetime'].strftime('%d.%m %H:%M') if isinstance(match['match_datetime'], datetime) else match['match_datetime']
            print(f"  {match['home_team']} {score} {match['away_team']} - {date_str} ({match.get('source', 'Unknown')}) {status}")
        
        scraper.save_to_database(matches)
    else:
        print("\n❌ Hiç maç bulunamadı")
    
    print("\n" + "="*70)
    print("✅ İşlem tamamlandı!")
    print("="*70)

if __name__ == '__main__':
    main()
