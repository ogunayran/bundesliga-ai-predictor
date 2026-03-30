#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundesliga Gelişmiş Tahmin Modelleri
- Neural Network
- Poisson Regression
- Ensemble Model
"""

import sqlite3
import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.metrics import accuracy_score, classification_report
from scipy.stats import poisson as poisson_dist

class PoissonScorePredictor:
    """
    Poisson Regression - Skor tahmini için özel model
    """
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
        self.home_lambda = {}  # Takım başına beklenen ev sahibi gol
        self.away_lambda = {}  # Takım başına beklenen deplasman gol
    
    def train(self):
        """
        Poisson parametrelerini hesapla
        """
        conn = sqlite3.connect(self.db_path)
        
        # Her takım için ev sahibi gol ortalaması
        query = '''
            SELECT t.id, t.name, AVG(m.home_score) as avg_goals
            FROM matches m
            JOIN teams t ON m.home_team_id = t.id
            WHERE m.is_finished = 1 AND m.season = '2025_26'
            GROUP BY t.id, t.name
        '''
        home_df = pd.read_sql_query(query, conn)
        
        for _, row in home_df.iterrows():
            self.home_lambda[row['id']] = row['avg_goals'] if row['avg_goals'] else 1.5
        
        # Her takım için deplasman gol ortalaması
        query = '''
            SELECT t.id, t.name, AVG(m.away_score) as avg_goals
            FROM matches m
            JOIN teams t ON m.away_team_id = t.id
            WHERE m.is_finished = 1 AND m.season = '2025_26'
            GROUP BY t.id, t.name
        '''
        away_df = pd.read_sql_query(query, conn)
        
        for _, row in away_df.iterrows():
            self.away_lambda[row['id']] = row['avg_goals'] if row['avg_goals'] else 1.0
        
        conn.close()
        
        print(f"✅ Poisson model eğitildi: {len(self.home_lambda)} takım")
    
    def predict_score_probabilities(self, home_team_id, away_team_id, max_goals=6):
        """
        Skor olasılıklarını hesapla
        """
        home_lambda = self.home_lambda.get(home_team_id, 1.5)
        away_lambda = self.away_lambda.get(away_team_id, 1.0)
        
        # Tüm olası skorlar için olasılık hesapla
        score_probs = {}
        
        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob_home = poisson_dist.pmf(home_goals, home_lambda)
                prob_away = poisson_dist.pmf(away_goals, away_lambda)
                prob = prob_home * prob_away
                
                score_probs[f'{home_goals}-{away_goals}'] = prob
        
        # En olası skor
        most_likely_score = max(score_probs, key=score_probs.get)
        
        # Sonuç olasılıkları
        home_win_prob = sum([p for score, p in score_probs.items() if int(score.split('-')[0]) > int(score.split('-')[1])])
        draw_prob = sum([p for score, p in score_probs.items() if int(score.split('-')[0]) == int(score.split('-')[1])])
        away_win_prob = sum([p for score, p in score_probs.items() if int(score.split('-')[0]) < int(score.split('-')[1])])
        
        return {
            'most_likely_score': most_likely_score,
            'score_probabilities': dict(sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:10]),
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'home_expected_goals': home_lambda,
            'away_expected_goals': away_lambda
        }

class NeuralNetworkPredictor:
    """
    Neural Network - Daha karmaşık paternler için
    """
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
    
    def prepare_features(self, home_team_id, away_team_id, before_date=None):
        """
        Gelişmiş özellik çıkarımı
        """
        conn = sqlite3.connect(self.db_path)
        
        features = {}
        
        # Ev sahibi istatistikleri (son 10 maç)
        query = '''
            SELECT 
                AVG(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as win_rate,
                AVG(home_score) as avg_goals_scored,
                AVG(away_score) as avg_goals_conceded,
                COUNT(*) as matches
            FROM matches
            WHERE home_team_id = ? AND is_finished = 1
            ORDER BY match_datetime DESC
            LIMIT 10
        '''
        home_stats = pd.read_sql_query(query, conn, params=[home_team_id]).iloc[0]
        
        features['home_win_rate'] = home_stats['win_rate']
        features['home_avg_goals'] = home_stats['avg_goals_scored']
        features['home_avg_conceded'] = home_stats['avg_goals_conceded']
        
        # Deplasman istatistikleri
        query = '''
            SELECT 
                AVG(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as win_rate,
                AVG(away_score) as avg_goals_scored,
                AVG(home_score) as avg_goals_conceded,
                COUNT(*) as matches
            FROM matches
            WHERE away_team_id = ? AND is_finished = 1
            ORDER BY match_datetime DESC
            LIMIT 10
        '''
        away_stats = pd.read_sql_query(query, conn, params=[away_team_id]).iloc[0]
        
        features['away_win_rate'] = away_stats['win_rate']
        features['away_avg_goals'] = away_stats['avg_goals_scored']
        features['away_avg_conceded'] = away_stats['avg_goals_conceded']
        
        # Gol farkı
        features['goal_diff'] = (home_stats['avg_goals_scored'] - home_stats['avg_goals_conceded']) - \
                                (away_stats['avg_goals_scored'] - away_stats['avg_goals_conceded'])
        
        # Form (son 5 maç)
        query = '''
            SELECT 
                SUM(CASE 
                    WHEN (home_team_id = ? AND home_score > away_score) OR 
                         (away_team_id = ? AND away_score > home_score) THEN 3
                    WHEN home_score = away_score THEN 1
                    ELSE 0
                END) as points
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND is_finished = 1
            ORDER BY match_datetime DESC
            LIMIT 5
        '''
        home_form = pd.read_sql_query(query, conn, params=[home_team_id, home_team_id, home_team_id, home_team_id]).iloc[0]['points']
        away_form = pd.read_sql_query(query, conn, params=[away_team_id, away_team_id, away_team_id, away_team_id]).iloc[0]['points']
        
        features['home_form'] = home_form if home_form else 0
        features['away_form'] = away_form if away_form else 0
        
        conn.close()
        
        return features
    
    def train(self, test_size=0.2):
        """
        Neural Network eğitimi
        """
        conn = sqlite3.connect(self.db_path)
        
        # Tamamlanmış maçları al
        matches = pd.read_sql_query('''
            SELECT match_id, home_team_id, away_team_id, home_score, away_score, match_datetime
            FROM matches
            WHERE is_finished = 1
            ORDER BY match_datetime
        ''', conn)
        
        conn.close()
        
        X_list = []
        y_list = []
        
        print(f"Toplam {len(matches)} maç işleniyor...")
        
        for idx, match in matches.iterrows():
            if idx % 100 == 0:
                print(f"İşlenen: {idx}/{len(matches)}")
            
            try:
                features = self.prepare_features(
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
                
                X_list.append(features)
                y_list.append(result)
                
            except Exception as e:
                continue
        
        X = pd.DataFrame(X_list)
        y = np.array(y_list)
        
        self.feature_names = X.columns.tolist()
        
        print(f"Temiz veri: {len(X)} örnek")
        
        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Neural Network
        self.model = MLPClassifier(
            hidden_layer_sizes=(20, 15, 10),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size=32,
            learning_rate='adaptive',
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        
        print("Neural Network eğitiliyor...")
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Neural Network Doğruluğu: {accuracy:.1%}")
        print("\nSınıflandırma Raporu:")
        print(classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
        
        return accuracy

class EnsemblePredictor:
    """
    Ensemble Model - Birden fazla modelin kombinasyonu
    """
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
        self.ensemble = None
        self.scaler = StandardScaler()
        self.feature_names = None
        self.poisson = PoissonScorePredictor(db_path)
    
    def prepare_features(self, home_team_id, away_team_id):
        """
        Özellik hazırlama (Neural Network ile aynı)
        """
        nn = NeuralNetworkPredictor(self.db_path)
        return nn.prepare_features(home_team_id, away_team_id)
    
    def train(self, test_size=0.2):
        """
        Ensemble model eğitimi
        """
        # Poisson'u eğit
        self.poisson.train()
        
        conn = sqlite3.connect(self.db_path)
        
        matches = pd.read_sql_query('''
            SELECT match_id, home_team_id, away_team_id, home_score, away_score, match_datetime
            FROM matches
            WHERE is_finished = 1
            ORDER BY match_datetime
        ''', conn)
        
        conn.close()
        
        X_list = []
        y_list = []
        
        print(f"Ensemble için {len(matches)} maç işleniyor...")
        
        for idx, match in matches.iterrows():
            if idx % 100 == 0:
                print(f"İşlenen: {idx}/{len(matches)}")
            
            try:
                features = self.prepare_features(
                    match['home_team_id'],
                    match['away_team_id']
                )
                
                if match['home_score'] > match['away_score']:
                    result = 2
                elif match['home_score'] < match['away_score']:
                    result = 0
                else:
                    result = 1
                
                X_list.append(features)
                y_list.append(result)
                
            except:
                continue
        
        X = pd.DataFrame(X_list)
        y = np.array(y_list)
        
        self.feature_names = X.columns.tolist()
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Ensemble: Random Forest + Gradient Boosting + Neural Network
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=10,
            random_state=42
        )
        
        gb = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        nn = MLPClassifier(
            hidden_layer_sizes=(15, 10),
            max_iter=300,
            random_state=42,
            early_stopping=True
        )
        
        # Voting Classifier (soft voting)
        self.ensemble = VotingClassifier(
            estimators=[('rf', rf), ('gb', gb), ('nn', nn)],
            voting='soft'
        )
        
        print("Ensemble model eğitiliyor (RF + GB + NN)...")
        self.ensemble.fit(X_train_scaled, y_train)
        
        y_pred = self.ensemble.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n✅ Ensemble Doğruluğu: {accuracy:.1%}")
        print("\nSınıflandırma Raporu:")
        print(classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
        
        return accuracy
    
    def predict(self, home_team_id, away_team_id):
        """
        Ensemble tahmin + Poisson skor tahmini
        """
        # Sonuç tahmini (Ensemble)
        features = self.prepare_features(home_team_id, away_team_id)
        X = pd.DataFrame([features])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.ensemble.predict(X_scaled)[0]
        probabilities = self.ensemble.predict_proba(X_scaled)[0]
        
        result_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        # Skor tahmini (Poisson)
        poisson_pred = self.poisson.predict_score_probabilities(home_team_id, away_team_id)
        
        return {
            'prediction': result_map[prediction],
            'probabilities': {
                'Home Win': probabilities[2],
                'Draw': probabilities[1],
                'Away Win': probabilities[0]
            },
            'confidence': max(probabilities),
            'poisson_score': poisson_pred['most_likely_score'],
            'poisson_probabilities': poisson_pred
        }

if __name__ == '__main__':
    print("="*70)
    print("🧠 BUNDESLIGA GELİŞMİŞ TAHMİN MODELLERİ")
    print("="*70)
    
    # 1. Poisson Regression
    print("\n1️⃣ POISSON REGRESSION - SKOR TAHMİNİ")
    print("="*70)
    poisson = PoissonScorePredictor()
    poisson.train()
    
    # Bayern vs Union Berlin
    conn = sqlite3.connect('bundesliga.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE name LIKE '%Bayern%'")
    bayern_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM teams WHERE name LIKE '%Union%'")
    union_id = cursor.fetchone()[0]
    conn.close()
    
    pred = poisson.predict_score_probabilities(bayern_id, union_id)
    print(f"\nBayern vs Union Berlin:")
    print(f"  En olası skor: {pred['most_likely_score']}")
    print(f"  Ev sahibi kazanır: {pred['home_win_prob']:.1%}")
    print(f"  Beraberlik: {pred['draw_prob']:.1%}")
    print(f"  Deplasman kazanır: {pred['away_win_prob']:.1%}")
    
    # 2. Neural Network
    print("\n\n2️⃣ NEURAL NETWORK")
    print("="*70)
    nn = NeuralNetworkPredictor()
    nn.train()
    
    # 3. Ensemble Model
    print("\n\n3️⃣ ENSEMBLE MODEL (RF + GB + NN)")
    print("="*70)
    ensemble = EnsemblePredictor()
    ensemble.train()
    
    print("\n\n✅ Tüm gelişmiş modeller eğitildi!")
