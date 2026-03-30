import sqlite3
from datetime import datetime

def add_week_26_matches():
    """26. Hafta gerçek maçlarını ekle"""
    
    db_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Mevcut hafta maçlarını temizle
    cursor.execute("DELETE FROM matches WHERE season = 'current_week'")
    
    # 26. Hafta Maçları (Gerçek veriler)
    matches = [
        # 13 Mart 2026
        ('Antalyaspor', 'Gaziantep', '13.03.2026 20:00'),
        ('Karagümrük', 'Fenerbahçe', '13.03.2026 20:00'),
        
        # 14 Mart 2026
        ('Kocaelispor', 'Konyaspor', '14.03.2026 13:30'),
        ('Trabzonspor', 'Rizespor', '14.03.2026 16:00'),
        ('Galatasaray', 'Başakşehir', '14.03.2026 20:00'),
        ('Göztepe', 'Alanyaspor', '14.03.2026 20:00'),
        
        # 15 Mart 2026
        ('Kasımpaşa', 'Eyüpspor', '15.03.2026 16:00'),
        ('Gençlerbirliği', 'Beşiktaş', '15.03.2026 20:00'),
        ('Samsunspor', 'Kayserispor', '15.03.2026 20:00'),
    ]
    
    saved_count = 0
    
    for home_team, away_team, date_time_str in matches:
        # Takım ID'lerini bul veya oluştur
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
        
        # Tarih parse
        match_datetime = datetime.strptime(date_time_str, '%d.%m.%Y %H:%M')
        
        # Maçı kaydet
        cursor.execute('''
            INSERT INTO matches 
            (season, home_team_id, away_team_id, match_date, match_datetime, 
             home_score, away_score)
            VALUES (?, ?, ?, ?, ?, NULL, NULL)
        ''', (
            'current_week',
            home_team_id,
            away_team_id,
            date_time_str,
            match_datetime
        ))
        
        saved_count += 1
        print(f"✅ {home_team} vs {away_team} - {date_time_str}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Toplam {saved_count} maç eklendi!")
    return saved_count

def update_league_standings():
    """Güncel puan durumunu güncelle"""
    
    db_path = '/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Standings tablosunu oluştur (yoksa)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            season TEXT NOT NULL,
            team_id INTEGER NOT NULL,
            played INTEGER DEFAULT 0,
            won INTEGER DEFAULT 0,
            drawn INTEGER DEFAULT 0,
            lost INTEGER DEFAULT 0,
            goals_for INTEGER DEFAULT 0,
            goals_against INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            FOREIGN KEY (team_id) REFERENCES teams(id)
        )
    ''')
    
    # 2025-26 sezonu için standings tablosunu temizle
    cursor.execute("DELETE FROM standings WHERE season = '2025_26'")
    
    # Güncel puan durumu
    standings = [
        ('Galatasaray', 25, 19, 4, 2, 59, 18, 61),
        ('Fenerbahçe', 25, 15, 9, 1, 55, 25, 54),
        ('Trabzonspor', 24, 15, 6, 3, 48, 28, 51),
        ('Beşiktaş', 25, 13, 7, 5, 45, 30, 46),
        ('Başakşehir', 25, 12, 6, 7, 44, 27, 42),
        ('Göztepe', 25, 11, 9, 5, 28, 18, 42),
        ('Samsunspor', 25, 8, 11, 6, 27, 28, 35),
        ('Rizespor', 25, 7, 9, 9, 32, 35, 30),
        ('Kocaelispor', 24, 8, 6, 10, 21, 25, 30),
        ('Gaziantep', 25, 7, 9, 9, 31, 41, 30),
        ('Alanyaspor', 24, 5, 11, 8, 26, 30, 26),
        ('Gençlerbirliği', 24, 6, 6, 12, 28, 34, 24),
        ('Konyaspor', 25, 5, 9, 11, 28, 38, 24),
        ('Antalyaspor', 25, 6, 6, 13, 24, 39, 24),
        ('Eyüpspor', 24, 5, 7, 12, 19, 35, 22),
        ('Kasımpaşa', 25, 4, 9, 12, 21, 36, 21),
        ('Kayserispor', 24, 3, 11, 10, 18, 43, 20),
        ('Karagümrük', 25, 3, 5, 17, 22, 46, 14),
    ]
    
    for team_name, played, won, drawn, lost, goals_for, goals_against, points in standings:
        # Takım ID'sini bul
        cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                      (f'%{team_name}%', f'%{team_name.upper()}%'))
        team_result = cursor.fetchone()
        
        if team_result:
            team_id = team_result[0]
            
            cursor.execute('''
                INSERT INTO standings 
                (season, team_id, played, won, drawn, lost, goals_for, goals_against, points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                '2025_26',
                team_id,
                played,
                won,
                drawn,
                lost,
                goals_for,
                goals_against,
                points
            ))
            
            print(f"✅ {team_name}: {points} puan")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Puan durumu güncellendi!")

if __name__ == '__main__':
    print("="*70)
    print("🏆 26. HAFTA MAÇLARI VE PUAN DURUMU EKLEME")
    print("="*70)
    print()
    
    print("📊 26. Hafta Maçları Ekleniyor...")
    print("-" * 70)
    add_week_26_matches()
    
    print("\n" + "="*70)
    print("📊 Puan Durumu Güncelleniyor...")
    print("-" * 70)
    update_league_standings()
    
    print("\n" + "="*70)
    print("✅ TÜM İŞLEMLER TAMAMLANDI!")
    print("="*70)
