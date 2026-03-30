#!/usr/bin/env python3
"""
Bundesliga Advanced Analyzer
2025-26 sezonunun tüm maçlarını, gollerini, takımları ve formları analiz eden AI sistemi
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import json

class BundesligaAnalyzer:
    def __init__(self, db_path='/Users/ogunayran/CascadeProjects/windsurf-project-6/bundesliga.db'):
        self.db_path = db_path
        self.season = '2025_26'
    
    def get_all_matches(self):
        """Tüm tamamlanmış maçları al"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.match_id, m.matchday, m.match_datetime,
                   ht.name as home_team, at.name as away_team,
                   m.home_score, m.away_score,
                   m.home_team_id, m.away_team_id
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE m.is_finished = 1
            ORDER BY m.match_datetime
        '''
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def analyze_team_form(self, team_id, last_n=5):
        """Takımın son N maçtaki formunu detaylı analiz et"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.match_datetime, m.home_team_id, m.away_team_id,
                   m.home_score, m.away_score,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.is_finished = 1
            ORDER BY m.match_datetime DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[team_id, team_id, last_n])
        conn.close()
        
        if df.empty:
            return None
        
        results = []
        points = 0
        wins = 0
        draws = 0
        losses = 0
        goals_scored = 0
        goals_conceded = 0
        clean_sheets = 0
        
        for _, match in df.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if is_home:
                scored = match['home_score']
                conceded = match['away_score']
                opponent = match['away_team']
            else:
                scored = match['away_score']
                conceded = match['home_score']
                opponent = match['home_team']
            
            goals_scored += scored
            goals_conceded += conceded
            
            if conceded == 0:
                clean_sheets += 1
            
            if scored > conceded:
                result = 'W'
                points += 3
                wins += 1
            elif scored == conceded:
                result = 'D'
                points += 1
                draws += 1
            else:
                result = 'L'
                losses += 1
            
            results.append({
                'opponent': opponent,
                'result': result,
                'score': f"{scored}-{conceded}",
                'home': is_home
            })
        
        return {
            'last_matches': results,
            'points': points,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'goals_scored': goals_scored,
            'goals_conceded': goals_conceded,
            'goal_difference': goals_scored - goals_conceded,
            'clean_sheets': clean_sheets,
            'avg_goals_scored': goals_scored / len(df),
            'avg_goals_conceded': goals_conceded / len(df),
            'win_rate': wins / len(df),
            'form_string': ''.join([r['result'] for r in results])
        }
    
    def analyze_goal_patterns(self, team_id):
        """Gol atma ve yeme paternlerini analiz et"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.home_team_id, m.away_team_id,
                   m.home_score, m.away_score, m.matchday
            FROM matches m
            WHERE (m.home_team_id = ? OR m.away_team_id = ?)
            AND m.is_finished = 1
            ORDER BY m.matchday
        '''
        
        df = pd.read_sql_query(query, conn, params=[team_id, team_id])
        conn.close()
        
        if df.empty:
            return None
        
        goals_by_half = {'first_half': 0, 'second_half': 0}  # Basitleştirilmiş
        high_scoring = 0  # 3+ gol
        low_scoring = 0   # 0-1 gol
        both_scored = 0   # Her iki takım gol attı
        
        for _, match in df.iterrows():
            is_home = match['home_team_id'] == team_id
            
            if is_home:
                scored = match['home_score']
                conceded = match['away_score']
            else:
                scored = match['away_score']
                conceded = match['home_score']
            
            total_goals = scored + conceded
            
            if total_goals >= 3:
                high_scoring += 1
            elif total_goals <= 1:
                low_scoring += 1
            
            if scored > 0 and conceded > 0:
                both_scored += 1
        
        total_matches = len(df)
        
        return {
            'high_scoring_rate': high_scoring / total_matches,
            'low_scoring_rate': low_scoring / total_matches,
            'both_teams_score_rate': both_scored / total_matches,
            'avg_total_goals': df.apply(lambda x: x['home_score'] + x['away_score'], axis=1).mean()
        }
    
    def analyze_head_to_head(self, team1_id, team2_id, last_n=5):
        """İki takım arasındaki son karşılaşmaları analiz et"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT m.match_datetime, m.home_team_id, m.away_team_id,
                   m.home_score, m.away_score,
                   ht.name as home_team, at.name as away_team
            FROM matches m
            JOIN teams ht ON m.home_team_id = ht.id
            JOIN teams at ON m.away_team_id = at.id
            WHERE ((m.home_team_id = ? AND m.away_team_id = ?) OR
                   (m.home_team_id = ? AND m.away_team_id = ?))
            AND m.is_finished = 1
            ORDER BY m.match_datetime DESC
            LIMIT ?
        '''
        
        df = pd.read_sql_query(query, conn, params=[team1_id, team2_id, team2_id, team1_id, last_n])
        conn.close()
        
        if df.empty:
            return None
        
        team1_wins = 0
        team2_wins = 0
        draws = 0
        total_goals = 0
        
        matches = []
        
        for _, match in df.iterrows():
            total_goals += match['home_score'] + match['away_score']
            
            if match['home_team_id'] == team1_id:
                team1_score = match['home_score']
                team2_score = match['away_score']
            else:
                team1_score = match['away_score']
                team2_score = match['home_score']
            
            if team1_score > team2_score:
                team1_wins += 1
                result = 'team1_win'
            elif team2_score > team1_score:
                team2_wins += 1
                result = 'team2_win'
            else:
                draws += 1
                result = 'draw'
            
            matches.append({
                'date': str(match['match_datetime']),
                'home': match['home_team'],
                'away': match['away_team'],
                'score': f"{match['home_score']}-{match['away_score']}",
                'result': result
            })
        
        return {
            'matches_played': len(df),
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws,
            'avg_goals': total_goals / len(df),
            'recent_matches': matches
        }
    
    def get_team_statistics(self, team_id):
        """Takımın sezon geneli istatistiklerini al"""
        conn = sqlite3.connect(self.db_path)
        
        # Puan durumundan al
        query = '''
            SELECT t.name, s.played, s.won, s.drawn, s.lost,
                   s.goals_for, s.goals_against, s.goal_difference, s.points
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            WHERE s.team_id = ? AND s.season = ?
        '''
        
        cursor = conn.cursor()
        cursor.execute(query, (team_id, self.season))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        # Ev ve deplasman performansı
        home_query = '''
            SELECT COUNT(*) as matches,
                   SUM(CASE WHEN home_score > away_score THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN home_score = away_score THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN home_score < away_score THEN 1 ELSE 0 END) as losses,
                   SUM(home_score) as goals_for,
                   SUM(away_score) as goals_against
            FROM matches
            WHERE home_team_id = ? AND is_finished = 1
        '''
        
        away_query = '''
            SELECT COUNT(*) as matches,
                   SUM(CASE WHEN away_score > home_score THEN 1 ELSE 0 END) as wins,
                   SUM(CASE WHEN away_score = home_score THEN 1 ELSE 0 END) as draws,
                   SUM(CASE WHEN away_score < home_score THEN 1 ELSE 0 END) as losses,
                   SUM(away_score) as goals_for,
                   SUM(home_score) as goals_against
            FROM matches
            WHERE away_team_id = ? AND is_finished = 1
        '''
        
        cursor.execute(home_query, (team_id,))
        home_stats = cursor.fetchone()
        
        cursor.execute(away_query, (team_id,))
        away_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'name': row[0],
            'overall': {
                'played': row[1],
                'won': row[2],
                'drawn': row[3],
                'lost': row[4],
                'goals_for': row[5],
                'goals_against': row[6],
                'goal_difference': row[7],
                'points': row[8]
            },
            'home': {
                'played': home_stats[0] or 0,
                'won': home_stats[1] or 0,
                'drawn': home_stats[2] or 0,
                'lost': home_stats[3] or 0,
                'goals_for': home_stats[4] or 0,
                'goals_against': home_stats[5] or 0
            },
            'away': {
                'played': away_stats[0] or 0,
                'won': away_stats[1] or 0,
                'drawn': away_stats[2] or 0,
                'lost': away_stats[3] or 0,
                'goals_for': away_stats[4] or 0,
                'goals_against': away_stats[5] or 0
            }
        }
    
    def comprehensive_match_analysis(self, home_team_id, away_team_id):
        """Maç için kapsamlı analiz"""
        
        # Takım bilgileri
        home_stats = self.get_team_statistics(home_team_id)
        away_stats = self.get_team_statistics(away_team_id)
        
        if not home_stats or not away_stats:
            return None
        
        # Form analizi
        home_form = self.analyze_team_form(home_team_id, 5)
        away_form = self.analyze_team_form(away_team_id, 5)
        
        # Gol paternleri
        home_goals = self.analyze_goal_patterns(home_team_id)
        away_goals = self.analyze_goal_patterns(away_team_id)
        
        # Kafa kafaya
        h2h = self.analyze_head_to_head(home_team_id, away_team_id, 5)
        
        # AI Tahmini
        from bundesliga_predictor import BundesligaPredictor
        predictor = BundesligaPredictor(self.db_path)
        try:
            predictor.load_model('bundesliga_model.pkl')
            prediction = predictor.predict_match(home_team_id, away_team_id)
        except:
            prediction = None
        
        # Analiz özeti oluştur
        analysis = {
            'match_info': {
                'home_team': home_stats['name'],
                'away_team': away_stats['name']
            },
            'team_statistics': {
                'home': home_stats,
                'away': away_stats
            },
            'current_form': {
                'home': home_form,
                'away': away_form
            },
            'goal_patterns': {
                'home': home_goals,
                'away': away_goals
            },
            'head_to_head': h2h,
            'ai_prediction': prediction,
            'key_insights': self._generate_insights(
                home_stats, away_stats, home_form, away_form, h2h
            )
        }
        
        return analysis
    
    def _generate_insights(self, home_stats, away_stats, home_form, away_form, h2h):
        """Anahtar içgörüler oluştur"""
        insights = []
        
        # Form karşılaştırması
        if home_form and away_form:
            if home_form['points'] > away_form['points']:
                insights.append(f"{home_stats['name']} son 5 maçta daha iyi form gösteriyor ({home_form['form_string']} vs {away_form['form_string']})")
            elif away_form['points'] > home_form['points']:
                insights.append(f"{away_stats['name']} son 5 maçta daha iyi form gösteriyor ({away_form['form_string']} vs {home_form['form_string']})")
        
        # Ev sahibi avantajı
        home_win_rate = home_stats['home']['won'] / max(home_stats['home']['played'], 1)
        if home_win_rate > 0.6:
            insights.append(f"{home_stats['name']} evinde çok güçlü (%{home_win_rate*100:.0f} galibiyet oranı)")
        
        # Deplasman performansı
        away_win_rate = away_stats['away']['won'] / max(away_stats['away']['played'], 1)
        if away_win_rate > 0.5:
            insights.append(f"{away_stats['name']} deplasmanda başarılı (%{away_win_rate*100:.0f} galibiyet oranı)")
        
        # Gol ortalamaları
        if home_form:
            if home_form['avg_goals_scored'] > 2:
                insights.append(f"{home_stats['name']} son maçlarda çok gol atıyor (ort. {home_form['avg_goals_scored']:.1f})")
            if home_form['clean_sheets'] >= 3:
                insights.append(f"{home_stats['name']} savunmada sağlam ({home_form['clean_sheets']} temiz sayfa)")
        
        # Kafa kafaya
        if h2h and h2h['matches_played'] >= 3:
            if h2h['team1_wins'] > h2h['team2_wins']:
                insights.append(f"{home_stats['name']} son karşılaşmalarda üstün ({h2h['team1_wins']}-{h2h['team2_wins']})")
            elif h2h['team2_wins'] > h2h['team1_wins']:
                insights.append(f"{away_stats['name']} son karşılaşmalarda üstün ({h2h['team2_wins']}-{h2h['team1_wins']})")
        
        return insights
    
    def get_league_insights(self):
        """Lig geneli içgörüler"""
        conn = sqlite3.connect(self.db_path)
        
        # En çok gol atan takımlar
        query = '''
            SELECT t.name, s.goals_for, s.played
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            WHERE s.season = ?
            ORDER BY s.goals_for DESC
            LIMIT 5
        '''
        
        top_scorers = pd.read_sql_query(query, conn, params=[self.season])
        
        # En az gol yiyen takımlar
        query = '''
            SELECT t.name, s.goals_against, s.played
            FROM standings s
            JOIN teams t ON s.team_id = t.id
            WHERE s.season = ?
            ORDER BY s.goals_against ASC
            LIMIT 5
        '''
        
        best_defense = pd.read_sql_query(query, conn, params=[self.season])
        
        # En iyi form (son 5 maç)
        # Bu daha karmaşık, basitleştirilmiş versiyon
        
        conn.close()
        
        return {
            'top_scorers': top_scorers.to_dict('records'),
            'best_defense': best_defense.to_dict('records')
        }

if __name__ == '__main__':
    print("="*70)
    print("🇩🇪 BUNDESLIGA ADVANCED ANALYZER - TEST")
    print("="*70)
    
    analyzer = BundesligaAnalyzer()
    
    # Örnek analiz - Bayern vs Dortmund
    conn = sqlite3.connect(analyzer.db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name FROM teams WHERE name LIKE '%Bayern%'")
    bayern = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM teams WHERE name LIKE '%Dortmund%'")
    dortmund = cursor.fetchone()
    
    conn.close()
    
    if bayern and dortmund:
        print(f"\n📊 Analiz: {bayern[1]} vs {dortmund[1]}")
        print("-" * 70)
        
        analysis = analyzer.comprehensive_match_analysis(bayern[0], dortmund[0])
        
        if analysis:
            print(f"\n✅ Kapsamlı analiz tamamlandı!")
            print(f"\nAnahtar İçgörüler:")
            for insight in analysis['key_insights']:
                print(f"  • {insight}")
            
            if analysis['ai_prediction']:
                pred = analysis['ai_prediction']
                print(f"\n🤖 AI Tahmini: {pred['prediction']}")
                print(f"   Güven: {pred['confidence']*100:.1f}%")
