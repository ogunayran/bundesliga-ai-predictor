#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bundesliga Oyuncu İstatistikleri ve Hava Durumu Modülü
"""

import requests
import sqlite3
from datetime import datetime

class BundesligaPlayerWeather:
    def __init__(self, db_path='bundesliga.db'):
        self.db_path = db_path
        self.api_base = 'https://api.openligadb.de'
        self.weather_api_key = None  # OpenWeatherMap API key (opsiyonel)
    
    def get_top_scorers(self, season=2025, limit=20):
        """
        Gol kralları listesi
        """
        try:
            url = f'{self.api_base}/getgoalgetters/bl1/{season}'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                scorers = response.json()
                
                # İlk N oyuncu
                top_scorers = []
                for scorer in scorers[:limit]:
                    top_scorers.append({
                        'name': scorer.get('goalGetterName', 'N/A'),
                        'goals': scorer.get('goalCount', 0),
                        'team': scorer.get('teamName', 'N/A'),
                        'team_icon': scorer.get('teamIconUrl', '')
                    })
                
                return top_scorers
            else:
                return []
        except Exception as e:
            print(f"Gol kralları hatası: {e}")
            return []
    
    def get_team_top_scorer(self, team_name, season=2025):
        """
        Takımın en golcü oyuncusu
        """
        scorers = self.get_top_scorers(season, limit=100)
        
        team_scorers = [s for s in scorers if team_name.lower() in s['team'].lower()]
        
        if team_scorers:
            return team_scorers[0]
        else:
            return None
    
    def get_match_weather(self, city, match_datetime):
        """
        Maç günü hava durumu tahmini
        Not: OpenWeatherMap API key gerektirir (ücretsiz)
        """
        if not self.weather_api_key:
            # API key yoksa basit tahmin
            return {
                'temperature': 15,
                'condition': 'Clear',
                'humidity': 60,
                'wind_speed': 10,
                'impact': 'neutral',
                'note': 'Weather API key not configured'
            }
        
        try:
            # OpenWeatherMap API
            url = f'http://api.openweathermap.org/data/2.5/forecast'
            params = {
                'q': f'{city},DE',
                'appid': self.weather_api_key,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Maç saatine en yakın tahmin
                forecasts = data.get('list', [])
                
                if forecasts:
                    forecast = forecasts[0]
                    
                    temp = forecast['main']['temp']
                    condition = forecast['weather'][0]['main']
                    humidity = forecast['main']['humidity']
                    wind = forecast['wind']['speed']
                    
                    # Hava durumu etkisi
                    impact = 'neutral'
                    if condition in ['Rain', 'Snow', 'Thunderstorm']:
                        impact = 'negative'
                    elif temp < 5 or temp > 30:
                        impact = 'negative'
                    elif wind > 15:
                        impact = 'negative'
                    
                    return {
                        'temperature': round(temp, 1),
                        'condition': condition,
                        'humidity': humidity,
                        'wind_speed': round(wind, 1),
                        'impact': impact
                    }
            
            return {
                'temperature': 15,
                'condition': 'Unknown',
                'humidity': 60,
                'wind_speed': 10,
                'impact': 'neutral'
            }
            
        except Exception as e:
            print(f"Hava durumu hatası: {e}")
            return {
                'temperature': 15,
                'condition': 'Unknown',
                'humidity': 60,
                'wind_speed': 10,
                'impact': 'neutral'
            }
    
    def get_weather_impact_factor(self, weather_data):
        """
        Hava durumunun maç üzerindeki etkisi (0.8 - 1.2 arası)
        """
        impact = weather_data.get('impact', 'neutral')
        
        if impact == 'negative':
            # Kötü hava - daha az gol beklenir
            return 0.85
        elif impact == 'positive':
            # İyi hava - normal
            return 1.0
        else:
            # Nötr
            return 0.95
    
    def get_comprehensive_match_context(self, home_team, away_team, match_datetime, city='Munich'):
        """
        Maç için kapsamlı bağlam bilgisi
        """
        # Gol kralları
        home_scorer = self.get_team_top_scorer(home_team)
        away_scorer = self.get_team_top_scorer(away_team)
        
        # Hava durumu
        weather = self.get_match_weather(city, match_datetime)
        weather_factor = self.get_weather_impact_factor(weather)
        
        return {
            'home_top_scorer': home_scorer,
            'away_top_scorer': away_scorer,
            'weather': weather,
            'weather_factor': weather_factor,
            'injuries': [],  # API'den sakatlık verisi yok
            'suspensions': []  # API'den ceza verisi yok
        }

if __name__ == '__main__':
    print("="*70)
    print("🏃 BUNDESLIGA OYUNCU İSTATİSTİKLERİ")
    print("="*70)
    
    pw = BundesligaPlayerWeather()
    
    # Gol kralları
    print("\n⚽ GOL KRALLARI (2025-26)")
    print("="*70)
    scorers = pw.get_top_scorers(2025, limit=10)
    
    for i, scorer in enumerate(scorers):
        print(f"{i+1:2d}. {scorer['name']:25s} ({scorer['team']:30s}) - {scorer['goals']:2d} gol")
    
    # Bayern'in golcüsü
    print("\n"+"="*70)
    print("🔴 BAYERN MÜNCHEN - EN GOLCÜ OYUNCU")
    print("="*70)
    
    bayern_scorer = pw.get_team_top_scorer('Bayern München', 2025)
    if bayern_scorer:
        print(f"Oyuncu: {bayern_scorer['name']}")
        print(f"Goller: {bayern_scorer['goals']}")
    
    # Hava durumu örneği
    print("\n"+"="*70)
    print("🌡️ HAVA DURUMU TAHMİNİ")
    print("="*70)
    
    weather = pw.get_match_weather('Munich', datetime.now())
    print(f"Sıcaklık: {weather['temperature']}°C")
    print(f"Durum: {weather['condition']}")
    print(f"Nem: {weather['humidity']}%")
    print(f"Rüzgar: {weather['wind_speed']} m/s")
    print(f"Etki: {weather['impact']}")
    print(f"Not: {weather.get('note', 'N/A')}")
