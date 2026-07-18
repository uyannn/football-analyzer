"""
投注策略生成器 - 三票策略
核心逻辑: 第一注或第二注单独中即可回本，第三注多串1博高倍
"""
from typing import List
from ..models import Match, Ticket, TicketLeg, BettingStrategy


class StrategyGenerator:
    """三票策略生成器"""
    
    def __init__(self, total_budget: float = 100.0):
        self.total_budget = total_budget
        self.t1_ratio = 0.60
        self.t2_ratio = 0.30
        self.t3_ratio = 0.10
    
    def generate_strategy(self, matches: List[Match]) -> BettingStrategy:
        """生成三票投注策略"""
        if not matches:
            print("[WARN] 没有可分析的比赛")
            return BettingStrategy(total_budget=self.total_budget)
        
        valid_matches = [m for m in matches if m.recommendation and m.had_odds]
        valid_matches.sort(key=lambda m: m.confidence, reverse=True)
        
        if not valid_matches:
            print("[WARN] 没有有效的分析比赛")
            return BettingStrategy(total_budget=self.total_budget)
        
        print(f"[INFO] 有效比赛: {len(valid_matches)}场")
        
        t1_invest = self.total_budget * self.t1_ratio
        t2_invest = self.total_budget * self.t2_ratio
        t3_invest = self.total_budget * self.t3_ratio
        
        ticket1 = self._generate_ticket1(valid_matches, t1_invest)
        ticket2 = self._generate_ticket2(valid_matches, t2_invest)
        
        # 收集第一二注已用的比赛，第三注尽量避开
        used_matches = set()
        for t in [ticket1, ticket2]:
            for leg in t.legs:
                used_matches.add(leg.match.match_id)
        
        ticket3 = self._generate_ticket3(valid_matches, t3_invest, used_matches)
        
        strategy = BettingStrategy(
            total_budget=self.total_budget,
            tickets=[ticket1, ticket2, ticket3],
        )
        
        returns = [t.expected_return for t in strategy.tickets]
        strategy.best_case_return = sum(returns)
        strategy.safe_case_return = max(returns) if returns else 0
        strategy.worst_case_return = 0
        
        return strategy
    
    def _generate_ticket1(self, matches: List[Match], investment: float) -> Ticket:
        """
        第一注: 保本回本票
        投入60%, 回报需 >= 总投资 (赔率 >= 1.67x)
        选择置信度最高的2串1
        """
        min_odds_needed = self.total_budget / investment
        max_legs = 2
        legs = []
        
        candidates = sorted(matches, key=lambda m: m.confidence, reverse=True)
        
        for m in candidates:
            pick_odds = m.analysis_details.get("pick_odds", 0)
            if pick_odds < 1.3:
                continue
            
            leg = self._create_leg(m)
            if leg:
                legs.append(leg)
                if len(legs) >= max_legs:
                    break
        
        if not legs:
            for m in candidates:
                leg = self._create_leg(m)
                if leg:
                    legs.append(leg)
                    break
        
        ticket = Ticket(
            ticket_id=1,
            name="保本回本票",
            risk_level="低风险",
            legs=legs,
            investment=investment,
            strategy_desc=f"低风险保本，{len(legs)}串1，单独命中即可回本（需{min_odds_needed:.2f}倍）",
        )
        self._calculate_ticket(ticket)
        return ticket
    
    def _generate_ticket2(self, matches: List[Match], investment: float) -> Ticket:
        """
        第二注: 中赔回本票
        投入30%, 回报需 >= 总投资 (赔率 >= 3.33x)
        选择中等赔率的3串1
        """
        min_odds_needed = self.total_budget / investment
        max_legs = 3
        legs = []
        
        # 按 "置信度 * 赔率" 综合评分排序，平衡可靠性和回报
        candidates = sorted(
            matches,
            key=lambda m: m.confidence * m.analysis_details.get("pick_odds", 1),
            reverse=True
        )
        
        for m in candidates:
            pick_odds = m.analysis_details.get("pick_odds", 0)
            if pick_odds < 1.4:
                continue
            
            leg = self._create_leg(m)
            if leg:
                legs.append(leg)
                if len(legs) >= max_legs:
                    break
        
        # 如果3串不够回本，减少场次但选更高赔率
        if legs and self._ticket_total_odds(legs) < min_odds_needed:
            legs_alt = []
            high_odds = sorted(
                matches,
                key=lambda m: m.analysis_details.get("pick_odds", 0),
                reverse=True
            )
            for m in high_odds:
                pick_odds = m.analysis_details.get("pick_odds", 0)
                if pick_odds >= 1.6:
                    leg = self._create_leg(m)
                    if leg:
                        legs_alt.append(leg)
                        if len(legs_alt) >= max_legs:
                            break
            if self._ticket_total_odds(legs_alt) > self._ticket_total_odds(legs):
                legs = legs_alt
        
        ticket = Ticket(
            ticket_id=2,
            name="中赔回本票",
            risk_level="中风险",
            legs=legs,
            investment=investment,
            strategy_desc=f"中风险平衡，{len(legs)}串1，单独命中即可回本（需{min_odds_needed:.2f}倍）",
        )
        self._calculate_ticket(ticket)
        return ticket
    
    def _generate_ticket3(self, matches: List[Match], investment: float, used_matches: set) -> Ticket:
        """
        第三注: 高倍博冷票
        投入10%, 多串1拉高倍数
        优先选未在票1/票2中出现的比赛，选高赔率场次
        """
        max_legs = 5
        legs = []
        
        # 优先选未用过的比赛，按赔率从高到低
        unused = [m for m in matches if m.match_id not in used_matches and m.recommendation]
        unused.sort(key=lambda m: m.analysis_details.get("pick_odds", 0), reverse=True)
        
        for m in unused:
            pick_odds = m.analysis_details.get("pick_odds", 0)
            if pick_odds >= 1.3:
                leg = self._create_leg(m)
                if leg:
                    legs.append(leg)
                    if len(legs) >= max_legs:
                        break
        
        # 如果不够3场，用所有比赛补充
        if len(legs) < 3:
            for m in matches:
                if m.recommendation and m.match_id not in {l.match.match_id for l in legs}:
                    leg = self._create_leg(m)
                    if leg:
                        legs.append(leg)
                        if len(legs) >= max_legs:
                            break
        
        ticket = Ticket(
            ticket_id=3,
            name="高倍博冷票",
            risk_level="高风险",
            legs=legs,
            investment=investment,
            strategy_desc=f"高风险高倍，{len(legs)}串1，低投入博高收益",
        )
        self._calculate_ticket(ticket)
        return ticket
    
    def _create_leg(self, match: Match) -> TicketLeg:
        """创建单腿"""
        if not match.recommendation:
            return None
        
        pick_type = match.analysis_details.get("pick_type", "had")
        pick_odds = match.analysis_details.get("pick_odds", 0)
        
        if pick_odds <= 0:
            return None
        
        rec = match.recommendation
        if "主胜" in rec:
            pick, pick_desc = "h", "主胜"
        elif "平局" in rec:
            pick, pick_desc = "d", "平局"
        elif "客胜" in rec:
            pick, pick_desc = "a", "客胜"
        else:
            pick, pick_desc = "h", rec
        
        return TicketLeg(
            match=match,
            pick=pick,
            pick_desc=pick_desc,
            odds=pick_odds,
            odds_type=pick_type,
            confidence=match.confidence,
        )
    
    def _ticket_total_odds(self, legs: List[TicketLeg]) -> float:
        """计算腿的组合赔率"""
        odds = 1.0
        for leg in legs:
            odds *= leg.odds
        return odds
    
    def _calculate_ticket(self, ticket: Ticket):
        """计算彩票的组合赔率和预期回报"""
        if not ticket.legs:
            ticket.total_odds = 1.0
            ticket.expected_return = 0.0
            return
        
        total_odds = self._ticket_total_odds(ticket.legs)
        ticket.total_odds = round(total_odds, 2)
        ticket.expected_return = round(ticket.investment * total_odds, 0)
        
        legs_desc = " + ".join([
            f"{l.match.home_team}vs{l.match.away_team}({l.pick_desc}@{l.odds:.2f})"
            for l in ticket.legs
        ])
        can_breakeven = "[OK]" if ticket.expected_return >= self.total_budget else "[FAIL]"
        print(f"  票{ticket.ticket_id}: {ticket.name} | {len(ticket.legs)}串1 | "
              f"投入{ticket.investment:.0f}元 | {ticket.total_odds:.2f}倍 | "
              f"回报{ticket.expected_return:.0f}元 | 回本{can_breakeven}")
        print(f"    选择: {legs_desc}")
