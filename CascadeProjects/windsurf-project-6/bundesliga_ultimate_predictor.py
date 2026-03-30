#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundesliga Ultimate Predictor - Tüm Gelişmiş Özellikleri İçeren Sistem
"""

import sqlite3
import pickle
from bundesliga_advanced_stats import BundesligaAdvancedStats
from bundesliga_player_weather import BundesligaPlayerWeather
from bundesliga_advanced_models import PoissonScorePredictor, EnsemblePredictor
from bundesliga_predictor import BundesligaPredictor

class BundesligaUltimatePredictor:
    """
    Tüm gelişmiş özellikleri birleştiren ultimate tahmin sistemi
    """
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
        
        # Temel tahmin modeli
        self.base_predictor = BundesligaPredictor(db_path)
        
        # Gelişmiş istatistikler
        self.advanced_stats = BundesligaAdvancedStats(db_path)
        
        # Oyuncu ve hava durumu
        self.player_weather = BundesligaPlayerWeather(db_path)
        
        # Gelişmiş modeller
        self.poisson = PoissonScorePredictor(db_path)
        self.ensemble = None  # İsteğe bağlı - eğitilmesi uzun sürer
        
        # Modelleri yükle
        self.load_models()
    
    def load_models(self):
        """
        Tüm modelleri yükle
        """
        try:
            self.base_predictor.load_model('bundesliga_model.pkl')
            print("✅ Temel model yüklendi")
        except:
            print("⚠️  Temel model bulunamadı")
        
        try:
            self.poisson.train()
            print("✅ Poisson model eğitildi")
        except Exception as e:
            print(f"⚠️  Poisson model hatası: {e}")
    
    def get_comprehensive_prediction(self, home_team_id, away_team_id, home_team_name=None, away_team_name=None):
        """
        Kapsamlı tahmin - tüm özellikleri içerir
        """
        result = {}
        
        # 1. Temel tahmin (Random Forest)
        try:
            base_pred = self.base_predictor.predict_match(home_team_id, away_team_id)
            result['base_prediction'] = base_pred
        except Exception as e:
            result['base_prediction'] = {'error': str(e)}
        
        # 2. Poisson skor tahmini
        try:
            poisson_pred = self.poisson.predict_score_probabilities(home_team_id, away_team_id)
            result['poisson_prediction'] = poisson_pred
        except Exception as e:
            result['poisson_prediction'] = {'error': str(e)}
        
        # 3. xG (Expected Goals)
        try:
            home_xg = self.advanced_stats.calculate_xg(home_team_id, is_home=True, last_n=10)
            away_xg = self.advanced_stats.calculate_xg(away_team_id, is_home=False, last_n=10)
            result['xg'] = {
                'home': home_xg,
                'away': away_xg
            }
        except Exception as e:
            result['xg'] = {'error': str(e)}
        
        # 4. Form analizi
        try:
            home_form = self.advanced_stats.get_form_analysis(home_team_id, last_n=5)
            away_form = self.advanced_stats.get_form_analysis(away_team_id, last_n=5)
            result['form'] = {
                'home': home_form,
                'away': away_form
            }
        except Exception as e:
            result['form'] = {'error': str(e)}
        
        # 5. Momentum
        try:
            home_momentum = self.advanced_stats.calculate_momentum(home_team_id, window=10)
            away_momentum = self.advanced_stats.calculate_momentum(away_team_id, window=10)
            result['momentum'] = {
                'home': home_momentum,
                'away': away_momentum
            }
        except Exception as e:
            result['momentum'] = {'error': str(e)}
        
        # 6. Oyuncu istatistikleri
        try:
            if home_team_name and away_team_name:
                home_scorer = self.player_weather.get_team_top_scorer(home_team_name)
                away_scorer = self.player_weather.get_team_top_scorer(away_team_name)
                result['top_scorers'] = {
                    'home': home_scorer,
                    'away': away_scorer
                }
        except Exception as e:
            result['top_scorers'] = {'error': str(e)}
        
        # 7. Final tahmin - tüm modellerin birleşimi
        result['final_prediction'] = self._combine_predictions(result)
        
        return result
    
    def _combine_predictions(self, all_predictions):
        """
        Tüm tahminleri birleştir ve final tahmin oluştur
        """
        # Temel tahmin
        base = all_predictions.get('base_prediction', {})
        poisson = all_predictions.get('poisson_prediction', {})
        
        if 'error' in base or 'error' in poisson:
            return {
                'prediction': 'Unknown',
                'confidence': 0.0,
                'score': 'N/A'
            }
        
        # Sonuç tahmini - temel modelden
        prediction = base.get('prediction', 'Unknown')
        
        # Olasılıklar - temel model %70, Poisson %30
        base_probs = base.get('probabilities', {})
        poisson_probs = {
            'Home Win': poisson.get('home_win_prob', 0.33),
            'Draw': poisson.get('draw_prob', 0.33),
            'Away Win': poisson.get('away_win_prob', 0.33)
        }
        
        combined_probs = {}
        for key in ['Home Win', 'Draw', 'Away Win']:
            combined_probs[key] = (base_probs.get(key, 0) * 0.7) + (poisson_probs.get(key, 0) * 0.3)
        
        # En yüksek olasılık
        final_prediction = max(combined_probs, key=combined_probs.get)
        confidence = combined_probs[final_prediction]
        
        # Skor tahmini - Poisson'dan
        score = poisson.get('most_likely_score', 'N/A')
        
        # Skor ile tahmin uyumlu olmalı - skora göre tahmini düzelt
        if isinstance(score, str) and '-' in score:
            try:
                home_score, away_score = map(int, score.split('-'))
                if home_score > away_score:
                    score_prediction = 'Home Win'
                elif away_score > home_score:
                    score_prediction = 'Away Win'
                else:
                    score_prediction = 'Draw'
                
                # Eğer skor tahmini ile olasılık tahmini çok farklıysa, skoru düzelt
                if score_prediction != final_prediction:
                    # Final prediction'a göre skoru ayarla
                    if final_prediction == 'Home Win':
                        # Ev sahibi kazanmalı
                        if home_score <= away_score:
                            score = f"{away_score + 1}-{away_score}"
                    elif final_prediction == 'Away Win':
                        # Deplasman kazanmalı
                        if away_score <= home_score:
                            score = f"{home_score}-{home_score + 1}"
                    elif final_prediction == 'Draw':
                        # Berabere olmalı
                        if home_score != away_score:
                            avg = (home_score + away_score) // 2
                            score = f"{avg}-{avg}"
            except:
                pass
        
        return {
            'prediction': final_prediction,
            'confidence': round(confidence, 3),
            'probabilities': combined_probs,
            'predicted_score': score,
            'score_probabilities': poisson.get('score_probabilities', {})
        }
    
    def get_power_rankings(self):
        """
        Güç sıralaması
        """
        try:
            return self.advanced_stats.calculate_power_ranking()
        except Exception as e:
            return {'error': str(e)}
    
    def get_top_scorers(self, limit=20):
        """
        Gol kralları
        """
        try:
            return self.player_weather.get_top_scorers(2025, limit)
        except Exception as e:
            return {'error': str(e)}
    
    def predict_upcoming_matches(self):
        """
        Gelecek hafta maçlarını tahmin et (sadece bir sonraki matchday)
        """
        conn = sqlite3.connect(self.db_path)
        
        # Önce bir sonraki hafta numarasını bul (sadece gelecekteki maçlar)
        next_matchday_query = '''
            SELECT MIN(matchday) 
            FROM matches 
            WHERE is_finished = 0 
            AND match_datetime > datetime('now', '+2 hours')
        '''
        
        next_matchday = conn.execute(next_matchday_query).fetchone()[0]
        
        if not next_matchday:
            conn.close()
            return []
        
        # Sadece o haftanın maçlarını al (henüz başlamamış olanlar)
        query = '''
            SELECT m.match_id, m.home_team_id, m.away_team_id, m.match_datetime, m.matchday,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.is_finished = 0
            AND m.matchday = ?
            AND m.match_datetime > datetime('now')
            ORDER BY m.match_datetime
        '''
        
        matches = conn.execute(query, (next_matchday,)).fetchall()
        conn.close()
        
        predictions = []
        
        for match in matches:
            match_id, home_id, away_id, match_dt, matchday, home_name, away_name = match
            
            # Kapsamlı tahmin
            pred = self.get_comprehensive_prediction(home_id, away_id, home_name, away_name)
            
            predictions.append({
                'match_id': match_id,
                'home_team': home_name,
                'away_team': away_name,
                'match_datetime': str(match_dt),
                'matchday': matchday,
                'prediction': pred['final_prediction']['prediction'],
                'confidence': pred['final_prediction']['confidence'],
                'probabilities': pred['final_prediction']['probabilities'],
                'predicted_score': pred['final_prediction']['predicted_score'],
                'xg_home': pred['xg']['home']['xg'] if 'error' not in pred['xg'] else 0,
                'xg_away': pred['xg']['away']['xg'] if 'error' not in pred['xg'] else 0,
                'form_home': pred['form']['home']['form'] if 'error' not in pred['form'] else 'N/A',
                'form_away': pred['form']['away']['form'] if 'error' not in pred['form'] else 'N/A',
                'momentum_home': pred['momentum']['home']['direction'] if 'error' not in pred['momentum'] else 'stable',
                'momentum_away': pred['momentum']['away']['direction'] if 'error' not in pred['momentum'] else 'stable',
                'top_scorer_home': pred['top_scorers']['home']['name'] if 'top_scorers' in pred and pred['top_scorers'].get('home') else None,
                'top_scorer_away': pred['top_scorers']['away']['name'] if 'top_scorers' in pred and pred['top_scorers'].get('away') else None
            })
        
        return predictions

if __name__ == '__main__':
    print("="*70)
    print("🚀 BUNDESLIGA ULTIMATE PREDICTOR")
    print("="*70)
    
    predictor = BundesligaUltimatePredictor()
    
    # Güç sıralaması
    print("\n💪 GÜÇ SIRALAMASI (Top 5)")
    print("="*70)
    rankings = predictor.get_power_rankings()
    if 'error' not in rankings:
        for rank in rankings[:5]:
            print(f"{rank['rank']:2d}. {rank['team']:30s} - Güç: {rank['power_score']:6.1f} | Form: {rank['form']}")
    
    # Gol kralları
    print("\n⚽ GOL KRALLARI (Top 5)")
    print("="*70)
    scorers = predictor.get_top_scorers(5)
    if 'error' not in scorers:
        for i, scorer in enumerate(scorers):
            print(f"{i+1}. {scorer['name']:25s} - {scorer['goals']} gol")
    
    # Yaklaşan maçlar
    print("\n🔮 YAKLAŞAN MAÇLAR - KAPSAMLI TAHMİNLER")
    print("="*70)
    predictions = predictor.predict_upcoming_matches()
    
    for pred in predictions[:3]:
        print(f"\n{pred['home_team']} vs {pred['away_team']}")
        print(f"  Tahmin: {pred['prediction']} ({pred['confidence']*100:.1f}%)")
        print(f"  Skor: {pred['predicted_score']}")
        print(f"  xG: {pred['xg_home']:.2f} - {pred['xg_away']:.2f}")
        print(f"  Form: {pred['form_home']} vs {pred['form_away']}")
        print(f"  Momentum: {pred['momentum_home']} vs {pred['momentum_away']}")
        if pred['top_scorer_home']:
            print(f"  Golcüler: {pred['top_scorer_home']} vs {pred['top_scorer_away']}")
