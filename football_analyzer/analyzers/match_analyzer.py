"""
比赛多维度分析引擎
"""
from typing import Dict, List
from ..models import Match, TeamStats, H2HRecord, WeatherInfo
from ..data_fetchers.team_stats import TeamStatsFetcher
from ..data_fetchers.weather import WeatherFetcher
from ..config import ANALYSIS_WEIGHTS


class MatchAnalyzer:
    """比赛多维度分析器"""
    
    def __init__(self):
        self.team_fetcher = TeamStatsFetcher()
        self.weather_fetcher = WeatherFetcher()
    
    def analyze_match(self, match: Match) -> Match:
        """分析单场比赛，返回带分析结果的Match对象"""
        print(f"分析: {match.home_team} vs {match.away_team}...")
        
        # 获取球队数据
        home_stats = self.team_fetcher.get_team_stats(match, is_home=True)
        away_stats = self.team_fetcher.get_team_stats(match, is_home=False)
        h2h = self.team_fetcher.get_h2h_record(match)
        
        # 获取天气
        weather = self.weather_fetcher.fetch_for_league(match.league)
        
        # 多维度评分
        scores = self._calculate_scores(match, home_stats, away_stats, h2h, weather)
        
        # 综合评分
        total_score = sum(
            scores[key] * ANALYSIS_WEIGHTS[key]
            for key in ANALYSIS_WEIGHTS.keys()
        )
        
        # 确定推荐
        recommendation, confidence, pick_odds, pick_type = self._make_recommendation(
            match, scores, total_score
        )
        
        # 更新Match对象
        match.analysis_score = total_score
        match.confidence = confidence
        match.recommendation = recommendation
        match.analysis_details = {
            "scores": scores,
            "home_stats": home_stats,
            "away_stats": away_stats,
            "h2h": h2h,
            "weather": weather,
            "pick_odds": pick_odds,
            "pick_type": pick_type,
        }
        
        return match
    
    def _calculate_scores(
        self,
        match: Match,
        home_stats: TeamStats,
        away_stats: TeamStats,
        h2h: H2HRecord,
        weather: WeatherInfo
    ) -> Dict[str, float]:
        """计算各维度评分 (0-1)"""
        scores = {}
        
        # 1. 赔率隐含概率
        had = match.had_odds
        total_prob = 1/had["h"] + 1/had["d"] + 1/had["a"]
        home_prob = (1/had["h"]) / total_prob
        away_prob = (1/had["a"]) / total_prob
        
        # 赔率评分: 概率越高，该方向得分越高
        scores["odds_probability"] = max(home_prob, away_prob)
        
        # 2. 近期状态
        home_form_score = self._calculate_form_score(home_stats.recent_form)
        away_form_score = self._calculate_form_score(away_stats.recent_form)
        scores["team_form"] = max(home_form_score, away_form_score)
        
        # 3. 历史交锋
        if h2h.total_matches > 0:
            home_h2h_rate = h2h.home_wins / h2h.total_matches
            away_h2h_rate = h2h.away_wins / h2h.total_matches
            scores["h2h_record"] = max(home_h2h_rate, away_h2h_rate)
        else:
            scores["h2h_record"] = 0.5
        
        # 4. 主场优势
        home_home_record = home_stats.home_record
        away_away_record = away_stats.away_record
        home_home_rate = home_home_record["wins"] / 8 if home_home_record else 0.5
        away_away_rate = away_away_record["wins"] / 8 if away_away_record else 0.5
        scores["home_advantage"] = max(home_home_rate, away_away_rate)
        
        # 5. 排名实力
        rank_diff = away_stats.rank - home_stats.rank
        if rank_diff > 0:
            scores["rank_strength"] = min(0.5 + rank_diff * 0.05, 0.9)
        else:
            scores["rank_strength"] = max(0.5 + rank_diff * 0.05, 0.1)
        
        # 6. 天气影响
        if weather and weather.precipitation > 5:
            # 恶劣天气利好防守方（弱队）
            scores["weather_impact"] = 0.6 if away_stats.rank > home_stats.rank else 0.4
        else:
            scores["weather_impact"] = 0.5
        
        # 7. 赛程疲劳 (简化处理)
        scores["schedule_fatigue"] = 0.5
        
        # 8. 比赛动机
        # 排名靠后的球队保级动机强，排名靠前的争冠动机强
        if home_stats.rank <= 3 or home_stats.rank >= home_stats.rank * 0.8:
            scores["motivation"] = 0.7
        else:
            scores["motivation"] = 0.5
        
        return scores
    
    def _calculate_form_score(self, form: List[str]) -> float:
        """计算近期状态得分"""
        if not form:
            return 0.5
        
        score = 0
        weights = [1.5, 1.2, 1.0, 0.8, 0.5]  # 最近的比赛权重更高
        
        for i, result in enumerate(form[:5]):
            if result == "W":
                score += weights[i]
            elif result == "D":
                score += weights[i] * 0.5
        
        max_score = sum(weights[:len(form)])
        return score / max_score if max_score > 0 else 0.5
    
    def _make_recommendation(
        self, match: Match, scores: Dict, total_score: float
    ) -> tuple:
        """生成推荐选项"""
        had = match.had_odds
        hhad = match.hhad_odds
        
        # 计算各选项的期望值
        options = [
            ("主胜", had["h"], "had"),
            ("平局", had["d"], "had"),
            ("客胜", had["a"], "had"),
        ]
        
        if hhad:
            options.extend([
                ("让球主胜", hhad["h"], "hhad"),
                ("让球平局", hhad["d"], "hhad"),
                ("让球客胜", hhad["a"], "hhad"),
            ])
        
        # 根据分析评分选择最优选项
        # 简化逻辑: 选择赔率隐含概率最高且与分析方向一致的选项
        best_option = None
        best_ev = 0
        
        for desc, odds, otype in options:
            # 期望值 = 赔率 * 置信度
            implied_prob = 1.0 / odds if odds > 0 else 0
            ev = implied_prob * total_score
            
            if ev > best_ev:
                best_ev = ev
                best_option = (desc, odds, otype)
        
        if not best_option:
            return "无推荐", 0.0, 0.0, "had"
        
        rec_desc, rec_odds, rec_type = best_option
        confidence = min(best_ev * 2, 0.95)  # 转换为置信度
        
        return rec_desc, confidence, rec_odds, rec_type
    
    def analyze_all_matches(self, matches: List[Match]) -> List[Match]:
        """分析所有比赛"""
        analyzed = []
        for match in matches:
            try:
                analyzed_match = self.analyze_match(match)
                analyzed.append(analyzed_match)
            except Exception as e:
                print(f"[ERROR] 分析 {match.home_team} vs {match.away_team} 失败: {e}")
                analyzed.append(match)
        
        # 按综合评分排序
        analyzed.sort(key=lambda m: m.analysis_score, reverse=True)
        
        return analyzed
