"""
配置文件
"""

# 竞彩官网API
SPORTTERY_API = "https://webapi.sporttery.cn/gateway/jc/football/getMatchCalculatorV1.qry"
SPORTTERY_MAIN = "https://www.sporttery.cn/"
SPORTTERY_POOL_CODES = "had,hhad"
SPORTTERY_CHANNEL = "c923-jc-jsfb"

# 天气API (Open-Meteo, 免费无需API Key)
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"

# 联赛城市映射 (用于天气查询)
LEAGUE_CITIES = {
    "挪超": ["Oslo", "Bergen", "Stavanger", "Trondheim", "Molde"],
    "芬超": ["Helsinki", "Tampere", "Turku", "Oulu"],
    "瑞超": ["Stockholm", "Gothenburg", "Malmo", "Uppsala"],
    "韩职": ["Seoul", "Busan", "Incheon"],
    "世界杯": [],
}

# 联赛稳定性系数 (0-1, 越高越稳定可预测)
# 基于各联赛历史爆冷率、球队实力差距、主场优势等因素
LEAGUE_STABILITY = {
    "世界杯": 0.85,  # 大赛强队发挥稳定，但淘汰赛有不确定性
    "欧冠": 0.82,
    "欧联": 0.75,
    "英超": 0.78,
    "德甲": 0.80,
    "西甲": 0.80,
    "意甲": 0.78,
    "法甲": 0.76,
    "挪超": 0.72,  # 主场优势明显，强弱较分明
    "芬超": 0.78,  # 头部球队碾压明显，可预测性高
    "瑞超": 0.70,  # 竞争较激烈
    "韩职": 0.55,  # 实力差距小，容易爆冷
    "日职": 0.58,  # 类似韩职，爆冷率偏高
    "澳超": 0.52,  # 非常不稳定
    "美职": 0.50,  # 非常不稳定
    "中超": 0.55,
    "世预赛": 0.72,
}
# 未列入的联赛默认值
DEFAULT_LEAGUE_STABILITY = 0.60

# 分析权重配置
ANALYSIS_WEIGHTS = {
    "odds_probability": 0.25,
    "team_form": 0.20,
    "h2h_record": 0.15,
    "home_advantage": 0.10,
    "rank_strength": 0.10,
    "weather_impact": 0.05,
    "schedule_fatigue": 0.05,
    "motivation": 0.10,
}

# 投注策略配置
BETTING_CONFIG = {
    "total_budget": 100.0,
    "ticket1_ratio": 0.60,
    "ticket2_ratio": 0.30,
    "ticket3_ratio": 0.10,
    "ticket1_max_legs": 2,
    "ticket2_max_legs": 3,
    "ticket3_max_legs": 5,
    "ticket1_min_confidence": 0.75,
    "ticket2_min_confidence": 0.60,
    "ticket3_min_confidence": 0.45,
}

# 请求配置
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
