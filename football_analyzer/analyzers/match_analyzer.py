"""
比赛多维度分析引擎
"""
from typing import Dict, List
from ..models import Match, TeamStats, H2HRecord, WeatherInfo
from ..data_fetchers.team_stats import TeamStatsFetcher
from ..data_fetchers.weather import WeatherFetcher
from ..config import ANALYSIS_WEIGHTS


def log(msg):
    print(msg, flush=True)


class MatchAnalyzer:
    def __init__(self):
        self.team_fetcher = TeamStatsFetcher()
        self.weather_fetcher = WeatherFetcher()
    
    def analyze_match(self, match: Match) -> Match:
        log(f"分析: {match.home_team} vs {match.away_team}...")
        
        home_stats = self.team_fetcher.get_team_stats(match, is_home=True)
        away_stats = self.team_fetcher.get_team_stats(match, is_home=False)
        h2h = self.team_fetcher.get_h2h_record(match)
        weather = self.weather_fetcher.fetch_for_league(match.league)
        
        scores = self._calculate_scores(match, home_stats, away_stats, h2h, weather)
        total_score = sum(scores[k] * ANALYSIS_WEIGHTS[k] for k in ANALYSIS_WEIGHTS)
        recommendation, confidence, pick_odds, pick_type = self._make_recommendation(match, scores, total_score)
        
        match.analysis_score = total_score
        match.confidence = confidence
        match.recommendation = recommendation
        match.analysis_details = {
            "scores": scores, "home_stats": home_stats,
            "away_stats": away_stats, "h2h": h2h, "weather": weather,
            "pick_odds": pick_odds, "pick_type": pick_type,
        }
        return match
    
    def _calculate_scores(self, match, home_stats, away_stats, h2h, weather):
        scores = {}
        had = match.had_odds
        total_prob = 1/had["h"] + 1/had["d"] + 1/had["a"]
        home_prob = (1/had["h"]) / total_prob
        away_prob = (1/had["a"]) / total_prob
        scores["odds_probability"] = max(home_prob, away_prob)
        
        home_form = self._form_score(home_stats.recent_form)
        away_form = self._form_score(away_stats.recent_form)
        scores["team_form"] = max(home_form, away_form)
        
        if h2h.total_matches > 0:
            scores["h2h_record"] = max(h2h.home_wins, h2h.away_wins) / h2h.total_matches
        else:
            scores["h2h_record"] = 0.5
        
        hr = home_stats.home_record
        ar = away_stats.away_record
        scores["home_advantage"] = max(hr["wins"]/8 if hr else 0.5, ar["wins"]/8 if ar else 0.5)
        
        rank_diff = away_stats.rank - home_stats.rank
        scores["rank_strength"] = min(max(0.5 + rank_diff * 0.05, 0.1), 0.9)
        
        if weather and weather.precipitation > 5:
            scores["weather_impact"] = 0.6 if away_stats.rank > home_stats.rank else 0.4
        else:
            scores["weather_impact"] = 0.5
        
        scores["schedule_fatigue"] = 0.5
        scores["motivation"] = 0.7 if home_stats.rank <= 3 or home_stats.rank >= home_stats.rank * 0.8 else 0.5
        return scores
    
    def _form_score(self, form):
        if not form: return 0.5
        weights = [1.5, 1.2, 1.0, 0.8, 0.5]
        score = sum(weights[i] * (1 if r == "W" else 0.5 if r == "D" else 0) for i, r in enumerate(form[:5]))
        max_s = sum(weights[:len(form)])
        return score / max_s if max_s > 0 else 0.5
    
    def _make_recommendation(self, match, scores, total_score):
        had = match.had_odds
        hhad = match.hhad_odds
        options = [("主胜", had["h"], "had"), ("平局", had["d"], "had"), ("客胜", had["a"], "had")]
        if hhad:
            options.extend([("让球主胜", hhad["h"], "hhad"), ("让球平局", hhad["d"], "hhad"), ("让球客胜", hhad["a"], "hhad")])
        
        best = None
        best_ev = 0
        for desc, odds, otype in options:
            ev = (1.0 / odds if odds > 0 else 0) * total_score
            if ev > best_ev:
                best_ev = ev
                best = (desc, odds, otype)
        
        if not best:
            return "无推荐", 0.0, 0.0, "had"
        return best[0], min(best_ev * 2, 0.95), best[1], best[2]
    
    def analyze_all_matches(self, matches):
        analyzed = []
        for match in matches:
            try:
                analyzed.append(self.analyze_match(match))
            except Exception as e:
                log(f"[ERROR] 分析 {match.home_team} vs {match.away_team} 失败: {e}")
                analyzed.append(match)
        analyzed.sort(key=lambda m: m.analysis_score, reverse=True)
        return analyzed
