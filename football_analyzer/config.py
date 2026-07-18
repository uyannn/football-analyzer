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
    "世界杯": [],  # 世界杯城市不固定
}

# 分析权重配置
ANALYSIS_WEIGHTS = {
    "odds_probability": 0.25,      # 赔率隐含概率
    "team_form": 0.20,             # 近期状态
    "h2h_record": 0.15,            # 历史交锋
    "home_advantage": 0.10,        # 主场优势
    "rank_strength": 0.10,         # 排名实力
    "weather_impact": 0.05,        # 天气影响
    "schedule_fatigue": 0.05,      # 赛程疲劳
    "motivation": 0.10,            # 比赛动机
}

# 投注策略配置
BETTING_CONFIG = {
    "total_budget": 100.0,
    "ticket1_ratio": 0.50,   # 保本票占比
    "ticket2_ratio": 0.40,   # 中赔票占比
    "ticket3_ratio": 0.10,   # 高倍票占比
    
    "ticket1_max_legs": 2,   # 保本票最多串几场
    "ticket2_max_legs": 3,   # 中赔票最多串几场
    "ticket3_max_legs": 5,   # 高倍票最多串几场
    
    "ticket1_min_confidence": 0.75,  # 保本票最低置信度
    "ticket2_min_confidence": 0.60,  # 中赔票最低置信度
    "ticket3_min_confidence": 0.45,  # 高倍票最低置信度
}

# 请求配置
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}
