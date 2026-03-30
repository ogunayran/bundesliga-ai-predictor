import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import sqlite3
from datetime import datetime, timedelta
import pickle
import warnings
warnings.filterwarnings('ignore')

class AdvancedSuperLigPredictor:
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'):
        self.db_path = db_path
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.model_accuracy = 0.0
    
    def get_team_stats(self, team_id, before_date=None, last_n_matches=10):
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT home_team_id, away_team_id, home_score, away_score, match_datetime
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND home_score IS NOT NULL
        '''
        
        params = [team_id, team_id]
        
        if before_date:
            query += ' AND match_datetime < ?'
            params.append(before_date)
        
        query += ' ORDER BY match_datetime DESC LIMIT ?'
        params.append(last_n_matches)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        if df.empty:
            return {
                'matches_played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_scored': 0,
                'goals_conceded': 0,
                'points': 0,
                'avg_goals_scored': 0,
                'avg_goals_conceded': 0,
                'win_rate': 0,
                'clean_sheets': 0,
                'btts_rate': 0
            }
        
        stats = {
            'matches_played': len(df),
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'points': 0,
            'clean_sheets': 0,
            'btts_count': 0
        }
        
        for _, match in df.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if is_home:
                goals_for = match['home_score']
                goals_against = match['away_score']
            else:
                goals_for = match['away_score']
                goals_against = match['home_score']
            
            stats['goals_scored'] += goals_for
            stats['goals_conceded'] += goals_against
            
            if goals_for > goals_against:
                stats['wins'] += 1
                stats['points'] += 3
            elif goals_for == goals_against:
                stats['draws'] += 1
                stats['points'] += 1
            else:
                stats['losses'] += 1
            
            if goals_against == 0:
                stats['clean_sheets'] += 1
            
            if goals_for > 0 and goals_against > 0:
                stats['btts_count'] += 1
        
        stats['avg_goals_scored'] = stats['goals_scored'] / max(stats['matches_played'], 1)
        stats['avg_goals_conceded'] = stats['goals_conceded'] / max(stats['matches_played'], 1)
        stats['win_rate'] = stats['wins'] / max(stats['matches_played'], 1)
        stats['btts_rate'] = stats['btts_count'] / max(stats['matches_played'], 1)
        
        return stats
    
    def get_head_to_head_stats(self, home_team_id, away_team_id, last_n=10):
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT home_team_id, away_team_id, home_score, away_score
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
            AND home_score IS NOT NULL
            ORDER BY match_datetime DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[home_team_id, away_team_id, away_team_id, home_team_id, last_n])
        conn.close()
        
        if df.empty:
            return {
                'h2h_home_wins': 0,
                'h2h_draws': 0,
                'h2h_away_wins': 0,
                'h2h_avg_goals': 0,
                'h2h_btts_rate': 0
            }
        
        home_wins = 0
        draws = 0
        away_wins = 0
        total_goals = 0
        btts_count = 0
        
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
            
            if match['home_score'] > 0 and match['away_score'] > 0:
                btts_count += 1
        
        return {
            'h2h_home_wins': home_wins,
            'h2h_draws': draws,
            'h2h_away_wins': away_wins,
            'h2h_avg_goals': total_goals / max(len(df), 1),
            'h2h_btts_rate': btts_count / max(len(df), 1)
        }
    
    def extract_features(self, home_team_id, away_team_id, before_date=None):
        home_stats_5 = self.get_team_stats(home_team_id, before_date, 5)
        home_stats_10 = self.get_team_stats(home_team_id, before_date, 10)
        away_stats_5 = self.get_team_stats(away_team_id, before_date, 5)
        away_stats_10 = self.get_team_stats(away_team_id, before_date, 10)
        h2h_stats = self.get_head_to_head_stats(home_team_id, away_team_id)
        
        features = {
            'home_points_5': home_stats_5['points'],
            'home_points_10': home_stats_10['points'],
            'away_points_5': away_stats_5['points'],
            'away_points_10': away_stats_10['points'],
            
            'home_win_rate_5': home_stats_5['win_rate'],
            'home_win_rate_10': home_stats_10['win_rate'],
            'away_win_rate_5': away_stats_5['win_rate'],
            'away_win_rate_10': away_stats_10['win_rate'],
            
            'home_avg_goals_scored_5': home_stats_5['avg_goals_scored'],
            'home_avg_goals_scored_10': home_stats_10['avg_goals_scored'],
            'away_avg_goals_scored_5': away_stats_5['avg_goals_scored'],
            'away_avg_goals_scored_10': away_stats_10['avg_goals_scored'],
            
            'home_avg_goals_conceded_5': home_stats_5['avg_goals_conceded'],
            'home_avg_goals_conceded_10': home_stats_10['avg_goals_conceded'],
            'away_avg_goals_conceded_5': away_stats_5['avg_goals_conceded'],
            'away_avg_goals_conceded_10': away_stats_10['avg_goals_conceded'],
            
            'home_btts_rate_5': home_stats_5['btts_rate'],
            'away_btts_rate_5': away_stats_5['btts_rate'],
            
            'h2h_home_wins': h2h_stats['h2h_home_wins'],
            'h2h_draws': h2h_stats['h2h_draws'],
            'h2h_away_wins': h2h_stats['h2h_away_wins'],
            'h2h_avg_goals': h2h_stats['h2h_avg_goals'],
            'h2h_btts_rate': h2h_stats['h2h_btts_rate'],
            
            'goal_diff_5': home_stats_5['goals_scored'] - home_stats_5['goals_conceded'] - (away_stats_5['goals_scored'] - away_stats_5['goals_conceded']),
            'goal_diff_10': home_stats_10['goals_scored'] - home_stats_10['goals_conceded'] - (away_stats_10['goals_scored'] - away_stats_10['goals_conceded'])
        }
        
        return features
    
    def prepare_training_data(self, min_season='1990_91', max_season='2021_22'):
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT id, home_team_id, away_team_id, home_score, away_score, match_datetime, season
            FROM matches
            WHERE home_score IS NOT NULL
            AND match_datetime IS NOT NULL
            AND season >= ?
            AND season <= ?
            ORDER BY match_datetime
        '''
        
        matches_df = pd.read_sql_query(query, conn, params=[min_season, max_season])
        conn.close()
        
        print(f"Preparing training data from {len(matches_df)} matches...")
        
        X_list = []
        y_list = []
        
        for idx, match in matches_df.iterrows():
            if idx % 1000 == 0:
                print(f"Processing match {idx}/{len(matches_df)}...")
            
            features = self.extract_features(
                match['home_team_id'],
                match['away_team_id'],
                match['match_datetime']
            )
            
            X_list.append(list(features.values()))
            
            if match['home_score'] > match['away_score']:
                y_list.append(2)
            elif match['home_score'] < match['away_score']:
                y_list.append(0)
            else:
                y_list.append(1)
        
        self.feature_names = list(features.keys())
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        print(f"Training data prepared: {len(X)} samples with {len(self.feature_names)} features")
        
        return X, y
    
    def train_model(self, test_size=0.2):
        print("Starting model training...")
        
        X, y = self.prepare_training_data()
        
        if len(X) < 100:
            print("Insufficient data for training")
            return False
        
        # Remove rows with NaN values
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]
        
        print(f"After removing NaN: {len(X)} samples")
        
        if len(X) < 100:
            print("Insufficient data after cleaning")
            return False
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        
        print("Training model...")
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        self.model_accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\n{'='*50}")
        print(f"Model Training Complete!")
        print(f"{'='*50}")
        print(f"Accuracy: {self.model_accuracy:.3f}")
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Away Win', 'Draw', 'Home Win']))
        
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print(f"\nTop 10 Most Important Features:")
        print(feature_importance.head(10).to_string(index=False))
        
        return True
    
    def predict_match(self, home_team_id, away_team_id):
        if self.model is None:
            print("Model not trained yet!")
            return None
        
        features = self.extract_features(home_team_id, away_team_id)
        X = np.array([list(features.values())])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probabilities = self.model.predict_proba(X_scaled)[0]
        
        result_map = {0: 'Away Win', 1: 'Draw', 2: 'Home Win'}
        
        return {
            'prediction': result_map[prediction],
            'probabilities': {
                'Home Win': float(probabilities[2]),
                'Draw': float(probabilities[1]),
                'Away Win': float(probabilities[0])
            },
            'confidence': float(max(probabilities)),
            'features': features
        }
    
    def get_upcoming_matches(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        
        # Önce bu haftanın maçlarını kontrol et
        query = '''
            SELECT m.id, m.home_team_id, m.away_team_id, m.match_datetime,
                   ht.name as home_team, at.name as away_team, m.season
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.season = 'current_week'
            AND m.home_score IS NULL
            ORDER BY m.match_datetime
        '''
        
        upcoming = pd.read_sql_query(query, conn)
        
        # Eğer bu hafta maçı yoksa, gelecek maçları göster
        if upcoming.empty:
            query = '''
                SELECT m.id, m.home_team_id, m.away_team_id, m.match_datetime,
                       ht.name as home_team, at.name as away_team, m.season
                FROM matches m
                JOIN teams ht ON m.home_team_id = ht.id
                JOIN teams at ON m.away_team_id = at.id
                WHERE m.match_datetime > datetime('now')
                OR (m.home_score IS NULL AND m.season >= '2024_25')
                ORDER BY m.match_datetime
                LIMIT ?
            '''
            upcoming = pd.read_sql_query(query, conn, params=[limit])
        
        conn.close()
        
        return upcoming
    
    def predict_upcoming_matches(self):
        upcoming = self.get_upcoming_matches()
        
        if upcoming.empty:
            print("No upcoming matches found")
            return []
        
        predictions = []
        
        for _, match in upcoming.iterrows():
            pred = self.predict_match(match['home_team_id'], match['away_team_id'])
            
            if pred:
                predictions.append({
                    'match_id': match['id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_date': match['match_datetime'],
                    'season': match['season'],
                    'prediction': pred['prediction'],
                    'probabilities': pred['probabilities'],
                    'confidence': pred['confidence']
                })
        
        return predictions
    
    def save_model(self, filepath='model.pkl'):
        if self.model is None:
            print("No model to save")
            return False
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
            'accuracy': self.model_accuracy
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Model saved to {filepath}")
        return True
    
    def load_model(self, filepath='model.pkl'):
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.model_accuracy = model_data['accuracy']
            
            print(f"Model loaded from {filepath} (Accuracy: {self.model_accuracy:.3f})")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

if __name__ == '__main__':
    predictor = AdvancedSuperLigPredictor()
    
    if predictor.train_model():
        predictor.save_model('/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_model.pkl')
        
        print("\n" + "="*50)
        print("Upcoming Match Predictions:")
        print("="*50)
        
        predictions = predictor.predict_upcoming_matches()
        for pred in predictions[:10]:
            print(f"\n{pred['home_team']} vs {pred['away_team']}")
            print(f"  Prediction: {pred['prediction']} (Confidence: {pred['confidence']:.1%})")
            print(f"  Probabilities: H:{pred['probabilities']['Home Win']:.1%} D:{pred['probabilities']['Draw']:.1%} A:{pred['probabilities']['Away Win']:.1%}")
