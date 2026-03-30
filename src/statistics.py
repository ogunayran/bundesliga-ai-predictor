#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundesliga Gelişmiş İstatistikler ve Analiz Sistemi
- xG (Expected Goals)
- Form Analizi
- Güç Sıralaması
- Momentum Göstergesi
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle

class BundesligaAdvancedStats:
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
    
    def calculate_xg(self, team_id, is_home=True, last_n=10):
        """
        xG (Expected Goals) hesaplama
        Basitleştirilmiş model - gerçek şut verileri olmadığı için
        gol ve maç istatistiklerine göre hesaplıyoruz
        """
        conn = sqlite3.connect(self.db_path)
        
        if is_home:
            query = '''
                SELECT 
                    home_score,
                    away_score,
                    (SELECT COUNT(*) FROM matches m2 
                     WHERE m2.home_team_id = m.home_team_id 
                     AND m2.match_datetime < m.match_datetime 
                     AND m2.is_finished = 1) as match_number
                FROM matches m
                WHERE home_team_id = ? AND is_finished = 1
                ORDER BY match_datetime DESC
                LIMIT ?
            '''
        else:
            query = '''
                SELECT 
                    away_score,
                    home_score,
                    (SELECT COUNT(*) FROM matches m2 
                     WHERE m2.away_team_id = m.away_team_id 
                     AND m2.match_datetime < m.match_datetime 
                     AND m2.is_finished = 1) as match_number
                FROM matches m
                WHERE away_team_id = ? AND is_finished = 1
                ORDER BY match_datetime DESC
                LIMIT ?
            '''
        
        df = pd.read_sql_query(query, conn, params=[team_id, last_n])
        conn.close()
        
        if df.empty:
            return {
                'xg': 0.0,
                'xg_per_match': 0.0,
                'xg_diff': 0.0,
                'xg_performance': 0.0
            }
        
        # xG hesaplama - gol ortalaması + performans faktörü
        goals_scored = df.iloc[:, 0].mean()
        goals_conceded = df.iloc[:, 1].mean()
        
        # Performans faktörü - son maçlara daha fazla ağırlık
        weights = np.exp(-np.arange(len(df)) * 0.1)
        weighted_goals = np.average(df.iloc[:, 0], weights=weights)
        
        # xG = ağırlıklı gol ortalaması
        xg = weighted_goals
        xg_per_match = goals_scored
        xg_diff = goals_scored - goals_conceded
        
        # xG Performance = gerçek goller / beklenen goller
        xg_performance = goals_scored / max(xg, 0.1)
        
        return {
            'xg': round(xg, 2),
            'xg_per_match': round(xg_per_match, 2),
            'xg_diff': round(xg_diff, 2),
            'xg_performance': round(xg_performance, 2),
            'matches_analyzed': len(df)
        }
    
    def get_form_analysis(self, team_id, last_n=5):
        """
        Form analizi - son N maçtaki performans trendi
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                m.match_datetime,
                CASE 
                    WHEN m.home_team_id = ? THEN m.home_score
                    ELSE m.away_score
                END as goals_for,
                CASE 
                    WHEN m.home_team_id = ? THEN m.away_score
                    ELSE m.home_score
                END as goals_against,
                CASE 
                    WHEN m.home_team_id = ? THEN 'H'
                    ELSE 'A'
                END as venue,
                ht.name as home_team,
                at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.is_finished = 1
            ORDER BY m.match_datetime DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[team_id, team_id, team_id, team_id, team_id, last_n])
        conn.close()
        
        if df.empty:
            return {
                'form': 'N/A',
                'points': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'trend': 'stable',
                'matches': []
            }
        
        # Sonuçları hesapla
        results = []
        points = 0
        wins = 0
        draws = 0
        losses = 0
        
        for _, match in df.iterrows():
            gf = match['goals_for']
            ga = match['goals_against']
            
            if gf > ga:
                result = 'W'
                pts = 3
                wins += 1
            elif gf == ga:
                result = 'D'
                pts = 1
                draws += 1
            else:
                result = 'L'
                pts = 0
                losses += 1
            
            points += pts
            results.append({
                'result': result,
                'score': f'{gf}-{ga}',
                'opponent': match['away_team'] if match['venue'] == 'H' else match['home_team'],
                'venue': match['venue'],
                'date': str(match['match_datetime'])
            })
        
        # Form string (örn: "WWDLW")
        form_string = ''.join([r['result'] for r in results[::-1]])
        
        # Trend analizi - son 3 vs önceki 2 maç
        if len(results) >= 5:
            recent_points = sum([3 if r['result'] == 'W' else 1 if r['result'] == 'D' else 0 for r in results[:3]])
            older_points = sum([3 if r['result'] == 'W' else 1 if r['result'] == 'D' else 0 for r in results[3:5]])
            
            if recent_points > older_points + 2:
                trend = 'rising'
            elif recent_points < older_points - 2:
                trend = 'falling'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'form': form_string,
            'points': points,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_for': int(df['goals_for'].sum()),
            'goals_against': int(df['goals_against'].sum()),
            'trend': trend,
            'matches': results
        }
    
    def calculate_power_ranking(self):
        """
        Güç sıralaması - tüm takımların güncel güç seviyesi
        ELO benzeri sistem
        """
        conn = sqlite3.connect(self.db_path)
        
        # Tüm takımları al
        teams_df = pd.read_sql_query('SELECT id, name FROM teams', conn)
        
        power_rankings = []
        
        for _, team in teams_df.iterrows():
            team_id = team['id']
            team_name = team['name']
            
            # Son 10 maç performansı
            query = '''
                SELECT 
                    CASE 
                        WHEN m.home_team_id = ? THEN m.home_score
                        ELSE m.away_score
                    END as goals_for,
                    CASE 
                        WHEN m.home_team_id = ? THEN m.away_score
                        ELSE m.home_score
                    END as goals_against,
                    CASE 
                        WHEN m.home_team_id = ? THEN 1
                        ELSE 0
                    END as is_home
                FROM matches m
                WHERE (m.home_team_id = ? OR m.away_team_id = ?)
                AND m.is_finished = 1
                AND m.season = '2025_26'
                ORDER BY m.match_datetime DESC
                LIMIT 10
            '''
            
            matches_df = pd.read_sql_query(query, conn, params=[team_id, team_id, team_id, team_id, team_id])
            
            if matches_df.empty:
                power_score = 1000  # Başlangıç skoru
            else:
                # Güç skoru hesaplama
                points = 0
                goal_diff = 0
                
                for _, match in matches_df.iterrows():
                    gf = match['goals_for']
                    ga = match['goals_against']
                    is_home = match['is_home']
                    
                    # Puan
                    if gf > ga:
                        points += 3
                    elif gf == ga:
                        points += 1
                    
                    # Gol farkı (ev sahibi avantajı düzeltmesi)
                    if is_home:
                        goal_diff += (gf - ga) * 0.9  # Ev sahibi golü biraz daha az değerli
                    else:
                        goal_diff += (gf - ga) * 1.1  # Deplasman golü daha değerli
                
                # Güç skoru = 1000 + (puan * 10) + (gol farkı * 5)
                power_score = 1000 + (points * 10) + (goal_diff * 5)
            
            # xG ekle
            xg_stats = self.calculate_xg(team_id, is_home=True, last_n=10)
            
            # Form analizi ekle
            form = self.get_form_analysis(team_id, last_n=5)
            
            power_rankings.append({
                'team_id': team_id,
                'team': team_name,
                'power_score': round(power_score, 1),
                'xg': xg_stats['xg'],
                'form': form['form'],
                'trend': form['trend']
            })
        
        conn.close()
        
        # Sırala
        power_rankings.sort(key=lambda x: x['power_score'], reverse=True)
        
        # Sıralama ekle
        for i, ranking in enumerate(power_rankings):
            ranking['rank'] = i + 1
        
        return power_rankings
    
    def calculate_momentum(self, team_id, window=10):
        """
        Momentum göstergesi - yükseliş/düşüş trendi
        """
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT 
                m.match_datetime,
                CASE 
                    WHEN m.home_team_id = ? THEN m.home_score
                    ELSE m.away_score
                END as goals_for,
                CASE 
                    WHEN m.home_team_id = ? THEN m.away_score
                    ELSE m.home_score
                END as goals_against
            FROM matches m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.is_finished = 1
            ORDER BY m.match_datetime DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[team_id, team_id, team_id, team_id, window])
        conn.close()
        
        if len(df) < 3:
            return {
                'momentum': 0.0,
                'direction': 'stable',
                'strength': 'weak'
            }
        
        # Her maç için puan hesapla
        points = []
        for _, match in df.iterrows():
            gf = match['goals_for']
            ga = match['goals_against']
            
            if gf > ga:
                points.append(3)
            elif gf == ga:
                points.append(1)
            else:
                points.append(0)
        
        # Ters çevir (en eski maçtan en yeniye)
        points = points[::-1]
        
        # Momentum hesaplama - son maçlara daha fazla ağırlık
        weights = np.exp(np.linspace(0, 1, len(points)))
        weighted_avg = np.average(points, weights=weights)
        
        # Trend - son 3 vs önceki maçlar
        recent_avg = np.mean(points[-3:])
        older_avg = np.mean(points[:-3]) if len(points) > 3 else recent_avg
        
        momentum_score = (recent_avg - older_avg) * 10
        
        # Yön belirleme
        if momentum_score > 2:
            direction = 'rising'
            strength = 'strong' if momentum_score > 5 else 'moderate'
        elif momentum_score < -2:
            direction = 'falling'
            strength = 'strong' if momentum_score < -5 else 'moderate'
        else:
            direction = 'stable'
            strength = 'weak'
        
        return {
            'momentum': round(momentum_score, 2),
            'direction': direction,
            'strength': strength,
            'recent_form': round(recent_avg, 2),
            'older_form': round(older_avg, 2)
        }
    
    def get_comprehensive_team_stats(self, team_id):
        """
        Takım için kapsamlı istatistikler
        """
        # xG
        xg_home = self.calculate_xg(team_id, is_home=True, last_n=10)
        xg_away = self.calculate_xg(team_id, is_home=False, last_n=10)
        
        # Form
        form = self.get_form_analysis(team_id, last_n=5)
        
        # Momentum
        momentum = self.calculate_momentum(team_id, window=10)
        
        return {
            'xg_home': xg_home,
            'xg_away': xg_away,
            'form': form,
            'momentum': momentum
        }

if __name__ == '__main__':
    print("="*70)
    print("🇩🇪 BUNDESLIGA GELİŞMİŞ İSTATİSTİKLER")
    print("="*70)
    
    stats = BundesligaAdvancedStats()
    
    # Güç sıralaması
    print("\n💪 GÜÇ SIRALAMASI")
    print("="*70)
    rankings = stats.calculate_power_ranking()
    
    for rank in rankings[:10]:
        print(f"{rank['rank']:2d}. {rank['team']:30s} - Güç: {rank['power_score']:6.1f} | xG: {rank['xg']:.2f} | Form: {rank['form']} | Trend: {rank['trend']}")
    
    # Bayern detaylı analiz
    print("\n"+"="*70)
    print("📊 BAYERN MÜNCHEN - DETAYLI ANALİZ")
    print("="*70)
    
    conn = sqlite3.connect('bundesliga.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM teams WHERE name LIKE '%Bayern%'")
    bayern_id = cursor.fetchone()[0]
    conn.close()
    
    bayern_stats = stats.get_comprehensive_team_stats(bayern_id)
    
    print("\n⚽ xG (Expected Goals):")
    print(f"  Evde: {bayern_stats['xg_home']['xg']:.2f} xG/maç")
    print(f"  Deplasmanda: {bayern_stats['xg_away']['xg']:.2f} xG/maç")
    print(f"  xG Performans: {bayern_stats['xg_home']['xg_performance']:.2f}")
    
    print("\n📈 Form Analizi (Son 5 Maç):")
    print(f"  Form: {bayern_stats['form']['form']}")
    print(f"  Puan: {bayern_stats['form']['points']}/15")
    print(f"  Galibiyet: {bayern_stats['form']['wins']} | Beraberlik: {bayern_stats['form']['draws']} | Mağlubiyet: {bayern_stats['form']['losses']}")
    print(f"  Trend: {bayern_stats['form']['trend']}")
    
    print("\n🚀 Momentum:")
    print(f"  Skor: {bayern_stats['momentum']['momentum']:.2f}")
    print(f"  Yön: {bayern_stats['momentum']['direction']}")
    print(f"  Güç: {bayern_stats['momentum']['strength']}")
