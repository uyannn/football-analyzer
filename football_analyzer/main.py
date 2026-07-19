"""
竞彩足球分析系统 - 主程序
"""
import os
import sys
import io
from datetime import datetime
from .models import AnalysisReport
from .data_fetchers.sporttery import SportteryFetcher
from .analyzers.match_analyzer import MatchAnalyzer
from .analyzers.strategy import StrategyGenerator
from .generators.html_report import HTMLReportGenerator

# 修复Windows控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8', errors='replace')


def log(msg):
    """带flush的打印，确保实时输出"""
    print(msg, flush=True)


def get_budget_input():
    """获取用户输入的投资金额"""
    log("[输入] 请输入今日投资金额（元），直接回车默认100:")
    while True:
        try:
            budget_str = input("金额: ").strip()
            if not budget_str:
                budget_str = "100"
            budget = float(budget_str)
            if budget <= 0:
                log("[错误] 金额必须大于0，请重新输入")
                continue
            if budget > 10000:
                log("[警告] 金额较大，确认继续吗？(y/n)")
                confirm = input().strip().lower()
                if confirm != 'y':
                    continue
            return budget
        except ValueError:
            log("[错误] 请输入有效的数字")
        except KeyboardInterrupt:
            log("\n[退出] 用户取消")
            sys.exit(0)


def main():
    """主入口"""
    log("=" * 60)
    log("  竞彩足球智能分析系统")
    log("=" * 60)
    log("")
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    log(f"[INFO] 分析日期: {report_date}")
    log("")
    
    # 获取投资金额
    budget = get_budget_input()
    log(f"[INFO] 投资金额: {budget:.0f}元")
    log("")
    
    # 1. 抓取竞彩数据
    log("[1/4] 抓取竞彩赔率数据...")
    sporttery = SportteryFetcher()
    matches = sporttery.fetch_matches()
    
    if not matches:
        log("[ERROR] 未获取到任何比赛数据，程序退出")
        return
    
    # 过滤可购买的比赛
    purchasable = sporttery.filter_purchasable_matches(matches)
    log("")
    
    # 2. 多维度分析
    log("[2/4] 多维度分析比赛...")
    analyzer = MatchAnalyzer()
    analyzed_matches = analyzer.analyze_all_matches(purchasable)
    log("")
    
    # 3. 生成策略
    log("[3/4] 生成投注策略...")
    strategy_gen = StrategyGenerator(total_budget=budget)
    strategy = strategy_gen.generate_strategy(analyzed_matches)
    log("")
    
    # 4. 生成报告
    log("[4/4] 生成HTML报告...")
    report = AnalysisReport(
        report_date=report_date,
        matches=analyzed_matches,
        strategy=strategy,
        notes=[
            "<strong>竞彩停售时间 23:00</strong> — 所有投注必须在23:00前完成购买",
            "部分比赛可能已开赛，请确认是否仍可购买滚球",
            "串关规则: 同一场比赛在同一张票中只能选择一个选项",
            "竞彩为娱乐性质，请理性投注，切勿超出可承受范围",
            "本分析仅供参考，不构成任何投注建议",
            "<strong>投资策略</strong>: 第一注或第二注单独命中即可回本，第三注多串1博高倍数",
        ],
    )
    
    generator = HTMLReportGenerator()
    
    # 输出到桌面体彩目录
    output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(
        output_dir,
        f"竞彩策略分析_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    
    generator.generate_report(report, output_file)
    
    log("")
    log("=" * 60)
    log("  分析完成！")
    log(f"  报告位置: {output_file}")
    log("=" * 60)
    log("")
    
    # 尝试打开报告
    try:
        if sys.platform == "win32":
            os.startfile(output_file)
        else:
            import webbrowser
            webbrowser.open(f"file://{output_file}")
    except:
        log(f"[INFO] 请手动打开报告: {output_file}")


if __name__ == "__main__":
    main()
