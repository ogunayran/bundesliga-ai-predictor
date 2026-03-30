#!/usr/bin/env python3
"""
Bundesliga AI Predictor
Gerçek 2024-25 sezonu verileriyle eğitilmiş tahmin modeli
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
from sklearn.calibration import CalibratedClassifierCV
import pickle
from datetime import datetime, timedelta

class BundesligaPredictor:
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/bundesliga.db'):
        self.db_path = db_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.accuracy = 0
    
    def get_team_stats(self, team_id, before_date=None, last_n_matches=10):
        """Takım istatistiklerini al"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.home_score, m.away_score, m.home_team_id, m.away_team_id, m.match_datetime
            FROM matches m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.is_finished = 1
        '''
        
        params = [team_id, team_id]
        
        if before_date:
            query += ' AND m.match_datetime < ?'
            params.append(before_date)
        
        query += ' ORDER BY m.match_datetime DESC LIMIT ?'
        params.append(last_n_matches)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {
                'points': 0, 'win_rate': 0, 'avg_goals_scored': 0,
                'avg_goals_conceded': 0, 'clean_sheets': 0
            }
        
        points = 0
        goals_scored = 0
        goals_conceded = 0
        wins = 0
        clean_sheets = 0
        
        for _, match in df.iterrows():
            if match['home_team_id'] == team_id:
                goals_scored += match['home_score']
                goals_conceded += match['away_score']
                if match['home_score'] > match['away_score']:
                    points += 3
                    wins += 1
                elif match['home_score'] == match['away_score']:
                    points += 1
                if match['away_score'] == 0:
                    clean_sheets += 1
            else:
                goals_scored += match['away_score']
                goals_conceded += match['home_score']
                if match['away_score'] > match['home_score']:
                    points += 3
                    wins += 1
                elif match['away_score'] == match['home_score']:
                    points += 1
                if match['home_score'] == 0:
                    clean_sheets += 1
        
        matches_count = len(df)
        
        return {
            'points': points,
            'win_rate': wins / matches_count if matches_count > 0 else 0,
            'avg_goals_scored': goals_scored / matches_count if matches_count > 0 else 0,
            'avg_goals_conceded': goals_conceded / matches_count if matches_count > 0 else 0,
            'clean_sheets': clean_sheets / matches_count if matches_count > 0 else 0
        }
    
    def get_h2h_stats(self, home_team_id, away_team_id):
        """Kafa kafaya istatistikler"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT home_score, away_score, home_team_id
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) OR
                   (home_team_id = ? AND away_team_id = ?))
            AND is_finished = 1
            ORDER BY match_datetime DESC
            LIMIT 5
        '''
        
        df = pd.read_sql_query(query, conn, params=[home_team_id, away_team_id, away_team_id, home_team_id])
        conn.close()
        
        if df.empty:
            return {'h2h_home_wins': 0, 'h2h_draws': 0, 'h2h_away_wins': 0, 'h2h_avg_goals': 0}
        
        home_wins = 0
        draws = 0
        away_wins = 0
        total_goals = 0
        
        for _, match in df.iterrows():
            if match['home_team_id'] == home_team_id:
                if match['home_score'] > match['away_score']:
                    home_wins += 1
                elif match['home_score'] == match['away_score']:
                    draws += 1
                else:
                    away_wins += 1
            else:
                if match['away_score'] > match['home_score']:
                    home_wins += 1
                elif match['away_score'] == match['home_score']:
                    draws += 1
                else:
                    away_wins += 1
            
            total_goals += match['home_score'] + match['away_score']
        
        return {
            'h2h_home_wins': home_wins,
            'h2h_draws': draws,
            'h2h_away_wins': away_wins,
            'h2h_avg_goals': total_goals / len(df)
        }
    
    def get_home_away_stats(self, team_id, is_home, before_date=None, last_n=5):
        """Ev/deplasman özel istatistikler"""
        conn = sqlite3.connect(self.db_path)
        
        if is_home:
            query = '''
                SELECT home_score, away_score
                FROM matches
                WHERE home_team_id = ? AND is_finished = 1
            '''
        else:
            query = '''
                SELECT away_score, home_score
                FROM matches
                WHERE away_team_id = ? AND is_finished = 1
            '''
        
        if before_date:
            query += ' AND match_datetime < ?'
            params = [team_id, before_date]
        else:
            params = [team_id]
        
        query += ' ORDER BY match_datetime DESC LIMIT ?'
        params.append(last_n)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {'points': 0, 'win_rate': 0, 'avg_goals_scored': 0}
        
        points = 0
        wins = 0
        goals_scored = 0
        
        for _, match in df.iterrows():
            scored = match.iloc[0]
            conceded = match.iloc[1]
            goals_scored += scored
            
            if scored > conceded:
                points += 3
                wins += 1
            elif scored == conceded:
                points += 1
        
        return {
            'points': points,
            'win_rate': wins / len(df),
            'avg_goals_scored': goals_scored / len(df)
        }
    
    def extract_features(self, home_team_id, away_team_id, before_date=None):
        """Özellik çıkarımı - ev sahibi avantajı ile"""
        home_stats_5 = self.get_team_stats(home_team_id, before_date, 5)
        home_stats_10 = self.get_team_stats(home_team_id, before_date, 10)
        away_stats_5 = self.get_team_stats(away_team_id, before_date, 5)
        away_stats_10 = self.get_team_stats(away_team_id, before_date, 10)
        
        # Ev/deplasman özel istatistikler
        home_at_home = self.get_home_away_stats(home_team_id, True, before_date, 5)
        away_at_away = self.get_home_away_stats(away_team_id, False, before_date, 5)
        
        h2h_stats = self.get_h2h_stats(home_team_id, away_team_id)
        
        features = {
            # SADECE ev/deplasman özel istatistikler - genel formu kullanma
            'home_at_home_points': home_at_home['points'],
            'home_at_home_win_rate': home_at_home['win_rate'],
            'home_at_home_goals': home_at_home['avg_goals_scored'],
            
            'away_at_away_points': away_at_away['points'],
            'away_at_away_win_rate': away_at_away['win_rate'],
            'away_at_away_goals': away_at_away['avg_goals_scored'],
            
            'home_avg_goals_scored_5': home_stats_5['avg_goals_scored'],
            'home_avg_goals_scored_10': home_stats_10['avg_goals_scored'],
            'away_avg_goals_scored_5': away_stats_5['avg_goals_scored'],
            'away_avg_goals_scored_10': away_stats_10['avg_goals_scored'],
            
            'home_avg_goals_conceded_5': home_stats_5['avg_goals_conceded'],
            'home_avg_goals_conceded_10': home_stats_10['avg_goals_conceded'],
            'away_avg_goals_conceded_5': away_stats_5['avg_goals_conceded'],
            'away_avg_goals_conceded_10': away_stats_10['avg_goals_conceded'],
            
            'home_clean_sheets_5': home_stats_5['clean_sheets'],
            'away_clean_sheets_5': away_stats_5['clean_sheets'],
            
            'goal_diff_5': (home_stats_5['avg_goals_scored'] - home_stats_5['avg_goals_conceded']) - 
                          (away_stats_5['avg_goals_scored'] - away_stats_5['avg_goals_conceded']),
            'goal_diff_10': (home_stats_10['avg_goals_scored'] - home_stats_10['avg_goals_conceded']) - 
                           (away_stats_10['avg_goals_scored'] - away_stats_10['avg_goals_conceded']),
            
            'h2h_home_wins': h2h_stats['h2h_home_wins'],
            'h2h_draws': h2h_stats['h2h_draws'],
            'h2h_away_wins': h2h_stats['h2h_away_wins'],
            'h2h_avg_goals': h2h_stats['h2h_avg_goals'],
            
            # Ev sahibi avantajı faktörü
            'home_advantage': 1.0  # Sabit özellik - ev sahibi olduğunu gösterir
        }
        
        return features
    
    def prepare_training_data(self):
        """Eğitim verisini hazırla"""
        print("Eğitim verisi hazırlanıyor...")
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.id, m.home_team_id, m.away_team_id, m.home_score, m.away_score, m.match_datetime
            FROM matches m
            WHERE m.is_finished = 1
            ORDER BY m.match_datetime
        '''
        
        matches = pd.read_sql_query(query, conn)
        conn.close()
        
        X = []
        y = []
        
        print(f"Toplam {len(matches)} maç işleniyor...")
        
        for idx, match in matches.iterrows():
            if idx % 50 == 0:
                print(f"İşlenen: {idx}/{len(matches)}")
            
            features = self.extract_features(
                match['home_team_id'],
                match['away_team_id'],
                match['match_datetime']
            )
            
            # Sonuç
            if match['home_score'] > match['away_score']:
                result = 2  # Home Win
            elif match['home_score'] < match['away_score']:
                result = 0  # Away Win
            else:
                result = 1  # Draw
            
            X.append(list(features.values()))
            y.append(result)
        
        self.feature_names = list(features.keys())
        
        return np.array(X), np.array(y)
    
    def train_model(self, test_size=0.2):
        """Modeli eğit"""
        print("\n🤖 Model eğitimi başlıyor...")
        
        X, y = self.prepare_training_data()
        
        if len(X) < 50:
            print("❌ Yetersiz veri!")
            return False
        
        # NaN temizle
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]
        
        print(f"Temiz veri: {len(X)} örnek")
        
        # Stratified split - her sınıftan dengeli örnek
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Random Forest - basit ve dengeli
        from sklearn.ensemble import RandomForestClassifier
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=5,
            min_samples_split=20,
            min_samples_leaf=10,
            max_features='sqrt',
            random_state=42
        )
        
        print("Eğitim yapılıyor (basit Random Forest)...")
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        self.accuracy = accuracy_score(y_test, y_pred)
        
        print("\n" + "="*70)
        print("✅ MODEL EĞİTİMİ TAMAMLANDI!")
        print("="*70)
        print(f"Doğruluk: {self.accuracy:.1%}")
        print("\nSınıflandırma Raporu:")
        print(classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
        
        return True
    
    def save_model(self, path='bundesliga_model.pkl'):
        """Modeli kaydet"""
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'accuracy': self.accuracy
            }, f)
        print(f"\n✅ Model kaydedildi: {path}")
    
    def load_model(self, path='bundesliga_model.pkl'):
        """Modeli yükle"""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.feature_names = data['feature_names']
            self.accuracy = data['accuracy']
        print(f"✅ Model yüklendi (Doğruluk: {self.accuracy:.1%})")
    
    def predict_score(self, home_team_id, away_team_id):
        """Skor tahmini - H2H ve sezon istatistiklerine göre"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. H2H maçlar - son 5 karşılaşma
        cursor.execute('''
            SELECT home_score, away_score
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) OR 
                   (home_team_id = ? AND away_team_id = ?))
            AND is_finished = 1
            ORDER BY match_datetime DESC
            LIMIT 5
        ''', (home_team_id, away_team_id, away_team_id, home_team_id))
        
        h2h_matches = cursor.fetchall()
        
        # 2. Ev sahibi - evdeki gol ortalaması (bu sezon)
        cursor.execute('''
            SELECT AVG(home_score) as avg_scored, AVG(away_score) as avg_conceded
            FROM matches
            WHERE home_team_id = ? AND is_finished = 1
            AND season = '2025_26'
        ''', (home_team_id,))
        
        home_stats = cursor.fetchone()
        home_avg_scored = home_stats[0] if home_stats[0] else 1.5
        home_avg_conceded = home_stats[1] if home_stats[1] else 1.0
        
        # 3. Deplasman - deplasmanki gol ortalaması (bu sezon)
        cursor.execute('''
            SELECT AVG(away_score) as avg_scored, AVG(home_score) as avg_conceded
            FROM matches
            WHERE away_team_id = ? AND is_finished = 1
            AND season = '2025_26'
        ''', (away_team_id,))
        
        away_stats = cursor.fetchone()
        away_avg_scored = away_stats[0] if away_stats[0] else 1.0
        away_avg_conceded = away_stats[1] if away_stats[1] else 1.5
        
        conn.close()
        
        # 4. H2H ortalaması
        h2h_home_goals = 0
        h2h_away_goals = 0
        
        if h2h_matches:
            for match in h2h_matches:
                # Ev sahibi perspektifinden
                if match[0] is not None and match[1] is not None:
                    h2h_home_goals += match[0]
                    h2h_away_goals += match[1]
            
            h2h_home_avg = h2h_home_goals / len(h2h_matches)
            h2h_away_avg = h2h_away_goals / len(h2h_matches)
        else:
            h2h_home_avg = 1.5
            h2h_away_avg = 1.0
        
        # 5. Tahmin - %60 sezon ortalaması, %40 H2H
        predicted_home_goals = (home_avg_scored * 0.6) + (h2h_home_avg * 0.4)
        predicted_away_goals = (away_avg_scored * 0.6) + (h2h_away_avg * 0.4)
        
        # Yuvarla
        home_goals = round(predicted_home_goals)
        away_goals = round(predicted_away_goals)
        
        return {
            'predicted_score': f'{home_goals}-{away_goals}',
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_expected': round(predicted_home_goals, 1),
            'away_expected': round(predicted_away_goals, 1),
            'h2h_matches': len(h2h_matches),
            'based_on': {
                'home_season_avg': round(home_avg_scored, 1),
                'away_season_avg': round(away_avg_scored, 1),
                'h2h_home_avg': round(h2h_home_avg, 1) if h2h_matches else None,
                'h2h_away_avg': round(h2h_away_avg, 1) if h2h_matches else None
            }
        }
    
    def predict_match(self, home_team_id, away_team_id):
        """Tek maç tahmini - sonuç + skor"""
        if self.model is None:
            raise Exception("Model henüz eğitilmemiş!")
        
        features = self.extract_features(home_team_id, away_team_id)
        X = pd.DataFrame([features])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        result_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        # Skor tahmini ekle
        score_prediction = self.predict_score(home_team_id, away_team_id)
        
        return {
            'prediction': result_map[prediction],
            'probabilities': {
                'Home Win': probabilities[2],
                'Draw': probabilities[1],
                'Away Win': probabilities[0]
            },
            'confidence': max(probabilities),
            'score_prediction': score_prediction
        }
    
    def get_next_week_matches(self):
        """Gelecek haftanın maçlarını al"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.match_id, m.home_team_id, m.away_team_id, m.match_datetime, m.matchday,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.is_finished = 0
            AND m.match_datetime > datetime('now')
            ORDER BY m.match_datetime
            LIMIT 9
        '''
        
        matches = pd.read_sql_query(query, conn)
        conn.close()
        
        return matches
    
    def predict_next_week(self):
        """Gelecek hafta tahminleri"""
        matches = self.get_next_week_matches()
        
        predictions = []
        
        for _, match in matches.iterrows():
            pred = self.predict_match(match['home_team_id'], match['away_team_id'])
            
            if pred:
                predictions.append({
                    'match_id': int(match['match_id']),
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_datetime': str(match['match_datetime']),
                    'matchday': int(match['matchday']),
                    **pred
                })
        
        return predictions

if __name__ == '__main__':
    print("="*70)
    print("🇩🇪 BUNDESLIGA AI MODEL - EĞİTİM")
    print("="*70)
    
    predictor = BundesligaPredictor()
    
    if predictor.train_model():
        predictor.save_model('/Users/ogunayran/CascadeProjects/windsurf-project-6/bundesliga_model.pkl')
        
        print("\n" + "="*70)
        print("📊 GELECEK HAFTA TAHMİNLERİ")
        print("="*70)
        
        predictions = predictor.predict_next_week()
        
        for pred in predictions:
            print(f"\n{pred['home_team']} vs {pred['away_team']}")
            print(f"  Tahmin: {pred['prediction']} ({pred['confidence']:.1%} güven)")
            print(f"  Olasılıklar: H:{pred['probabilities']['Home Win']:.1%} D:{pred['probabilities']['Draw']:.1%} A:{pred['probabilities']['Away Win']:.1%}")
