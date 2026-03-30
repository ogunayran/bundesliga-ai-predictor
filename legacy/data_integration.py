import pandas as pd
import sqlite3
import os
from datetime import datetime
import glob

class DataIntegration:
    def __init__(self):
        self.historical_data_path = '/Users/ogunayran/Downloads/TFF_Data'
        self.db_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                normalized_name TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT,
                match_code INTEGER,
                tff_link TEXT,
                home_team_id INTEGER,
                away_team_id INTEGER,
                home_score INTEGER,
                away_score INTEGER,
                stadium TEXT,
                referee TEXT,
                match_date TEXT,
                match_datetime DATETIME,
                FOREIGN KEY (home_team_id) REFERENCES teams (id),
                FOREIGN KEY (away_team_id) REFERENCES teams (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS season_standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                season TEXT,
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
                FOREIGN KEY (team_id) REFERENCES teams (id)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_matches_season ON matches(season)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_datetime)
        ''')
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")
    
    def normalize_team_name(self, name):
        name = name.upper()
        name = name.replace('A.Ş.', '').replace('A.Ş', '').replace('A.S.', '').replace('FK', '')
        name = name.replace('SPOR', '').replace('KULÜBÜ', '').replace('KULÜBÜ', '')
        name = name.strip()
        
        team_mappings = {
            'BEŞIKTAŞ': 'BEŞİKTAŞ',
            'FENERBAHÇE': 'FENERBAHÇE',
            'GALATASARAY': 'GALATASARAY',
            'TRABZONSPOR': 'TRABZONSPOR',
            'BAŞAKŞEHIR': 'BAŞAKŞEHİR',
            'MEDIPOL BAŞAKŞEHIR': 'BAŞAKŞEHİR',
            'İSTANBUL BAŞAKŞEHIR': 'BAŞAKŞEHİR',
            'KONYASPOR': 'KONYASPOR',
            'İTTİFAK HOLDİNG KONYASPOR': 'KONYASPOR',
            'TORKU KONYASPOR': 'KONYASPOR',
            'SIVASSPOR': 'SİVASSPOR',
            'DEMIR GRUP SIVASSPOR': 'SİVASSPOR',
            'ALANYASPOR': 'ALANYASPOR',
            'AYTEMIZ ALANYASPOR': 'ALANYASPOR',
            'ANTALYASPOR': 'ANTALYASPOR',
            'FRAPORT TAV ANTALYASPOR': 'ANTALYASPOR',
            'KASIMPAŞA': 'KASIMPAŞA',
            'HATAYSPOR': 'HATAYSPOR',
            'ATAKAŞ HATAYSPOR': 'HATAYSPOR',
            'KAYSERISPOR': 'KAYSERİSPOR',
            'YUKATEL KAYSERISPOR': 'KAYSERİSPOR',
            'GAZIANTEP': 'GAZİANTEP',
            'GAZIANTEP FUTBOL': 'GAZİANTEP',
            'ADANA DEMIRSPOR': 'ADANA DEMİRSPOR',
            'RIZESPOR': 'RİZESPOR',
            'ÇAYKUR RIZESPOR': 'RİZESPOR',
            'GIRESUNSPOR': 'GİRESUNSPOR',
            'GZT GIRESUNSPOR': 'GİRESUNSPOR',
            'FATIH KARAGÜMRÜK': 'FATİH KARAGÜMRÜK',
            'VAVACARS FATIH KARAGÜMRÜK': 'FATİH KARAGÜMRÜK',
            'MALATYASPOR': 'MALATYASPOR',
            'ÖZNUR KABLO YENI MALATYASPOR': 'MALATYASPOR',
            'YENI MALATYASPOR': 'MALATYASPOR',
            'ANKARAGÜCÜ': 'ANKARAGÜCÜ',
            'MKE ANKARAGÜCÜ': 'ANKARAGÜCÜ',
            'GÖZTEPE': 'GÖZTEPE',
            'ALTAY': 'ALTAY',
            'İSTANBULSPOR': 'İSTANBULSPOR',
            'ÜMRANIYESPOR': 'ÜMRANİYESPOR'
        }
        
        for key, value in team_mappings.items():
            if key in name:
                return value
        
        return name
    
    def get_or_create_team(self, team_name, cursor):
        normalized = self.normalize_team_name(team_name)
        
        cursor.execute('SELECT id FROM teams WHERE normalized_name = ?', (normalized,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            cursor.execute('INSERT INTO teams (name, normalized_name) VALUES (?, ?)', (team_name, normalized))
            return cursor.lastrowid
    
    def parse_date(self, date_str):
        try:
            if ' - ' in date_str:
                date_str = date_str.replace(' - ', ' ')
            
            formats = [
                '%d.%m.%Y %H:%M',
                '%d.%m.%Y - %H:%M',
                '%d/%m/%Y %H:%M',
                '%Y-%m-%d %H:%M',
                '%d.%m.%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue
            
            return None
        except:
            return None
    
    def import_season_data(self, season_folder):
        season_name = os.path.basename(season_folder)
        print(f"Importing season: {season_name}")
        
        matches_file = os.path.join(season_folder, f'{season_name}_sezon_maclari.csv')
        standings_file = os.path.join(season_folder, f'{season_name}.csv')
        
        if not os.path.exists(matches_file):
            print(f"Matches file not found: {matches_file}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            matches_df = pd.read_csv(matches_file, encoding='utf-8-sig')
            
            cursor.execute('DELETE FROM matches WHERE season = ?', (season_name,))
            
            for _, row in matches_df.iterrows():
                home_team_id = self.get_or_create_team(row['Ev_sahibi'], cursor)
                away_team_id = self.get_or_create_team(row['Misafir_takim'], cursor)
                
                match_datetime = self.parse_date(str(row['Tarih_saat'])) if pd.notna(row['Tarih_saat']) else None
                
                cursor.execute('''
                    INSERT INTO matches 
                    (season, match_code, tff_link, home_team_id, away_team_id, 
                     home_score, away_score, stadium, referee, match_date, match_datetime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    season_name,
                    int(row['Mac_kodu']) if pd.notna(row['Mac_kodu']) else None,
                    row['TFF_mac_linki'] if pd.notna(row['TFF_mac_linki']) else '',
                    home_team_id,
                    away_team_id,
                    int(row['Ev_sahibi_gol']) if pd.notna(row['Ev_sahibi_gol']) else None,
                    int(row['Misafir_takim_gol']) if pd.notna(row['Misafir_takim_gol']) else None,
                    row['Stat'] if pd.notna(row['Stat']) else '',
                    row['Ana_hakem'] if pd.notna(row['Ana_hakem']) else '',
                    str(row['Tarih_saat']) if pd.notna(row['Tarih_saat']) else '',
                    match_datetime
                ))
            
            print(f"Imported {len(matches_df)} matches for {season_name}")
            
            if os.path.exists(standings_file):
                standings_df = pd.read_csv(standings_file, encoding='utf-8-sig')
                
                cursor.execute('DELETE FROM season_standings WHERE season = ?', (season_name,))
                
                for idx, row in standings_df.iterrows():
                    team_id = self.get_or_create_team(row['Takim_adi'], cursor)
                    
                    cursor.execute('''
                        INSERT INTO season_standings 
                        (season, team_id, position, played, won, drawn, lost, 
                         goals_for, goals_against, goal_difference, points)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        season_name,
                        team_id,
                        idx + 1,
                        int(row['Oynadigi_mac_sayisi']) if pd.notna(row['Oynadigi_mac_sayisi']) else 0,
                        int(row['Galibiyet_sayisi']) if pd.notna(row['Galibiyet_sayisi']) else 0,
                        int(row['Beraberlik_sayisi']) if pd.notna(row['Beraberlik_sayisi']) else 0,
                        int(row['Maglubiyet_sayisi']) if pd.notna(row['Maglubiyet_sayisi']) else 0,
                        int(row['Attigi_gol_sayisi']) if pd.notna(row['Attigi_gol_sayisi']) else 0,
                        int(row['Yedigi_gol_sayisi']) if pd.notna(row['Yedigi_gol_sayisi']) else 0,
                        int(row['Averaj']) if pd.notna(row['Averaj']) else 0,
                        int(row['Puan']) if pd.notna(row['Puan']) else 0
                    ))
                
                print(f"Imported standings for {season_name}")
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"Error importing {season_name}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def import_all_seasons(self):
        season_folders = sorted(glob.glob(os.path.join(self.historical_data_path, '*_*')))
        
        total_seasons = len(season_folders)
        successful = 0
        
        for folder in season_folders:
            if os.path.isdir(folder):
                if self.import_season_data(folder):
                    successful += 1
        
        print(f"\n{'='*50}")
        print(f"Import completed: {successful}/{total_seasons} seasons imported successfully")
        print(f"{'='*50}")
        
        self.print_database_stats()
    
    def print_database_stats(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM teams')
        team_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM matches')
        match_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT season) FROM matches')
        season_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(match_datetime), MAX(match_datetime) FROM matches WHERE match_datetime IS NOT NULL')
        date_range = cursor.fetchone()
        
        print(f"\nDatabase Statistics:")
        print(f"  Total Teams: {team_count}")
        print(f"  Total Matches: {match_count}")
        print(f"  Total Seasons: {season_count}")
        if date_range[0] and date_range[1]:
            print(f"  Date Range: {date_range[0]} to {date_range[1]}")
        
        cursor.execute('''
            SELECT season, COUNT(*) as match_count 
            FROM matches 
            GROUP BY season 
            ORDER BY season DESC 
            LIMIT 10
        ''')
        
        print(f"\nRecent Seasons:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} matches")
        
        conn.close()

if __name__ == '__main__':
    integrator = DataIntegration()
    integrator.import_all_seasons()
