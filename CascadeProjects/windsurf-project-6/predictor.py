import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class SuperLigPredictor:
    def __init__(self):
        self.db_path = 'superlig.db'
        self.model = None
        self.scaler = StandardScaler()
        self.features = [
            'home_team_points', 'away_team_points', 'home_team_goal_diff', 
            'away_team_goal_diff', 'home_team_form_points', 'away_team_form_points',
            'home_team_avg_goals', 'away_team_avg_goals', 'home_team_avg_conceded',
            'away_team_avg_conceded', 'h2h_home_wins', 'h2h_away_wins', 'h2h_draws'
        ]
    
    def prepare_training_data(self):
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.home_team_id, m.away_team_id, m.home_score, m.away_score,
                   m.match_date, ht.name as home_team_name, at.name as away_team_name
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.home_score IS NOT NULL
            ORDER BY m.match_date
        '''
        matches_df = pd.read_sql_query(query, conn)
        
        standings_query = '''
            SELECT team_id, season, points, goal_difference, position
            FROM standings
            WHERE season = '2023-2024'
        '''
        standings_df = pd.read_sql_query(standings_query, conn)
        
        conn.close()
        
        if matches_df.empty:
            return None, None
        
        features_list = []
        labels = []
        
        for _, match in matches_df.iterrows():
            home_team_id = match['home_team_id']
            away_team_id = match['away_team_id']
            
            home_standings = standings_df[standings_df['team_id'] == home_team_id]
            away_standings = standings_df[standings_df['team_id'] == away_team_id]
            
            if home_standings.empty or away_standings.empty:
                continue
            
            home_points = home_standings['points'].iloc[0]
            away_points = away_standings['points'].iloc[0]
            home_goal_diff = home_standings['goal_difference'].iloc[0]
            away_goal_diff = away_standings['goal_difference'].iloc[0]
            
            home_form = self._calculate_team_form(home_team_id, match['match_date'])
            away_form = self._calculate_team_form(away_team_id, match['match_date'])
            
            home_avg_goals = self._calculate_avg_goals(home_team_id, match['match_date'], True)
            away_avg_goals = self._calculate_avg_goals(away_team_id, match['match_date'], True)
            home_avg_conceded = self._calculate_avg_goals(home_team_id, match['match_date'], False)
            away_avg_conceded = self._calculate_avg_goals(away_team_id, match['match_date'], False)
            
            h2h_stats = self._calculate_h2h_stats(home_team_id, away_team_id, match['match_date'])
            
            feature_vector = [
                home_points, away_points, home_goal_diff, away_goal_diff,
                home_form, away_form, home_avg_goals, away_avg_goals,
                home_avg_conceded, away_avg_conceded,
                h2h_stats['home_wins'], h2h_stats['away_wins'], h2h_stats['draws']
            ]
            
            features_list.append(feature_vector)
            
            if match['home_score'] > match['away_score']:
                labels.append(2)  # Home win
            elif match['home_score'] < match['away_score']:
                labels.append(0)  # Away win
            else:
                labels.append(1)  # Draw
        
        X = np.array(features_list)
        y = np.array(labels)
        
        return X, y
    
    def _calculate_team_form(self, team_id, match_date, last_n=5):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT home_team_id, away_team_id, home_score, away_score
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND match_date < ?
            AND home_score IS NOT NULL
            ORDER BY match_date DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=[team_id, team_id, match_date, last_n])
        conn.close()
        
        points = 0
        for _, row in df.iterrows():
            if row['home_team_id'] == team_id:
                if row['home_score'] > row['away_score']:
                    points += 3
                elif row['home_score'] == row['away_score']:
                    points += 1
            else:
                if row['away_score'] > row['home_score']:
                    points += 3
                elif row['away_score'] == row['home_score']:
                    points += 1
        
        return points
    
    def _calculate_avg_goals(self, team_id, match_date, scored=True, last_n=10):
        conn = sqlite3.connect(self.db_path)
        if scored:
            query = '''
                SELECT home_score, away_score
                FROM matches
                WHERE (home_team_id = ? OR away_team_id = ?)
                AND match_date < ?
                AND home_score IS NOT NULL
                ORDER BY match_date DESC
                LIMIT ?
            '''
            df = pd.read_sql_query(query, conn, params=[team_id, team_id, match_date, last_n])
        else:
            query = '''
                SELECT home_score, away_score
                FROM matches
                WHERE (home_team_id = ? OR away_team_id = ?)
                AND match_date < ?
                AND home_score IS NOT NULL
                ORDER BY match_date DESC
                LIMIT ?
            '''
            df = pd.read_sql_query(query, conn, params=[team_id, team_id, match_date, last_n])
        
        conn.close()
        
        if df.empty:
            return 0.0
        
        goals = 0
        for _, row in df.iterrows():
            if row['home_team_id'] == team_id:
                goals += row['home_score'] if scored else row['away_score']
            else:
                goals += row['away_score'] if scored else row['home_score']
        
        return goals / len(df)
    
    def _calculate_h2h_stats(self, home_team_id, away_team_id, match_date, last_n=10):
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT home_team_id, home_score, away_score
            FROM matches
            WHERE ((home_team_id = ? AND away_team_id = ?) OR (home_team_id = ? AND away_team_id = ?))
            AND match_date < ?
            AND home_score IS NOT NULL
            ORDER BY match_date DESC
            LIMIT ?
        '''
        df = pd.read_sql_query(query, conn, params=[home_team_id, away_team_id, away_team_id, home_team_id, match_date, last_n])
        conn.close()
        
        stats = {'home_wins': 0, 'away_wins': 0, 'draws': 0}
        
        for _, row in df.iterrows():
            if row['home_team_id'] == home_team_id:
                if row['home_score'] > row['away_score']:
                    stats['home_wins'] += 1
                elif row['home_score'] == row['away_score']:
                    stats['draws'] += 1
                else:
                    stats['away_wins'] += 1
            else:
                if row['away_score'] > row['home_score']:
                    stats['home_wins'] += 1
                elif row['away_score'] == row['home_score']:
                    stats['draws'] += 1
                else:
                    stats['away_wins'] += 1
        
        return stats
    
    def train_model(self):
        X, y = self.prepare_training_data()
        
        if X is None or len(X) < 10:
            print("Insufficient data for training")
            return False
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train_scaled, y_train)
        
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model trained with accuracy: {accuracy:.3f}")
        return True
    
    def predict_match(self, home_team_id, away_team_id):
        if self.model is None:
            self.train_model()
        
        if self.model is None:
            return None
        
        conn = sqlite3.connect(self.db_path)
        
        standings_query = '''
            SELECT team_id, points, goal_difference
            FROM standings
            WHERE season = '2023-2024'
        '''
        standings_df = pd.read_sql_query(standings_query, conn)
        conn.close()
        
        home_standings = standings_df[standings_df['team_id'] == home_team_id]
        away_standings = standings_df[standings_df['team_id'] == away_team_id]
        
        if home_standings.empty or away_standings.empty:
            return None
        
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        feature_vector = [
            home_standings['points'].iloc[0], away_standings['points'].iloc[0],
            home_standings['goal_difference'].iloc[0], away_standings['goal_difference'].iloc[0],
            self._calculate_team_form(home_team_id, current_date),
            self._calculate_team_form(away_team_id, current_date),
            self._calculate_avg_goals(home_team_id, current_date, True),
            self._calculate_avg_goals(away_team_id, current_date, True),
            self._calculate_avg_goals(home_team_id, current_date, False),
            self._calculate_avg_goals(away_team_id, current_date, False),
            self._calculate_h2h_stats(home_team_id, away_team_id, current_date)['home_wins'],
            self._calculate_h2h_stats(home_team_id, away_team_id, current_date)['away_wins'],
            self._calculate_h2h_stats(home_team_id, away_team_id, current_date)['draws']
        ]
        
        X = np.array([feature_vector])
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
            'confidence': float(max(probabilities))
        }
    
    def get_current_predictions(self):
        conn = sqlite3.connect(self.db_path)
        
        upcoming_matches_query = '''
            SELECT m.id, m.home_team_id, m.away_team_id, m.match_date,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.match_date > datetime('now')
            ORDER BY m.match_date
            LIMIT 10
        '''
        upcoming_matches = pd.read_sql_query(upcoming_matches_query, conn)
        conn.close()
        
        predictions = []
        
        for _, match in upcoming_matches.iterrows():
            prediction = self.predict_match(match['home_team_id'], match['away_team_id'])
            
            if prediction:
                predictions.append({
                    'match_id': match['id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_date': match['match_date'],
                    'prediction': prediction['prediction'],
                    'probabilities': prediction['probabilities'],
                    'confidence': prediction['confidence']
                })
        
        return predictions

if __name__ == '__main__':
    predictor = SuperLigPredictor()
    predictor.train_model()
    predictions = predictor.get_current_predictions()
    for pred in predictions:
        print(f"{pred['home_team']} vs {pred['away_team']}: {pred['prediction']} (Confidence: {pred['confidence']:.2f})")
