"""
数据模型定义
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Match:
    """比赛信息"""
    match_id: str
    match_num: str  # 如: 周六103
    league: str  # 如: 世界杯, 挪超
    home_team: str
    away_team: str
    home_rank: str  # 如: [世界杯1]
    away_rank: str
    match_date: str  # YYYY-MM-DD
    match_time: str  # HH:MM:SS
    status: str  # Selling, Closed, etc.
    
    # 赔率数据
    had_odds: Dict[str, float] = field(default_factory=dict)  # 胜平负: {h, d, a}
    hhad_odds: Dict[str, float] = field(default_factory=dict)  # 让球胜平负: {h, d, a, line}
    
    # 分析数据
    analysis_score: float = 0.0  # 综合评分
    confidence: float = 0.0  # 置信度
    recommendation: str = ""  # 推荐选项
    analysis_details: Dict = field(default_factory=dict)  # 详细分析


@dataclass
class TeamStats:
    """球队统计"""
    team_name: str
    league: str
    rank: int
    recent_form: List[str] = field(default_factory=list)  # 近5场: ['W', 'D', 'L']
    goals_scored: int = 0
    goals_conceded: int = 0
    home_record: Dict = field(default_factory=dict)  # {wins, draws, losses, gf, ga}
    away_record: Dict = field(default_factory=dict)
    injuries: List[str] = field(default_factory=list)
    suspensions: List[str] = field(default_factory=list)


@dataclass
class H2HRecord:
    """历史交锋记录"""
    home_team: str
    away_team: str
    total_matches: int = 0
    home_wins: int = 0
    draws: int = 0
    away_wins: int = 0
    recent_results: List[Dict] = field(default_factory=list)  # [{date, score, winner}]


@dataclass
class WeatherInfo:
    """天气信息"""
    city: str
    temperature: float  # 摄氏度
    wind_speed: float  # km/h
    precipitation: float  # mm
    condition: str  # 天气状况
    impact: str = ""  # 对比赛的影响评估


@dataclass
class TicketLeg:
    """彩票腿（单场比赛选择）"""
    match: Match
    pick: str  # 选择: 'h', 'd', 'a'
    pick_desc: str  # 描述: '主胜', '平局', '客胜'
    odds: float
    odds_type: str  # 'had' or 'hhad'
    confidence: float = 0.0


@dataclass
class Ticket:
    """彩票"""
    ticket_id: int
    name: str  # 保本票, 中赔票, 高倍票
    risk_level: str  # 低风险, 中风险, 高风险
    legs: List[TicketLeg] = field(default_factory=list)
    investment: float = 0.0  # 投入金额
    total_odds: float = 1.0  # 组合赔率
    expected_return: float = 0.0  # 预期回报
    strategy_desc: str = ""  # 策略描述


@dataclass
class BettingStrategy:
    """投注策略"""
    total_budget: float = 100.0
    tickets: List[Ticket] = field(default_factory=list)
    best_case_return: float = 0.0
    safe_case_return: float = 0.0
    worst_case_return: float = 0.0


@dataclass
class AnalysisReport:
    """分析报告"""
    report_date: str
    matches: List[Match] = field(default_factory=list)
    strategy: BettingStrategy = field(default_factory=lambda: BettingStrategy())
    scenarios: List[Dict] = field(default_factory=list)  # 情景分析
    notes: List[str] = field(default_factory=list)  # 重要提示
