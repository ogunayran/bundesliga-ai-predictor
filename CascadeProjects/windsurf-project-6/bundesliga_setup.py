#!/usr/bin/env python3
"""
Bundesliga Tahmin Sistemi - Kurulum
Gerçek 2024-25 sezonu verileriyle AI tahmin sistemi
"""

import requests
import sqlite3
from datetime import datetime
import json

class BundesligaSetup:
    def __init__(self):
        self.db_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/bundesliga.db'
        self.api_base = 'https://api.openligadb.de'
        
    def create_database(self):
        """Bundesliga için ayrı veritabanı oluştur"""
        print("📊 Bundesliga veritabanı oluşturuluyor...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Teams tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                short_name TEXT,
                team_icon_url TEXT,
                team_group_name TEXT
            )
        ''')
        
        # Matches tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER UNIQUE,
                season TEXT NOT NULL,
                matchday INTEGER,
                home_team_id INTEGER,
                away_team_id INTEGER,
                match_datetime DATETIME,
                home_score INTEGER,
                away_score INTEGER,
                is_finished BOOLEAN,
                location TEXT,
                stadium TEXT,
                FOREIGN KEY (home_team_id) REFERENCES teams(id),
                FOREIGN KEY (away_team_id) REFERENCES teams(id)
            )
        ''')
        
        # Standings tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT NOT NULL,
                team_id INTEGER,
                position INTEGER,
                played INTEGER,
                won INTEGER,
                drawn INTEGER,
                lost INTEGER,
                goals_for INTEGER,
                goals_against INTEGER,
                goal_difference INTEGER,
                points INTEGER,
                FOREIGN KEY (team_id) REFERENCES teams(id)
            )
        ''')
        
        # Live scores tablosu (canlı skorlar için)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER UNIQUE,
                home_score INTEGER,
                away_score INTEGER,
                match_status TEXT,
                last_updated DATETIME,
                FOREIGN KEY (match_id) REFERENCES matches(match_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print("✅ Veritabanı oluşturuldu!")
    
    def fetch_season_data(self, season=2025):
        """2025-26 sezonu verilerini çek"""
        print(f"\n📥 {season}-{season+1} sezonu verileri çekiliyor...")
        
        url = f"{self.api_base}/getmatchdata/bl1/{season}"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                matches = response.json()
                print(f"✅ {len(matches)} maç verisi alındı")
                return matches
            else:
                print(f"❌ API hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ İstek hatası: {e}")
            return []
    
    def fetch_standings(self, season=2025):
        """Puan durumunu çek"""
        print(f"\n📊 Puan durumu çekiliyor...")
        
        url = f"{self.api_base}/getbltable/bl1/{season}"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                standings = response.json()
                print(f"✅ {len(standings)} takım puan durumu alındı")
                return standings
            else:
                print(f"❌ API hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ İstek hatası: {e}")
            return []
    
    def save_teams(self, matches):
        """Takımları kaydet"""
        print("\n👥 Takımlar kaydediliyor...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        teams = set()
        for match in matches:
            if match.get('team1'):
                teams.add((
                    match['team1'].get('teamName'),
                    match['team1'].get('shortName'),
                    match['team1'].get('teamIconUrl')
                ))
            if match.get('team2'):
                teams.add((
                    match['team2'].get('teamName'),
                    match['team2'].get('shortName'),
                    match['team2'].get('teamIconUrl')
                ))
        
        saved = 0
        for team_name, short_name, icon_url in teams:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO teams (name, short_name, team_icon_url)
                    VALUES (?, ?, ?)
                ''', (team_name, short_name, icon_url))
                if cursor.rowcount > 0:
                    saved += 1
            except Exception as e:
                print(f"Takım kaydetme hatası: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {saved} takım kaydedildi")
    
    def save_matches(self, matches, season='2025_26'):
        """Maçları kaydet"""
        print("\n⚽ Maçlar kaydediliyor...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        saved = 0
        for match in matches:
            try:
                # Takım kontrolü
                if not match.get('team1') or not match.get('team2'):
                    continue
                
                # Takım ID'lerini bul
                home_team = match['team1'].get('teamName')
                away_team = match['team2'].get('teamName')
                
                if not home_team or not away_team:
                    continue
                
                cursor.execute('SELECT id FROM teams WHERE name = ?', (home_team,))
                home_result = cursor.fetchone()
                
                cursor.execute('SELECT id FROM teams WHERE name = ?', (away_team,))
                away_result = cursor.fetchone()
                
                if not home_result or not away_result:
                    continue
                
                home_team_id = home_result[0]
                away_team_id = away_result[0]
                
                # Skor bilgisi
                home_score = None
                away_score = None
                is_finished = match.get('matchIsFinished', False)
                
                if is_finished and match.get('matchResults'):
                    for result in match['matchResults']:
                        if result.get('resultTypeID') == 2:  # Final score
                            home_score = result.get('pointsTeam1')
                            away_score = result.get('pointsTeam2')
                            break
                
                # Tarih
                match_datetime_str = match.get('matchDateTime')
                if match_datetime_str:
                    try:
                        match_datetime = datetime.fromisoformat(match_datetime_str.replace('Z', '+00:00'))
                    except:
                        match_datetime = datetime.now()
                else:
                    match_datetime = datetime.now()
                
                # Lokasyon bilgisi
                location = match.get('location')
                location_city = location.get('locationCity') if location else None
                location_stadium = location.get('locationStadium') if location else None
                
                # Grup bilgisi
                group = match.get('group')
                matchday = group.get('groupOrderID') if group else 1
                
                # Maçı kaydet
                cursor.execute('''
                    INSERT OR REPLACE INTO matches 
                    (match_id, season, matchday, home_team_id, away_team_id, 
                     match_datetime, home_score, away_score, is_finished, 
                     location, stadium)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match.get('matchID'),
                    season,
                    matchday,
                    home_team_id,
                    away_team_id,
                    match_datetime,
                    home_score,
                    away_score,
                    is_finished,
                    location_city,
                    location_stadium
                ))
                
                saved += 1
                
            except Exception as e:
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ {saved} maç kaydedildi")
    
    def save_standings(self, standings, season='2025_26'):
        """Puan durumunu kaydet"""
        print("\n📈 Puan durumu kaydediliyor...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Eski puan durumunu temizle
        cursor.execute('DELETE FROM standings WHERE season = ?', (season,))
        
        saved = 0
        for team in standings:
            try:
                team_name = team.get('teamName')
                
                cursor.execute('SELECT id FROM teams WHERE name = ?', (team_name,))
                team_result = cursor.fetchone()
                
                if not team_result:
                    continue
                
                team_id = team_result[0]
                
                cursor.execute('''
                    INSERT INTO standings 
                    (season, team_id, position, played, won, drawn, lost, 
                     goals_for, goals_against, goal_difference, points)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    season,
                    team_id,
                    team.get('teamInfoId'),
                    team.get('matches'),
                    team.get('won'),
                    team.get('draw'),
                    team.get('lost'),
                    team.get('goals'),
                    team.get('opponentGoals'),
                    team.get('goalDiff'),
                    team.get('points')
                ))
                
                saved += 1
                
            except Exception as e:
                print(f"Puan durumu kaydetme hatası: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ {saved} takım puan durumu kaydedildi")
    
    def get_database_stats(self):
        """Veritabanı istatistikleri"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM teams')
        teams_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM matches')
        matches_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM matches WHERE is_finished = 1')
        finished_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT matchday) FROM matches')
        matchdays_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'teams': teams_count,
            'matches': matches_count,
            'finished': finished_count,
            'matchdays': matchdays_count
        }
    
    def setup_complete_system(self):
        """Tüm sistemi kur - 3 sezon verisiyle"""
        print("="*70)
        print("🇩🇪 BUNDESLIGA TAHMİN SİSTEMİ - KURULUM (3 SEZON)")
        print("="*70)
        
        # 1. Veritabanı oluştur
        self.create_database()
        
        all_teams = set()
        
        # 2. 2022-23, 2023-24, 2025-26 sezonlarını çek
        for season_year, season_name in [(2022, '2022_23'), (2023, '2023_24'), (2025, '2025_26')]:
            print(f"\n{'='*70}")
            print(f"📥 {season_year}-{season_year+1} SEZONU")
            print('='*70)
            
            matches = self.fetch_season_data(season_year)
            
            if not matches:
                print(f"⚠️  {season_name} verisi çekilemedi, devam ediliyor...")
                continue
            
            # Takımları topla
            self.save_teams(matches)
            
            # Maçları kaydet
            self.save_matches(matches, season_name)
            
            # Puan durumunu kaydet (sadece güncel sezon için)
            if season_year == 2025:
                standings = self.fetch_standings(season_year)
                if standings:
                    self.save_standings(standings, season_name)
        
        # 6. İstatistikler
        print("\n" + "="*70)
        print("📊 VERİTABANI İSTATİSTİKLERİ")
        print("="*70)
        
        stats = self.get_database_stats()
        print(f"Takımlar: {stats['teams']}")
        print(f"Toplam Maçlar: {stats['matches']}")
        print(f"Tamamlanan Maçlar: {stats['finished']}")
        print(f"Hafta Sayısı: {stats['matchdays']}")
        
        print("\n" + "="*70)
        print("✅ KURULUM TAMAMLANDI!")
        print("="*70)
        
        return True

if __name__ == '__main__':
    setup = BundesligaSetup()
    setup.setup_complete_system()
