import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from typing import Dict, List, Tuple, Optional

class DynamicPricingEngine:
    """
    Dinamik fiyatlandırma motoru - Bahis oranlarını piyasa koşullarına göre optimize eder
    """
    
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/superlig_full.db'):
        self.db_path = db_path
        self.base_margin = 0.10
        self.min_margin = 0.05
        self.max_margin = 0.25
        
        self.risk_multipliers = {
            'very_low': 0.85,
            'low': 0.90,
            'medium': 1.00,
            'high': 1.10,
            'very_high': 1.20
        }
        
        self.market_conditions = {
            'demand_high': 1.05,
            'demand_normal': 1.00,
            'demand_low': 0.95
        }
    
    def calculate_dynamic_odds(self, 
                              predicted_probability: float,
                              confidence: float,
                              market_demand: str = 'normal',
                              risk_level: str = 'medium',
                              liquidity_factor: float = 1.0) -> Dict[str, float]:
        """
        Dinamik oran hesaplama
        
        Args:
            predicted_probability: Model tahmini olasılığı (0-1)
            confidence: Tahmin güveni (0-1)
            market_demand: Piyasa talebi ('high', 'normal', 'low')
            risk_level: Risk seviyesi ('very_low', 'low', 'medium', 'high', 'very_high')
            liquidity_factor: Likidite faktörü (0.5-1.5)
        
        Returns:
            Dict: Dinamik fiyatlandırma bilgileri
        """
        
        adjusted_margin = self._calculate_adjusted_margin(
            confidence, market_demand, risk_level, liquidity_factor
        )
        
        fair_odds = 1 / predicted_probability if predicted_probability > 0 else 100
        
        margin_multiplier = 1 - adjusted_margin
        offered_odds = fair_odds * margin_multiplier
        
        risk_mult = self.risk_multipliers.get(risk_level, 1.0)
        offered_odds *= risk_mult
        
        demand_key = f'demand_{market_demand}'
        demand_mult = self.market_conditions.get(demand_key, 1.0)
        offered_odds *= demand_mult
        
        offered_odds *= liquidity_factor
        
        offered_odds = max(1.01, min(offered_odds, 100.0))
        
        implied_probability = 1 / offered_odds
        edge = (predicted_probability - implied_probability) / predicted_probability * 100
        
        return {
            'fair_odds': round(fair_odds, 2),
            'offered_odds': round(offered_odds, 2),
            'margin': round(adjusted_margin * 100, 2),
            'implied_probability': round(implied_probability, 4),
            'predicted_probability': round(predicted_probability, 4),
            'edge_percentage': round(edge, 2),
            'risk_level': risk_level,
            'market_demand': market_demand,
            'confidence': round(confidence, 4)
        }
    
    def _calculate_adjusted_margin(self, 
                                   confidence: float,
                                   market_demand: str,
                                   risk_level: str,
                                   liquidity_factor: float) -> float:
        """Ayarlanmış kar marjı hesaplama"""
        
        margin = self.base_margin
        
        if confidence > 0.8:
            margin *= 0.8
        elif confidence > 0.6:
            margin *= 0.9
        elif confidence < 0.4:
            margin *= 1.2
        
        if market_demand == 'high':
            margin *= 1.1
        elif market_demand == 'low':
            margin *= 0.9
        
        if risk_level in ['very_high', 'high']:
            margin *= 1.15
        elif risk_level in ['very_low', 'low']:
            margin *= 0.85
        
        if liquidity_factor < 0.8:
            margin *= 1.1
        elif liquidity_factor > 1.2:
            margin *= 0.95
        
        return max(self.min_margin, min(margin, self.max_margin))
    
    def calculate_match_odds_dynamic(self, 
                                    probabilities: Dict[str, float],
                                    confidence: float,
                                    team_popularity: Dict[str, float] = None) -> Dict[str, Dict]:
        """
        Maç için tüm sonuçların dinamik oranlarını hesapla
        
        Args:
            probabilities: {'Home Win': 0.45, 'Draw': 0.30, 'Away Win': 0.25}
            confidence: Model güveni
            team_popularity: Takım popülaritesi skorları (0-1)
        
        Returns:
            Dict: Her sonuç için dinamik fiyatlandırma
        """
        
        if team_popularity is None:
            team_popularity = {'home': 0.5, 'away': 0.5}
        
        results = {}
        
        for outcome, probability in probabilities.items():
            if outcome == 'Home Win':
                demand = self._determine_demand(team_popularity.get('home', 0.5))
                risk = self._determine_risk(probability, 'home')
            elif outcome == 'Away Win':
                demand = self._determine_demand(team_popularity.get('away', 0.5))
                risk = self._determine_risk(probability, 'away')
            else:
                demand = 'normal'
                risk = self._determine_risk(probability, 'draw')
            
            liquidity = self._calculate_liquidity_factor(probability, confidence)
            
            results[outcome] = self.calculate_dynamic_odds(
                predicted_probability=probability,
                confidence=confidence,
                market_demand=demand,
                risk_level=risk,
                liquidity_factor=liquidity
            )
        
        total_margin = sum(1/r['offered_odds'] for r in results.values())
        overround = (total_margin - 1) * 100
        
        return {
            'outcomes': results,
            'total_overround': round(overround, 2),
            'total_margin_percentage': round(overround, 2),
            'is_balanced': 0.95 <= total_margin <= 1.15
        }
    
    def _determine_demand(self, popularity: float) -> str:
        """Takım popülaritesine göre talep seviyesi belirle"""
        if popularity > 0.7:
            return 'high'
        elif popularity < 0.3:
            return 'low'
        return 'normal'
    
    def _determine_risk(self, probability: float, outcome_type: str) -> str:
        """Olasılığa göre risk seviyesi belirle"""
        if probability > 0.7:
            return 'very_low'
        elif probability > 0.55:
            return 'low'
        elif probability > 0.35:
            return 'medium'
        elif probability > 0.20:
            return 'high'
        else:
            return 'very_high'
    
    def _calculate_liquidity_factor(self, probability: float, confidence: float) -> float:
        """Likidite faktörü hesapla"""
        base_liquidity = 1.0
        
        if probability < 0.15 or probability > 0.85:
            base_liquidity *= 0.85
        
        if confidence < 0.5:
            base_liquidity *= 0.90
        elif confidence > 0.8:
            base_liquidity *= 1.05
        
        return max(0.5, min(base_liquidity, 1.5))
    
    def optimize_odds_for_profit(self, 
                                 match_odds: Dict[str, Dict],
                                 target_margin: float = 0.10,
                                 max_iterations: int = 100) -> Dict[str, Dict]:
        """
        Kar marjını optimize etmek için oranları ayarla
        
        Args:
            match_odds: calculate_match_odds_dynamic çıktısı
            target_margin: Hedef kar marjı (0.05-0.20)
            max_iterations: Maksimum iterasyon sayısı
        
        Returns:
            Optimize edilmiş oranlar
        """
        
        outcomes = match_odds['outcomes'].copy()
        current_overround = match_odds['total_overround'] / 100
        target_overround = target_margin
        
        if abs(current_overround - target_overround) < 0.01:
            return match_odds
        
        adjustment_factor = (1 + target_overround) / (1 + current_overround)
        
        for outcome in outcomes:
            current_odds = outcomes[outcome]['offered_odds']
            new_odds = current_odds * adjustment_factor
            new_odds = max(1.01, min(new_odds, 100.0))
            
            outcomes[outcome]['offered_odds'] = round(new_odds, 2)
            outcomes[outcome]['implied_probability'] = round(1 / new_odds, 4)
            outcomes[outcome]['margin'] = round(target_margin * 100, 2)
        
        new_total_margin = sum(1/o['offered_odds'] for o in outcomes.values())
        new_overround = (new_total_margin - 1) * 100
        
        return {
            'outcomes': outcomes,
            'total_overround': round(new_overround, 2),
            'total_margin_percentage': round(new_overround, 2),
            'is_balanced': 0.95 <= new_total_margin <= 1.15,
            'optimized': True
        }
    
    def get_team_popularity_score(self, team_id: int) -> float:
        """
        Takım popülarite skoru hesapla (geçmiş maç verileri, taraftar sayısı vb.)
        
        Returns:
            float: 0-1 arası popülarite skoru
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT COUNT(*) as match_count,
                   AVG(CASE WHEN home_team_id = ? THEN home_score ELSE away_score END) as avg_goals,
                   SUM(CASE 
                       WHEN (home_team_id = ? AND home_score > away_score) OR 
                            (away_team_id = ? AND away_score > home_score) THEN 1 
                       ELSE 0 
                   END) * 1.0 / COUNT(*) as win_rate
            FROM matches
            WHERE (home_team_id = ? OR away_team_id = ?)
            AND home_score IS NOT NULL
            AND match_datetime >= date('now', '-365 days')
        '''
        
        cursor = conn.cursor()
        cursor.execute(query, [team_id] * 5)
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] == 0:
            return 0.5
        
        match_count, avg_goals, win_rate = result
        
        popularity = 0.0
        
        if match_count > 30:
            popularity += 0.3
        elif match_count > 20:
            popularity += 0.2
        else:
            popularity += 0.1
        
        if win_rate and win_rate > 0.6:
            popularity += 0.4
        elif win_rate and win_rate > 0.4:
            popularity += 0.3
        else:
            popularity += 0.1
        
        if avg_goals and avg_goals > 1.5:
            popularity += 0.3
        elif avg_goals and avg_goals > 1.0:
            popularity += 0.2
        else:
            popularity += 0.1
        
        return min(1.0, max(0.0, popularity))
    
    def simulate_market_response(self, 
                                odds: Dict[str, float],
                                time_to_match: int,
                                betting_volume: float = 1.0) -> Dict[str, Dict]:
        """
        Piyasa tepkisini simüle et ve oranları ayarla
        
        Args:
            odds: Mevcut oranlar
            time_to_match: Maça kalan saat
            betting_volume: Bahis hacmi çarpanı (0.5-2.0)
        
        Returns:
            Güncellenmiş oranlar ve piyasa bilgisi
        """
        
        adjusted_odds = {}
        
        for outcome, odd_value in odds.items():
            time_factor = 1.0
            if time_to_match < 2:
                time_factor = 0.95
            elif time_to_match < 6:
                time_factor = 0.98
            elif time_to_match > 48:
                time_factor = 1.02
            
            volume_factor = 1.0
            if betting_volume > 1.5:
                volume_factor = 0.97
            elif betting_volume < 0.7:
                volume_factor = 1.03
            
            new_odd = odd_value * time_factor * volume_factor
            new_odd = max(1.01, min(new_odd, 100.0))
            
            adjusted_odds[outcome] = {
                'original_odds': round(odd_value, 2),
                'adjusted_odds': round(new_odd, 2),
                'time_factor': round(time_factor, 3),
                'volume_factor': round(volume_factor, 3),
                'change_percentage': round((new_odd - odd_value) / odd_value * 100, 2)
            }
        
        return {
            'adjusted_odds': adjusted_odds,
            'time_to_match_hours': time_to_match,
            'betting_volume_multiplier': betting_volume,
            'market_volatility': self._calculate_volatility(time_to_match, betting_volume)
        }
    
    def _calculate_volatility(self, time_to_match: int, betting_volume: float) -> str:
        """Piyasa volatilitesini hesapla"""
        volatility_score = 0
        
        if time_to_match < 3:
            volatility_score += 2
        elif time_to_match < 12:
            volatility_score += 1
        
        if betting_volume > 1.5 or betting_volume < 0.7:
            volatility_score += 2
        elif betting_volume > 1.2 or betting_volume < 0.8:
            volatility_score += 1
        
        if volatility_score >= 3:
            return 'high'
        elif volatility_score >= 1:
            return 'medium'
        return 'low'
    
    def generate_pricing_report(self, 
                               home_team_id: int,
                               away_team_id: int,
                               probabilities: Dict[str, float],
                               confidence: float) -> Dict:
        """
        Kapsamlı fiyatlandırma raporu oluştur
        """
        
        home_popularity = self.get_team_popularity_score(home_team_id)
        away_popularity = self.get_team_popularity_score(away_team_id)
        
        team_popularity = {
            'home': home_popularity,
            'away': away_popularity
        }
        
        base_odds = self.calculate_match_odds_dynamic(
            probabilities=probabilities,
            confidence=confidence,
            team_popularity=team_popularity
        )
        
        optimized_odds = self.optimize_odds_for_profit(
            match_odds=base_odds,
            target_margin=0.08
        )
        
        simple_odds = {k: v['offered_odds'] for k, v in optimized_odds['outcomes'].items()}
        market_sim = self.simulate_market_response(
            odds=simple_odds,
            time_to_match=24,
            betting_volume=1.0
        )
        
        return {
            'team_popularity': team_popularity,
            'base_pricing': base_odds,
            'optimized_pricing': optimized_odds,
            'market_simulation': market_sim,
            'recommendations': self._generate_pricing_recommendations(optimized_odds)
        }
    
    def _generate_pricing_recommendations(self, odds_data: Dict) -> List[str]:
        """Fiyatlandırma önerileri oluştur"""
        recommendations = []
        
        if odds_data['total_overround'] < 5:
            recommendations.append("⚠️ Kar marjı çok düşük - Oranları düşürmeyi düşünün")
        elif odds_data['total_overround'] > 15:
            recommendations.append("⚠️ Kar marjı çok yüksek - Rekabetçi olmayabilir")
        else:
            recommendations.append("✅ Kar marjı optimal seviyede")
        
        if not odds_data['is_balanced']:
            recommendations.append("⚠️ Oranlar dengesiz - Yeniden ayarlama gerekebilir")
        else:
            recommendations.append("✅ Oranlar dengeli")
        
        for outcome, data in odds_data['outcomes'].items():
            if data['edge_percentage'] < -10:
                recommendations.append(f"🔴 {outcome}: Müşteri lehine çok fazla avantaj var")
            elif data['edge_percentage'] > 20:
                recommendations.append(f"🟡 {outcome}: Oran çok düşük, talep azalabilir")
        
        return recommendations


if __name__ == '__main__':
    pricing_engine = DynamicPricingEngine()
    
    print("="*70)
    print("DYNAMIC PRICING ENGINE - TEST")
    print("="*70)
    
    test_probabilities = {
        'Home Win': 0.45,
        'Draw': 0.30,
        'Away Win': 0.25
    }
    
    print("\n📊 Test Olasılıkları:")
    for outcome, prob in test_probabilities.items():
        print(f"  {outcome}: {prob:.1%}")
    
    print("\n" + "="*70)
    print("SENARYO 1: Yüksek Güven, Normal Talep")
    print("="*70)
    
    result1 = pricing_engine.calculate_match_odds_dynamic(
        probabilities=test_probabilities,
        confidence=0.75,
        team_popularity={'home': 0.6, 'away': 0.4}
    )
    
    print(f"\nToplam Overround: {result1['total_overround']:.2f}%")
    print(f"Dengeli mi: {'✅ Evet' if result1['is_balanced'] else '❌ Hayır'}")
    print("\nOranlar:")
    for outcome, data in result1['outcomes'].items():
        print(f"\n{outcome}:")
        print(f"  Fair Oran: {data['fair_odds']:.2f}")
        print(f"  Sunulan Oran: {data['offered_odds']:.2f}")
        print(f"  Marj: {data['margin']:.2f}%")
        print(f"  Edge: {data['edge_percentage']:.2f}%")
        print(f"  Risk: {data['risk_level']}")
    
    print("\n" + "="*70)
    print("SENARYO 2: Optimize Edilmiş Oranlar")
    print("="*70)
    
    optimized = pricing_engine.optimize_odds_for_profit(result1, target_margin=0.08)
    
    print(f"\nOptimize Edilmiş Overround: {optimized['total_overround']:.2f}%")
    print("\nOptimize Edilmiş Oranlar:")
    for outcome, data in optimized['outcomes'].items():
        print(f"  {outcome}: {data['offered_odds']:.2f}")
    
    print("\n" + "="*70)
    print("SENARYO 3: Piyasa Simülasyonu (Maça 2 saat kala)")
    print("="*70)
    
    simple_odds = {k: v['offered_odds'] for k, v in optimized['outcomes'].items()}
    market_sim = pricing_engine.simulate_market_response(
        odds=simple_odds,
        time_to_match=2,
        betting_volume=1.8
    )
    
    print(f"\nPiyasa Volatilitesi: {market_sim['market_volatility'].upper()}")
    print("\nOran Değişimleri:")
    for outcome, data in market_sim['adjusted_odds'].items():
        print(f"\n{outcome}:")
        print(f"  Orijinal: {data['original_odds']:.2f}")
        print(f"  Güncel: {data['adjusted_odds']:.2f}")
        print(f"  Değişim: {data['change_percentage']:+.2f}%")
