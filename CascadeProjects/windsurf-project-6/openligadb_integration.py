#!/usr/bin/env python3
"""
OpenLigaDB API Entegrasyonu
Bundesliga ve diğer ligler için canlı maç verileri
"""

import requests
import json
from datetime import datetime
import sqlite3

class OpenLigaDBAPI:
    def __init__(self):
        self.base_url = "https://api.openligadb.de"
        
        # Lig kodları
        self.leagues = {
            'bundesliga': 'bl1',      # Almanya Bundesliga
            'bundesliga2': 'bl2',     # Almanya 2. Bundesliga
            'premier_league': 'pl',   # İngiltere Premier League
            'la_liga': 'es1',         # İspanya La Liga
            'serie_a': 'it1',         # İtalya Serie A
            'ligue1': 'fr1',          # Fransa Ligue 1
        }
    
    def get_current_season_matches(self, league='bl1'):
        """
        Güncel sezonun tüm maçlarını al
        
        Kullanım:
        api = OpenLigaDBAPI()
        matches = api.get_current_season_matches('bl1')
        """
        url = f"{self.base_url}/getmatchdata/{league}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"İstek hatası: {e}")
            return []
    
    def get_matches_by_season(self, league='bl1', season=2024):
        """
        Belirli bir sezonun maçlarını al
        
        Kullanım:
        matches = api.get_matches_by_season('bl1', 2024)
        """
        url = f"{self.base_url}/getmatchdata/{league}/{season}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"İstek hatası: {e}")
            return []
    
    def get_current_matchday(self, league='bl1'):
        """
        Güncel haftanın maçlarını al
        
        Kullanım:
        current_matches = api.get_current_matchday('bl1')
        """
        url = f"{self.base_url}/getmatchdata/{league}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # Sadece güncel haftanın maçları
                if data:
                    current_matchday = data[0].get('group', {}).get('groupOrderID', 1)
                    current_matches = [m for m in data if m.get('group', {}).get('groupOrderID') == current_matchday]
                    return current_matches
                return []
            else:
                return []
        except Exception as e:
            print(f"İstek hatası: {e}")
            return []
    
    def get_team_standings(self, league='bl1', season=2024):
        """
        Puan durumunu al
        
        Kullanım:
        standings = api.get_team_standings('bl1', 2024)
        """
        url = f"{self.base_url}/getbltable/{league}/{season}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"API Hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"İstek hatası: {e}")
            return []
    
    def parse_match_data(self, match):
        """Maç verisini parse et"""
        try:
            return {
                'match_id': match.get('matchID'),
                'match_datetime': match.get('matchDateTime'),
                'home_team': match.get('team1', {}).get('teamName'),
                'away_team': match.get('team2', {}).get('teamName'),
                'home_score': match.get('matchResults', [{}])[0].get('pointsTeam1') if match.get('matchResults') else None,
                'away_score': match.get('matchResults', [{}])[0].get('pointsTeam2') if match.get('matchResults') else None,
                'is_finished': match.get('matchIsFinished', False),
                'matchday': match.get('group', {}).get('groupOrderID'),
                'location': match.get('location', {}).get('locationCity', ''),
                'stadium': match.get('location', {}).get('locationStadium', '')
            }
        except Exception as e:
            print(f"Parse hatası: {e}")
            return None
    
    def save_to_database(self, matches, db_path, league_name='Bundesliga'):
        """
        Maçları veritabanına kaydet
        
        Kullanım:
        api.save_to_database(matches, 'superlig_full.db', 'Bundesliga')
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for match in matches:
            parsed = self.parse_match_data(match)
            if not parsed:
                continue
            
            try:
                # Takım ID'lerini bul veya oluştur
                for team_name in [parsed['home_team'], parsed['away_team']]:
                    cursor.execute('SELECT id FROM teams WHERE name = ?', (team_name,))
                    if not cursor.fetchone():
                        cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)',
                                     (team_name, team_name.upper()))
                
                # Ev sahibi ve deplasman takım ID'leri
                cursor.execute('SELECT id FROM teams WHERE name = ?', (parsed['home_team'],))
                home_team_id = cursor.fetchone()[0]
                
                cursor.execute('SELECT id FROM teams WHERE name = ?', (parsed['away_team'],))
                away_team_id = cursor.fetchone()[0]
                
                # Maç tarihini parse et
                match_datetime = datetime.fromisoformat(parsed['match_datetime'].replace('Z', '+00:00'))
                
                # Maçı kaydet
                cursor.execute('''
                    INSERT OR REPLACE INTO matches 
                    (season, home_team_id, away_team_id, match_date, match_datetime, 
                     home_score, away_score, stadium)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{league_name}_current",
                    home_team_id,
                    away_team_id,
                    match_datetime.strftime('%d.%m.%Y %H:%M'),
                    match_datetime,
                    parsed['home_score'],
                    parsed['away_score'],
                    parsed['stadium']
                ))
                
                saved_count += 1
                
            except Exception as e:
                print(f"Kaydetme hatası: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        print(f"✅ {saved_count} maç kaydedildi")
        return saved_count


def example_usage():
    """Örnek kullanım"""
    
    print("="*70)
    print("🏆 OPENLIGADB API - ÖRNEK KULLANIM")
    print("="*70)
    
    api = OpenLigaDBAPI()
    
    # 1. Bundesliga güncel hafta maçları
    print("\n📊 Bundesliga - Güncel Hafta Maçları:")
    print("-" * 70)
    
    current_matches = api.get_current_matchday('bl1')
    
    if current_matches:
        for match in current_matches[:5]:  # İlk 5 maç
            parsed = api.parse_match_data(match)
            if parsed:
                status = "✅ Bitti" if parsed['is_finished'] else "⏳ Oynanacak"
                score = f"{parsed['home_score']}-{parsed['away_score']}" if parsed['is_finished'] else "vs"
                print(f"{parsed['home_team']} {score} {parsed['away_team']} - {status}")
    
    # 2. Puan durumu
    print("\n📈 Bundesliga - Puan Durumu:")
    print("-" * 70)
    
    standings = api.get_team_standings('bl1', 2024)
    
    if standings:
        for i, team in enumerate(standings[:5], 1):  # İlk 5 takım
            print(f"{i}. {team.get('teamName')} - {team.get('points')} puan")
    
    # 3. Veritabanına kaydet
    print("\n💾 Veritabanına Kaydetme:")
    print("-" * 70)
    
    # api.save_to_database(current_matches, 'superlig_full.db', 'Bundesliga')
    print("Kaydetmek için yukarıdaki satırın yorumunu kaldır")
    
    print("\n" + "="*70)
    print("✅ İşlem Tamamlandı!")
    print("="*70)
    
    # API Endpoint Örnekleri
    print("\n📚 DİĞER KULLANIM ÖRNEKLERİ:")
    print("-" * 70)
    print("1. Tüm sezon maçları:")
    print("   matches = api.get_matches_by_season('bl1', 2024)")
    print()
    print("2. Güncel hafta:")
    print("   current = api.get_current_matchday('bl1')")
    print()
    print("3. Puan durumu:")
    print("   standings = api.get_team_standings('bl1', 2024)")
    print()
    print("4. Farklı ligler:")
    print("   premier = api.get_current_matchday('pl')  # Premier League")
    print("   laliga = api.get_current_matchday('es1')  # La Liga")
    print()
    print("5. API Endpoint'leri:")
    print("   https://api.openligadb.de/getmatchdata/bl1")
    print("   https://api.openligadb.de/getmatchdata/bl1/2024")
    print("   https://api.openligadb.de/getbltable/bl1/2024")
    print()


if __name__ == '__main__':
    example_usage()
