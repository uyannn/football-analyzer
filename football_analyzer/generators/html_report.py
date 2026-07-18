"""
HTML报告生成器
"""
import os
from datetime import datetime
from typing import List
from ..models import Match, BettingStrategy, AnalysisReport, Ticket


class HTMLReportGenerator:
    """HTML分析报告生成器"""
    
    def generate_report(self, report: AnalysisReport, output_path: str):
        """生成完整HTML报告"""
        html = self._build_html(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[OK] 报告已生成: {output_path}")
    
    def _build_html(self, report: AnalysisReport) -> str:
        """构建完整HTML"""
        matches_html = self._render_matches(report.matches)
        tickets_html = self._render_tickets(report.strategy)
        scenarios_html = self._render_scenarios(report.strategy)
        summary_html = self._render_summary(report)
        fund_alloc_html = self._render_fund_allocation(report.strategy)
        
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>竞彩足球策略分析 - {report.report_date}</title>
<style>
{self._get_css()}
</style>
</head>
<body>
<div class="container">
<h1>⚽ 竞彩足球策略分析</h1>
<p class="subtitle">{report.report_date} | 总资金: {report.strategy.total_budget:.0f}元 | 3票策略</p>

<div class="strategy-desc">
<strong>投资策略:</strong> 第一注或第二注单独命中即可回本，第三注多串1博高倍数
</div>

{summary_html}

<div class="section-title">📋 可投注赛事与分析</div>
{matches_html}

<div class="section-title">💰 资金分配</div>
{fund_alloc_html}

<div class="section-title">🎫 投注方案</div>
{tickets_html}

<div class="section-title">📊 预期结果 (情景分析)</div>
{scenarios_html}

<div class="notes">
<h4>⚠️ 重要提示</h4>
<ul>
{"".join(f'<li>{note}</li>' for note in report.notes)}
</ul>
</div>
</div>
</body>
</html>"""
    
    def _render_summary(self, report: AnalysisReport) -> str:
        """渲染摘要卡片"""
        s = report.strategy
        tickets = s.tickets
        
        # 计算各注回报
        returns = [t.expected_return for t in tickets] if tickets else [0, 0, 0]
        while len(returns) < 3:
            returns.append(0)
        
        # 检查回本情况
        t1_breakeven = returns[0] >= s.total_budget if returns[0] else False
        t2_breakeven = returns[1] >= s.total_budget if returns[1] else False
        
        best = sum(returns)
        safe_label = f"{'✓' if t1_breakeven or t2_breakeven else '✗'} 回本检查"
        
        return f"""
<div class="summary-row">
<div class="summary-card green">
<div class="label">总投入</div>
<div class="value">¥{s.total_budget:.0f}</div>
</div>
<div class="summary-card blue">
<div class="label">全部命中回报</div>
<div class="value">¥{best:.0f}</div>
</div>
<div class="summary-card {'green' if t1_breakeven else 'yellow'}">
<div class="label">第一注回报 {'✓回本' if t1_breakeven else '✗未回本'}</div>
<div class="value">¥{returns[0]:.0f}</div>
</div>
<div class="summary-card {'green' if t2_breakeven else 'yellow'}">
<div class="label">第二注回报 {'✓回本' if t2_breakeven else '✗未回本'}</div>
<div class="value">¥{returns[1]:.0f}</div>
</div>
</div>"""
    
    def _render_fund_allocation(self, strategy: BettingStrategy) -> str:
        """渲染资金分配表"""
        rows = []
        for t in strategy.tickets:
            breakeven = "✓ 可回本" if t.expected_return >= strategy.total_budget else "✗ 未回本"
            breakeven_class = "profit-pos" if t.expected_return >= strategy.total_budget else "profit-neg"
            rows.append(f"""
<tr>
<td>{'🟢' if t.ticket_id==1 else '🟡' if t.ticket_id==2 else '🔴'} {t.name}</td>
<td>{t.risk_level}</td>
<td>{len(t.legs)}串1</td>
<td class="odds-cell">¥{t.investment:.0f}</td>
<td>{t.investment/strategy.total_budget*100:.0f}%</td>
<td class="odds-cell">{t.total_odds:.2f}x</td>
<td class="odds-cell" style="color:var(--accent-green)">¥{t.expected_return:.0f}</td>
<td class="{breakeven_class}">{breakeven}</td>
</tr>""")
        
        return f"""
<table class="match-table">
<thead>
<tr>
<th>票次</th><th>风险</th><th>串法</th><th>投入</th><th>占比</th><th>赔率</th><th>回报</th><th>回本</th>
</tr>
</thead>
<tbody>{"".join(rows)}</tbody>
</table>"""
    
    def _render_matches(self, matches: List[Match]) -> str:
        """渲染比赛列表"""
        rows = []
        for m in matches:
            had = m.had_odds
            hhad = m.hhad_odds
            
            # 分析详情
            details = m.analysis_details or {}
            scores = details.get("scores", {})
            home_stats = details.get("home_stats")
            away_stats = details.get("away_stats")
            weather = details.get("weather")
            
            # 构建分析摘要
            analysis_parts = []
            if home_stats:
                form_str = " ".join(home_stats.recent_form[:3]) if home_stats.recent_form else "?"
                analysis_parts.append(f"主队近况: {form_str}")
            if away_stats:
                form_str = " ".join(away_stats.recent_form[:3]) if away_stats.recent_form else "?"
                analysis_parts.append(f"客队近况: {form_str}")
            if weather:
                analysis_parts.append(f"天气: {weather.condition}")
            
            analysis_text = " | ".join(analysis_parts) if analysis_parts else "无详细分析"
            
            conf_bar = f'<div class="conf-bar"><div class="conf-fill" style="width:{m.confidence*100:.0f}%"></div></div>'
            
            rec_html = f'<span class="pick">{m.recommendation}</span>' if m.recommendation else '<span style="color:var(--text-dim)">—</span>'
            
            rows.append(f"""
<tr>
<td>{m.match_num}</td>
<td><span class="league-tag">{m.league}</span></td>
<td>{m.match_date}<br><small style="color:var(--text-dim)">{m.match_time[:5]}</small></td>
<td>
<div>{m.home_team}<small style="color:var(--text-dim)">{m.home_rank}</small></div>
<div>vs {m.away_team}<small style="color:var(--text-dim)">{m.away_rank}</small></div>
</td>
<td class="odds-cell">{had.get('h', 0):.2f}</td>
<td class="odds-cell">{had.get('d', 0):.2f}</td>
<td class="odds-cell">{had.get('a', 0):.2f}</td>
<td>{rec_html}</td>
<td><small>{analysis_text}</small></td>
</tr>""")
        
        return f"""
<table class="match-table">
<thead>
<tr>
<th>编号</th><th>联赛</th><th>时间</th><th>对阵</th>
<th>主胜</th><th>平局</th><th>客胜</th><th>推荐</th><th>分析</th>
</tr>
</thead>
<tbody>{"".join(rows)}</tbody>
</table>"""
    
    def _render_tickets(self, strategy: BettingStrategy) -> str:
        """渲染三票策略"""
        cards = []
        badges = ["badge-safe", "badge-mid", "badge-high"]
        emojis = ["🟢", "🟡", "🔴"]
        
        for i, ticket in enumerate(strategy.tickets):
            if not ticket.legs:
                cards.append(f"""
<div class="ticket">
<div class="ticket-header">
<span class="ticket-name">{emojis[i]} 第{ticket.ticket_id}票 — {ticket.name}</span>
<span class="ticket-badge {badges[i]}">无数据</span>
</div>
<div class="ticket-body"><p style="color:var(--text-dim)">未找到合适的比赛组合</p></div>
</div>""")
                continue
            
            legs_html = ""
            for leg in ticket.legs:
                odds_type_label = "让球" if leg.odds_type == "hhad" else ""
                legs_html += f"""
<div class="leg">
<div class="leg-match">{leg.match.league} | {leg.match.home_team} vs {leg.match.away_team}</div>
<div class="leg-pick">{odds_type_label}{leg.pick_desc}</div>
<div class="leg-odds">@ {leg.odds:.2f}</div>
</div>"""
            
            breakeven = ticket.expected_return >= strategy.total_budget
            breakeven_html = f'<span class="breakeven-tag {"yes" if breakeven else "no"}">{"✓ 可回本" if breakeven else "✗ 未回本"}</span>'
            
            cards.append(f"""
<div class="ticket">
<div class="ticket-header">
<span class="ticket-name">{emojis[i]} 第{ticket.ticket_id}票 — {ticket.name}</span>
<span class="ticket-badge {badges[i]}">{ticket.risk_level} · {len(ticket.legs)}串1</span>
</div>
<div class="ticket-body">
<p class="ticket-strategy">{ticket.strategy_desc}</p>
<div class="ticket-legs">{legs_html}</div>
</div>
<div class="ticket-footer">
<div class="invest">投入: <span>¥{ticket.investment:.0f}</span> | 赔率: <span style="color:var(--accent-blue)">{ticket.total_odds:.2f}x</span> | {breakeven_html}</div>
<div class="return">预期回报: <span>¥{ticket.expected_return:.0f}</span></div>
</div>
</div>""")
        
        return f'<div class="ticket-grid">{"".join(cards)}</div>'
    
    def _render_scenarios(self, strategy: BettingStrategy) -> str:
        """渲染情景分析"""
        tickets = strategy.tickets
        if len(tickets) < 3:
            return "<p>数据不足</p>"
        
        t1, t2, t3 = tickets[0], tickets[1], tickets[2]
        budget = strategy.total_budget
        
        scenarios = [
            ("仅第一注中", True, False, False),
            ("仅第二注中", False, True, False),
            ("第一+第二中", True, True, False),
            ("第一+第三中", True, False, True),
            ("第二+第三中", False, True, True),
            ("三注全中", True, True, True),
            ("全部不中", False, False, False),
        ]
        
        rows = []
        for desc, h1, h2, h3 in scenarios:
            ret = 0
            if h1: ret += t1.expected_return
            if h2: ret += t2.expected_return
            if h3: ret += t3.expected_return
            profit = ret - budget
            profit_class = "profit-pos" if profit >= 0 else "profit-neg"
            profit_str = f"+{profit:.0f}" if profit >= 0 else f"{profit:.0f}"
            
            # 回本标记
            breakeven_tag = ""
            if ret >= budget:
                breakeven_tag = ' <span style="color:var(--accent-green);font-size:12px">✓回本</span>'
            
            # 高亮回本行
            row_class = ' class="highlight-row"' if ret >= budget else ''
            
            rows.append(f"""
<tr{row_class}>
<td>{desc}</td>
<td class="{'profit-pos' if h1 else 'profit-neg'}">{'✓' if h1 else '✗'}</td>
<td class="{'profit-pos' if h2 else 'profit-neg'}">{'✓' if h2 else '✗'}</td>
<td class="{'profit-pos' if h3 else 'profit-neg'}">{'✓' if h3 else '✗'}</td>
<td class="odds-cell">¥{ret:.0f}{breakeven_tag}</td>
<td class="{profit_class}">{profit_str}元</td>
</tr>""")
        
        return f"""
<table class="scenario-table">
<thead>
<tr><th>情景</th><th>🟢 第一注</th><th>🟡 第二注</th><th>🔴 第三注</th><th>总回报</th><th>净利润</th></tr>
</thead>
<tbody>{"".join(rows)}</tbody>
</table>"""
    
    def _get_css(self) -> str:
        """获取CSS样式"""
        return """
:root {
  --bg: #0f1923;
  --card: #1a2733;
  --card-hover: #1f3040;
  --accent-green: #00e676;
  --accent-yellow: #ffd740;
  --accent-red: #ff5252;
  --accent-blue: #448aff;
  --text: #e0e0e0;
  --text-dim: #78909c;
  --border: #263238;
}
* { margin:0; padding:0; box-sizing:border-box; }
body {
  font-family: -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 20px;
}
.container { max-width: 1200px; margin: 0 auto; }
h1 {
  text-align: center; font-size: 28px; margin-bottom: 8px;
  background: linear-gradient(135deg, var(--accent-green), var(--accent-blue));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.subtitle { text-align: center; color: var(--text-dim); margin-bottom: 10px; font-size: 14px; }
.strategy-desc {
  text-align: center; background: rgba(0,230,118,0.08); border: 1px solid rgba(0,230,118,0.2);
  border-radius: 10px; padding: 12px 20px; margin-bottom: 24px; font-size: 15px;
  color: var(--accent-green);
}
.section-title {
  font-size: 20px; font-weight: 700; margin: 30px 0 16px;
  padding-left: 12px; border-left: 4px solid var(--accent-blue);
}
.summary-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 24px; }
.summary-card {
  background: var(--card); border-radius: 12px; padding: 18px;
  text-align: center; border: 1px solid var(--border);
}
.summary-card .label { font-size: 13px; color: var(--text-dim); margin-bottom: 6px; }
.summary-card .value { font-size: 26px; font-weight: 800; }
.green .value { color: var(--accent-green); }
.yellow .value { color: var(--accent-yellow); }
.red .value { color: var(--accent-red); }
.blue .value { color: var(--accent-blue); }
.match-table, .scenario-table {
  width: 100%; border-collapse: collapse; background: var(--card);
  border-radius: 12px; overflow: hidden; border: 1px solid var(--border);
}
.match-table th, .scenario-table th {
  background: #162230; padding: 12px 10px; text-align: left;
  font-size: 13px; color: var(--text-dim); font-weight: 600;
}
.match-table td, .scenario-table td {
  padding: 12px 10px; border-top: 1px solid var(--border); font-size: 13px;
  vertical-align: middle;
}
.match-table tr:hover td, .scenario-table tr:hover td { background: var(--card-hover); }
.league-tag {
  display: inline-block; padding: 2px 8px; border-radius: 20px;
  font-size: 11px; background: #0d47a1; color: #90caf9;
}
.odds-cell { font-family: 'Consolas', monospace; font-weight: 600; }
.pick {
  background: rgba(0,230,118,0.12); color: var(--accent-green);
  padding: 3px 8px; border-radius: 6px; font-weight: 700; font-size: 12px;
  white-space: nowrap;
}
.conf-bar { width: 60px; height: 6px; background: #263238; border-radius: 3px; }
.conf-fill { height: 100%; background: var(--accent-green); border-radius: 3px; }
.ticket-grid { display: grid; grid-template-columns: 1fr; gap: 20px; }
.ticket {
  background: var(--card); border-radius: 14px;
  border: 1px solid var(--border); overflow: hidden;
}
.ticket-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
}
.ticket-name { font-size: 18px; font-weight: 700; }
.ticket-badge { padding: 5px 14px; border-radius: 20px; font-size: 13px; font-weight: 700; }
.badge-safe { background: rgba(0,230,118,0.15); color: var(--accent-green); }
.badge-mid { background: rgba(255,215,64,0.15); color: var(--accent-yellow); }
.badge-high { background: rgba(255,82,82,0.15); color: var(--accent-red); }
.ticket-body { padding: 16px 20px; }
.ticket-strategy { color: var(--text-dim); font-size: 13px; margin-bottom: 12px; font-style: italic; }
.ticket-legs { display: flex; gap: 10px; flex-wrap: wrap; }
.leg {
  background: #162230; border: 1px solid var(--border);
  border-radius: 10px; padding: 10px 14px; font-size: 13px; flex: 1; min-width: 160px;
}
.leg .leg-match { color: var(--text-dim); font-size: 12px; margin-bottom: 4px; }
.leg .leg-pick { font-weight: 700; color: var(--accent-green); font-size: 15px; }
.leg .leg-odds { color: var(--accent-blue); font-family: 'Consolas', monospace; margin-top: 4px; }
.ticket-footer {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 20px; background: #162230; border-top: 1px solid var(--border);
  flex-wrap: wrap; gap: 8px;
}
.ticket-footer .invest { font-size: 14px; color: var(--text-dim); }
.ticket-footer .invest span { color: var(--text); font-weight: 700; }
.ticket-footer .return { font-size: 14px; }
.ticket-footer .return span { font-weight: 800; font-size: 20px; color: var(--accent-green); }
.breakeven-tag { font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.breakeven-tag.yes { background: rgba(0,230,118,0.15); color: var(--accent-green); }
.breakeven-tag.no { background: rgba(255,82,82,0.15); color: var(--accent-red); }
.profit-pos { color: var(--accent-green); font-weight: 700; }
.profit-neg { color: var(--accent-red); font-weight: 700; }
.highlight-row { background: rgba(0,230,118,0.05) !important; }
.highlight-row td { border-left-color: var(--accent-green) !important; }
.notes {
  background: var(--card); border-radius: 12px; padding: 18px;
  border: 1px solid var(--border); margin-top: 30px;
}
.notes h4 { color: var(--accent-yellow); margin-bottom: 8px; font-size: 14px; }
.notes li { font-size: 13px; color: var(--text-dim); line-height: 1.8; margin-left: 18px; }
@media (max-width: 700px) {
  .summary-row { grid-template-columns: repeat(2, 1fr); }
}
"""
