import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import json
import time

class SuperLigDataCollector:
    def __init__(self):
        self.db_path = 'superlig.db'
        self.base_url = 'https://www.soccerway.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                founded_year INTEGER,
                stadium TEXT,
                capacity INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team_id INTEGER,
                away_team_id INTEGER,
                match_date TEXT,
                home_score INTEGER,
                away_score INTEGER,
                home_goals INTEGER,
                away_goals INTEGER,
                home_shots INTEGER,
                away_shots INTEGER,
                home_possession REAL,
                away_possession REAL,
                season TEXT,
                match_day INTEGER,
                FOREIGN KEY (home_team_id) REFERENCES teams (id),
                FOREIGN KEY (away_team_id) REFERENCES teams (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS standings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_id INTEGER,
                season TEXT,
                match_day INTEGER,
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
        
        conn.commit()
        conn.close()
    
    def get_superlig_teams(self):
        teams = [
            "Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor",
            "Sivasspor", "Alanyaspor", "Hatayspor", "Gaziantep FK",
            "Antalyaspor", "Kasımpaşa", "Adana Demirspor", "Konyaspor",
            "İstanbul Başakşehir", "Kayserispor", "Ankaragücü", "MKE Ankaragücü",
            "Çaykur Rizespor", "Giresunspor", "Ümraniyespor", "İstanbulspor"
        ]
        return teams
    
    def get_current_standings(self):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT t.name, s.position, s.played, s.won, s.drawn, s.lost,
                   s.goals_for, s.goals_against, s.goal_difference, s.points
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            WHERE s.season = '2023-2024'
            ORDER BY s.position
        '''
        standings = pd.read_sql_query(query, conn)
        conn.close()
        return standings.to_dict('records')
    
    def get_upcoming_matches(self):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT ht.name as home_team, at.name as away_team, m.match_date
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.match_date > datetime('now')
            ORDER BY m.match_date
            LIMIT 10
        '''
        matches = pd.read_sql_query(query, conn)
        conn.close()
        return matches.to_dict('records')
    
    def get_team_form(self, team_id, last_n=5):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT match_date, home_team_id, away_team_id, home_score, away_score
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND home_score IS NOT NULL
            ORDER BY match_date DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=[team_id, team_id, last_n])
        conn.close()
        
        form = []
        for _, row in df.iterrows():
            if row['home_team_id'] == team_id:
                result = 'W' if row['home_score'] > row['away_score'] else 'D' if row['home_score'] == row['away_score'] else 'L'
                goals_for = row['home_score']
                goals_against = row['away_score']
            else:
                result = 'W' if row['away_score'] > row['home_score'] else 'D' if row['away_score'] == row['home_score'] else 'L'
                goals_for = row['away_score']
                goals_against = row['home_score']
            
            form.append({
                'result': result,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'date': row['match_date']
            })
        
        return form
    
    def get_head_to_head(self, home_team_id, away_team_id, last_n=10):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT match_date, home_team_id, away_team_id, home_score, away_score
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
            AND home_score IS NOT NULL
            ORDER BY match_date DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=[home_team_id, away_team_id, away_team_id, home_team_id, last_n])
        conn.close()
        
        h2h = []
        for _, row in df.iterrows():
            if row['home_team_id'] == home_team_id:
                h2h.append({
                    'home_goals': row['home_score'],
                    'away_goals': row['away_score'],
                    'date': row['match_date'],
                    'venue': 'home'
                })
            else:
                h2h.append({
                    'home_goals': row['away_score'],
                    'away_goals': row['home_score'],
                    'date': row['match_date'],
                    'venue': 'away'
                })
        
        return h2h
    
    def collect_mock_data(self):
        teams = self.get_superlig_teams()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for team in teams:
            cursor.execute('INSERT OR IGNORE INTO teams (name) VALUES (?)', (team,))
        
        conn.commit()
        
        cursor.execute('SELECT id, name FROM teams')
        team_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        import random
        from datetime import datetime, timedelta
        
        for i in range(100):
            home_team = random.choice(list(team_map.keys()))
            away_team = random.choice([t for t in team_map.keys() if t != home_team])
            
            match_date = datetime.now() - timedelta(days=random.randint(1, 365))
            home_score = random.randint(0, 4)
            away_score = random.randint(0, 4)
            
            cursor.execute('''
                INSERT INTO matches 
                (home_team_id, away_team_id, match_date, home_score, away_score, 
                 home_goals, away_goals, season, match_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (team_map[home_team], team_map[away_team], 
                  match_date.strftime('%Y-%m-%d %H:%M'), 
                  home_score, away_score, home_score, away_score, '2023-2024', 
                  random.randint(1, 38)))
        
        conn.commit()
        conn.close()
        print("Mock data collected successfully!")

if __name__ == '__main__':
    collector = SuperLigDataCollector()
    collector.collect_mock_data()
