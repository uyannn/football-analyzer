"""
竞彩官网数据抓取
"""
import urllib.request
import json
import http.cookiejar
from typing import List
from datetime import datetime
from ..models import Match
from ..config import (
    SPORTTERY_API, SPORTTERY_MAIN, SPORTTERY_POOL_CODES,
    SPORTTERY_CHANNEL, REQUEST_HEADERS, REQUEST_TIMEOUT
)


class SportteryFetcher:
    """竞彩官网数据抓取器"""
    
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj)
        )
        self._init_session()
    
    def _init_session(self):
        """初始化会话，获取cookies"""
        try:
            req = urllib.request.Request(
                SPORTTERY_MAIN,
                headers=REQUEST_HEADERS
            )
            self.opener.open(req, timeout=REQUEST_TIMEOUT)
            print("[OK] 竞彩官网会话初始化成功")
        except Exception as e:
            print(f"[WARN] 竞彩官网会话初始化失败: {e}")
    
    def fetch_matches(self) -> List[Match]:
        """获取所有可购买的竞彩比赛"""
        try:
            url = f"{SPORTTERY_API}?poolCode={SPORTTERY_POOL_CODES}&channel={SPORTTERY_CHANNEL}"
            req = urllib.request.Request(url, headers={
                **REQUEST_HEADERS,
                "Referer": SPORTTERY_MAIN,
            })
            
            resp = self.opener.open(req, timeout=REQUEST_TIMEOUT)
            data = json.loads(resp.read().decode("utf-8"))
            
            if not data.get("success"):
                print(f"[ERROR] API返回错误: {data.get('errorMessage')}")
                return []
            
            matches = []
            match_list = data["value"]["matchInfoList"]
            
            for day_data in match_list:
                sub_matches = day_data.get("subMatchList", [])
                
                for m in sub_matches:
                    match = self._parse_match(m)
                    if match:
                        matches.append(match)
            
            print(f"[OK] 获取到 {len(matches)} 场比赛")
            return matches
            
        except Exception as e:
            print(f"[ERROR] 抓取竞彩数据失败: {e}")
            return []
    
    def _parse_match(self, m: dict) -> Match:
        """解析单场比赛数据"""
        try:
            # 提取赔率
            had = m.get("had", {})
            hhad = m.get("hhad", {})
            
            had_odds = {}
            if had:
                had_odds = {
                    "h": float(had.get("h", 0)),
                    "d": float(had.get("d", 0)),
                    "a": float(had.get("a", 0)),
                }
            
            hhad_odds = {}
            if hhad:
                hhad_odds = {
                    "h": float(hhad.get("h", 0)),
                    "d": float(hhad.get("d", 0)),
                    "a": float(hhad.get("a", 0)),
                    "line": hhad.get("goalLine", ""),
                }
            
            match = Match(
                match_id=str(m.get("matchId", "")),
                match_num=m.get("matchNumStr", ""),
                league=m.get("leagueAbbName", ""),
                home_team=m.get("homeTeamAbbName", ""),
                away_team=m.get("awayTeamAbbName", ""),
                home_rank=m.get("homeRank", ""),
                away_rank=m.get("awayRank", ""),
                match_date=m.get("matchDate", ""),
                match_time=m.get("matchTime", ""),
                status=m.get("matchStatus", ""),
                had_odds=had_odds,
                hhad_odds=hhad_odds,
            )
            
            return match
            
        except Exception as e:
            print(f"[WARN] 解析比赛数据失败: {e}")
            return None
    
    def filter_purchasable_matches(self, matches: List[Match]) -> List[Match]:
        """过滤出当前可购买的比赛"""
        now = datetime.now()
        purchasable = []
        
        for m in matches:
            # 只保留Selling状态
            if m.status != "Selling":
                continue
            
            # 检查比赛时间
            try:
                match_dt = datetime.strptime(
                    f"{m.match_date} {m.match_time}",
                    "%Y-%m-%d %H:%M:%S"
                )
                # 比赛开始后30分钟内仍可购买（滚球）
                if match_dt > now or (now - match_dt).total_seconds() < 1800:
                    purchasable.append(m)
            except:
                purchasable.append(m)  # 解析失败则保留
        
        print(f"[OK] 过滤后剩余 {len(purchasable)} 场可购买比赛")
        return purchasable
