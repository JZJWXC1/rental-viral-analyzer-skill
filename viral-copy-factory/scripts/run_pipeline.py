"""
爆款文案工厂 - 命令行入口
封装 content_pipeline 的完整流水线，支持单条生成、批量生成、分析、历史查看。

用法:
    python scripts/run_pipeline.py generate --platform xhs --property-index 0
    python scripts/run_pipeline.py batch --platform xhs --count 5
    python scripts/run_pipeline.py analyze --property-index 0
    python scripts/run_pipeline.py history
"""

import argparse
import sys
from pathlib import Path

# 自动定位项目根目录（脚本向上两级即为项目根目录的父目录）
SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
# 项目根目录是 ali-agent/小红书抖音自动运营工具
# 从 skill 目录回退到 workspace，再进入项目
WORKSPACE = SKILL_DIR.parent
PROJECT_ROOT = WORKSPACE / "ali-agent" / "小红书抖音自动运营工具"

# 将项目根目录加入 Python 路径
sys.path.insert(0, str(PROJECT_ROOT))

# 设置日志
from loguru import logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def cmd_analyze(args):
    """房源画像分析"""
    from agents.content_pipeline import analyze_property, _print_analysis_report
    from agents.content_pipeline import _get_pipeline_output_dir
    from datetime import datetime
    import json

    result = analyze_property(args.property_index)
    _print_analysis_report(result)

    # 保存分析结果
    output_dir = _get_pipeline_output_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"analysis_{args.property_index}_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n分析结果已保存: {output_path}")


def cmd_generate(args):
    """单条内容生成"""
    from agents.content_pipeline import generate_smart_content

    result = generate_smart_content(
        property_index=args.property_index,
        platform=args.platform,
        style=args.style,
        content_type="sublease" if args.sublease else None,
    )

    if "error" in result:
        logger.error(f"生成失败: {result['error']}")
        sys.exit(1)


def cmd_batch(args):
    """批量生成"""
    from agents.content_pipeline import batch_generate

    report = batch_generate(
        count=args.count,
        platform=args.platform,
        style=args.style,
        content_type="sublease" if args.sublease else None,
    )

    if "error" in report:
        logger.error(f"批量生成失败: {report['error']}")
        sys.exit(1)


def cmd_history(args):
    """查看历史"""
    from agents.content_pipeline import show_history
    show_history()


def main():
    parser = argparse.ArgumentParser(
        description="爆款文案工厂 - 租房内容生成流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python scripts/run_pipeline.py analyze --property-index 0\n"
            "  python scripts/run_pipeline.py generate --platform xhs --property-index 0\n"
            "  python scripts/run_pipeline.py generate --platform douyin --property-index 3 --style B\n"
            "  python scripts/run_pipeline.py generate --platform xhs --property-index 5 --sublease\n"
            "  python scripts/run_pipeline.py batch --platform xhs --count 5\n"
            "  python scripts/run_pipeline.py batch --platform douyin --count 3\n"
            "  python scripts/run_pipeline.py history\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # analyze
    analyze_parser = subparsers.add_parser("analyze", help="分析单套房源画像")
    analyze_parser.add_argument("--property-index", "-p", type=int, required=True,
                                help="房源索引（从0开始）")

    # generate
    gen_parser = subparsers.add_parser("generate", help="为单套房源生成内容（完整流水线）")
    gen_parser.add_argument("--property-index", "-p", type=int, required=True,
                            help="房源索引（从0开始）")
    gen_parser.add_argument("--platform", choices=["xhs", "douyin"], required=True,
                            help="目标平台")
    gen_parser.add_argument("--style", "-s", choices=["A", "B", "C", "D"], default=None,
                            help="内容风格: A=年轻人攻略 B=品质公寓 C=转租故事 D=区域指南")
    gen_parser.add_argument("--sublease", action="store_true",
                            help="个人转租模式")

    # batch
    batch_parser = subparsers.add_parser("batch", help="批量生成内容")
    batch_parser.add_argument("--count", "-n", type=int, default=5,
                              help="生成数量（默认5）")
    batch_parser.add_argument("--platform", choices=["xhs", "douyin"], default="xhs",
                              help="目标平台（默认xhs）")
    batch_parser.add_argument("--style", "-s", choices=["A", "B", "C", "D"], default=None,
                              help="内容风格")
    batch_parser.add_argument("--sublease", action="store_true",
                              help="个人转租模式")

    # history
    subparsers.add_parser("history", help="查看流水线输出历史")

    # verbose
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="显示详细日志")

    args = parser.parse_args()

    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")

    if args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "generate":
        cmd_generate(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "history":
        cmd_history(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
