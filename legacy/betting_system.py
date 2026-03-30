import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from advanced_predictor import AdvancedSuperLigPredictor

class BettingRecommendationSystem:
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'):
        self.db_path = db_path
        self.predictor = AdvancedSuperLigPredictor(db_path)
        
        try:
            self.predictor.load_model('/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_model.pkl')
        except:
            print("Model not found, will need to train first")
    
    def calculate_value_bet(self, predicted_prob, odds):
        if odds <= 1.0:
            return 0
        
        implied_prob = 1 / odds
        expected_value = (predicted_prob * odds) - 1
        
        value = expected_value / implied_prob if implied_prob > 0 else 0
        
        return value
    
    def get_betting_recommendation(self, home_team_id, away_team_id, odds=None):
        prediction = self.predictor.predict_match(home_team_id, away_team_id)
        
        if not prediction:
            return None
        
        probs = prediction['probabilities']
        
        if odds is None:
            odds = {
                'Home Win': 1 / probs['Home Win'] * 0.9,
                'Draw': 1 / probs['Draw'] * 0.9,
                'Away Win': 1 / probs['Away Win'] * 0.9
            }
        
        recommendations = []
        
        for outcome, prob in probs.items():
            if outcome in odds:
                value = self.calculate_value_bet(prob, odds[outcome])
                
                if value > 0.1 and prob > 0.3:
                    recommendations.append({
                        'outcome': outcome,
                        'probability': prob,
                        'odds': odds[outcome],
                        'value': value,
                        'confidence': prediction['confidence'] if prediction['prediction'] == outcome else prob
                    })
        
        recommendations.sort(key=lambda x: x['value'], reverse=True)
        
        over_under_prob = self._calculate_over_under_probability(
            prediction['features']['home_avg_goals_scored_5'],
            prediction['features']['away_avg_goals_scored_5'],
            prediction['features']['home_avg_goals_conceded_5'],
            prediction['features']['away_avg_goals_conceded_5']
        )
        
        btts_prob = self._calculate_btts_probability(
            prediction['features']['home_btts_rate_5'],
            prediction['features']['away_btts_rate_5'],
            prediction['features']['h2h_btts_rate']
        )
        
        return {
            'main_prediction': prediction['prediction'],
            'probabilities': probs,
            'confidence': prediction['confidence'],
            'recommendations': recommendations,
            'over_2_5_probability': over_under_prob,
            'btts_probability': btts_prob,
            'features': prediction['features']
        }
    
    def _calculate_over_under_probability(self, home_avg_scored, away_avg_scored, home_avg_conceded, away_avg_conceded):
        expected_goals = (home_avg_scored + away_avg_conceded) / 2 + (away_avg_scored + home_avg_conceded) / 2
        
        if expected_goals > 2.7:
            return min(0.75, expected_goals / 4)
        elif expected_goals > 2.3:
            return 0.5 + (expected_goals - 2.3) / 2
        else:
            return max(0.25, expected_goals / 4)
    
    def _calculate_btts_probability(self, home_btts_rate, away_btts_rate, h2h_btts_rate):
        avg_btts = (home_btts_rate + away_btts_rate + h2h_btts_rate) / 3
        return avg_btts
    
    def generate_accumulator_coupon(self, min_confidence=0.6, max_matches=5, target_odds=3.0):
        upcoming = self.predictor.get_upcoming_matches(limit=30)
        
        if upcoming.empty:
            return None
        
        match_predictions = []
        
        for _, match in upcoming.iterrows():
            rec = self.get_betting_recommendation(match['home_team_id'], match['away_team_id'])
            
            if rec and rec['confidence'] >= min_confidence:
                match_predictions.append({
                    'match_id': match['id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_date': match['match_datetime'],
                    'prediction': rec['main_prediction'],
                    'confidence': rec['confidence'],
                    'probabilities': rec['probabilities'],
                    'odds': 1 / rec['probabilities'][rec['main_prediction']] * 0.9
                })
        
        match_predictions.sort(key=lambda x: x['confidence'], reverse=True)
        
        selected_matches = match_predictions[:max_matches]
        
        total_odds = 1.0
        for match in selected_matches:
            total_odds *= match['odds']
        
        avg_confidence = sum(m['confidence'] for m in selected_matches) / len(selected_matches) if selected_matches else 0
        
        return {
            'matches': selected_matches,
            'total_odds': total_odds,
            'num_matches': len(selected_matches),
            'avg_confidence': avg_confidence,
            'recommended_stake': self._calculate_recommended_stake(avg_confidence, total_odds)
        }
    
    def generate_safe_coupon(self, min_confidence=0.7):
        return self.generate_accumulator_coupon(min_confidence=min_confidence, max_matches=3, target_odds=2.0)
    
    def generate_risky_coupon(self, min_confidence=0.5):
        return self.generate_accumulator_coupon(min_confidence=min_confidence, max_matches=8, target_odds=10.0)
    
    def _calculate_recommended_stake(self, confidence, odds):
        if confidence < 0.5 or odds < 1.5:
            return 0
        
        kelly_fraction = (confidence * odds - 1) / (odds - 1)
        kelly_fraction = max(0, min(kelly_fraction, 0.1))
        
        recommended_percentage = kelly_fraction * 100
        
        return round(recommended_percentage, 2)
    
    def get_daily_tips(self, date=None):
        if date is None:
            date = datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.id, m.home_team_id, m.away_team_id, m.match_datetime,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE DATE(m.match_datetime) = DATE(?)
            AND m.home_score IS NULL
            ORDER BY m.match_datetime
        '''
        
        matches = pd.read_sql_query(query, conn, params=[date.strftime('%Y-%m-%d')])
        conn.close()
        
        tips = []
        
        for _, match in matches.iterrows():
            rec = self.get_betting_recommendation(match['home_team_id'], match['away_team_id'])
            
            if rec:
                tip_quality = 'HIGH' if rec['confidence'] > 0.7 else 'MEDIUM' if rec['confidence'] > 0.5 else 'LOW'
                
                tips.append({
                    'match_id': match['id'],
                    'home_team': match['home_team'],
                    'away_team': match['away_team'],
                    'match_time': match['match_datetime'],
                    'main_tip': rec['main_prediction'],
                    'confidence': rec['confidence'],
                    'quality': tip_quality,
                    'probabilities': rec['probabilities'],
                    'over_2_5': rec['over_2_5_probability'],
                    'btts': rec['btts_probability'],
                    'recommendations': rec['recommendations'][:3]
                })
        
        return tips
    
    def analyze_team_performance(self, team_name, last_n_matches=10):
        conn = sqlite3.connect(self.db_path)
        
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM teams WHERE name LIKE ? OR normalized_name LIKE ?', 
                      (f'%{team_name}%', f'%{team_name.upper()}%'))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        team_id = result[0]
        
        stats = self.predictor.get_team_stats(team_id, last_n_matches=last_n_matches)
        
        query = '''
            SELECT m.match_datetime, 
                   CASE WHEN m.home_team_id = ? THEN t2.name ELSE t1.name END as opponent,
                   CASE WHEN m.home_team_id = ? THEN 'Home' ELSE 'Away' END as venue,
                   CASE WHEN m.home_team_id = ? THEN m.home_score ELSE m.away_score END as goals_for,
                   CASE WHEN m.home_team_id = ? THEN m.away_score ELSE m.home_score END as goals_against,
                   CASE 
                       WHEN (m.home_team_id = ? AND m.home_score > m.away_score) OR 
                            (m.away_team_id = ? AND m.away_score > m.home_score) THEN 'W'
                       WHEN m.home_score = m.away_score THEN 'D'
                       ELSE 'L'
                   END as result
            FROM matches m
            JOIN teams t1 ON m.home_team_id = t1.id
            JOIN teams t2 ON m.away_team_id = t2.id
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.home_score IS NOT NULL
            ORDER BY m.match_datetime DESC
            LIMIT ?
        '''
        
        recent_matches = pd.read_sql_query(query, conn, params=[team_id]*6 + [team_id, team_id, last_n_matches])
        conn.close()
        
        return {
            'team_name': team_name,
            'stats': stats,
            'recent_matches': recent_matches.to_dict('records'),
            'form': ''.join(recent_matches['result'].tolist()[:5])
        }

if __name__ == '__main__':
    betting_system = BettingRecommendationSystem()
    
    print("="*60)
    print("SÜPER LIG BETTING RECOMMENDATION SYSTEM")
    print("="*60)
    
    safe_coupon = betting_system.generate_safe_coupon()
    if safe_coupon:
        print("\n🟢 GÜVENLİ KUPON (Yüksek Güven)")
        print(f"Toplam Oran: {safe_coupon['total_odds']:.2f}")
        print(f"Ortalama Güven: {safe_coupon['avg_confidence']:.1%}")
        print(f"Önerilen Yatırım: %{safe_coupon['recommended_stake']:.1f}")
        print("\nMaçlar:")
        for i, match in enumerate(safe_coupon['matches'], 1):
            print(f"{i}. {match['home_team']} vs {match['away_team']}")
            print(f"   Tahmin: {match['prediction']} (Oran: {match['odds']:.2f}, Güven: {match['confidence']:.1%})")
    
    risky_coupon = betting_system.generate_risky_coupon()
    if risky_coupon:
        print("\n🔴 RİSKLİ KUPON (Yüksek Oran)")
        print(f"Toplam Oran: {risky_coupon['total_odds']:.2f}")
        print(f"Ortalama Güven: {risky_coupon['avg_confidence']:.1%}")
        print(f"Önerilen Yatırım: %{risky_coupon['recommended_stake']:.1f}")
        print(f"Maç Sayısı: {risky_coupon['num_matches']}")
