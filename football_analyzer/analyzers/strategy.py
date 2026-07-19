"""
投注策略生成器 - 三票策略
"""
from typing import List
from ..models import Match, Ticket, TicketLeg, BettingStrategy


def log(msg):
    print(msg, flush=True)


class StrategyGenerator:
    def __init__(self, total_budget: float = 100.0):
        self.total_budget = total_budget
        self.t1_ratio = 0.60
        self.t2_ratio = 0.30
        self.t3_ratio = 0.10
    
    def generate_strategy(self, matches):
        if not matches:
            log("[WARN] 没有可分析的比赛")
            return BettingStrategy(total_budget=self.total_budget)
        
        valid = [m for m in matches if m.recommendation and m.had_odds]
        valid.sort(key=lambda m: m.confidence, reverse=True)
        
        if not valid:
            log("[WARN] 没有有效的分析比赛")
            return BettingStrategy(total_budget=self.total_budget)
        
        count = len(valid)
        log(f"[INFO] 有效比赛: {count}场")
        
        t1 = self._ticket1(valid, self.total_budget * self.t1_ratio)
        t2 = self._ticket2(valid, self.total_budget * self.t2_ratio)
        
        used = {leg.match.match_id for t in [t1, t2] for leg in t.legs}
        t3 = self._ticket3(valid, self.total_budget * self.t3_ratio, used)
        
        strategy = BettingStrategy(total_budget=self.total_budget, tickets=[t1, t2, t3])
        returns = [t.expected_return for t in strategy.tickets]
        strategy.best_case_return = sum(returns)
        strategy.safe_case_return = max(returns) if returns else 0
        strategy.worst_case_return = 0
        return strategy
    
    def _ticket1(self, matches, investment):
        min_odds = self.total_budget / investment
        legs = []
        for m in sorted(matches, key=lambda m: m.confidence, reverse=True):
            if m.analysis_details.get("pick_odds", 0) < 1.3:
                continue
            leg = self._leg(m)
            if leg:
                legs.append(leg)
                if len(legs) >= 2:
                    break
        if not legs:
            for m in matches:
                leg = self._leg(m)
                if leg:
                    legs.append(leg)
                    break
        t = Ticket(ticket_id=1, name="保本回本票", risk_level="低风险", legs=legs,
                   investment=investment, strategy_desc=f"低风险保本，{len(legs)}串1，单独命中即可回本（需{min_odds:.2f}倍）")
        self._calc(t)
        return t
    
    def _ticket2(self, matches, investment):
        min_odds = self.total_budget / investment
        legs = []
        for m in sorted(matches, key=lambda m: m.confidence * m.analysis_details.get("pick_odds", 1), reverse=True):
            if m.analysis_details.get("pick_odds", 0) < 1.4:
                continue
            leg = self._leg(m)
            if leg:
                legs.append(leg)
                if len(legs) >= 3:
                    break
        if legs and self._total_odds(legs) < min_odds:
            alt = []
            for m in sorted(matches, key=lambda m: m.analysis_details.get("pick_odds", 0), reverse=True):
                if m.analysis_details.get("pick_odds", 0) >= 1.6:
                    leg = self._leg(m)
                    if leg:
                        alt.append(leg)
                        if len(alt) >= 3:
                            break
            if self._total_odds(alt) > self._total_odds(legs):
                legs = alt
        t = Ticket(ticket_id=2, name="中赔回本票", risk_level="中风险", legs=legs,
                   investment=investment, strategy_desc=f"中风险平衡，{len(legs)}串1，单独命中即可回本（需{min_odds:.2f}倍）")
        self._calc(t)
        return t
    
    def _ticket3(self, matches, investment, used):
        legs = []
        unused = sorted([m for m in matches if m.match_id not in used and m.recommendation],
                        key=lambda m: m.analysis_details.get("pick_odds", 0), reverse=True)
        for m in unused:
            if m.analysis_details.get("pick_odds", 0) >= 1.3:
                leg = self._leg(m)
                if leg:
                    legs.append(leg)
                    if len(legs) >= 5:
                        break
        if len(legs) < 3:
            for m in matches:
                if m.recommendation and m.match_id not in {l.match.match_id for l in legs}:
                    leg = self._leg(m)
                    if leg:
                        legs.append(leg)
                        if len(legs) >= 5:
                            break
        t = Ticket(ticket_id=3, name="高倍博冷票", risk_level="高风险", legs=legs,
                   investment=investment, strategy_desc=f"高风险高倍，{len(legs)}串1，低投入博高收益")
        self._calc(t)
        return t
    
    def _leg(self, match):
        if not match.recommendation:
            return None
        odds = match.analysis_details.get("pick_odds", 0)
        if odds <= 0:
            return None
        rec = match.recommendation
        pick_desc = "主胜" if "主胜" in rec else "平局" if "平局" in rec else "客胜" if "客胜" in rec else rec
        pick = "h" if "主胜" in rec else "d" if "平局" in rec else "a"
        return TicketLeg(match=match, pick=pick, pick_desc=pick_desc, odds=odds,
                         odds_type=match.analysis_details.get("pick_type", "had"), confidence=match.confidence)
    
    def _total_odds(self, legs):
        r = 1.0
        for l in legs: r *= l.odds
        return r
    
    def _calc(self, ticket):
        if not ticket.legs:
            ticket.total_odds = 1.0
            ticket.expected_return = 0.0
            return
        ticket.total_odds = round(self._total_odds(ticket.legs), 2)
        ticket.expected_return = round(ticket.investment * ticket.total_odds, 0)
        
        desc = " + ".join(f"{l.match.home_team}vs{l.match.away_team}({l.pick_desc}@{l.odds:.2f})" for l in ticket.legs)
        ok = "[OK]" if ticket.expected_return >= self.total_budget else "[FAIL]"
        log(f"  票{ticket.ticket_id}: {ticket.name} | {len(ticket.legs)}串1 | "
            f"投入{ticket.investment:.0f}元 | {ticket.total_odds:.2f}倍 | "
            f"回报{ticket.expected_return:.0f}元 | 回本{ok}")
        log(f"    选择: {desc}")
