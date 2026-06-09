"""
爆款元素采集与分析脚本
用法: python collect_and_analyze.py [--project-root PATH] [--output-md PATH]

功能:
  1. 从项目 data/trending/ 目录加载趋势帖子数据
  2. 按平台筛选高互动帖子
  3. 调用 Qwen AI 提取爆款内容结构
  4. 合并到本地 viral_structures.json
  5. 生成 Markdown 报告文件
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


# ============================================================
# 常量
# ============================================================

HIGH_ENGAGEMENT_THRESHOLD_XHS = 500
HIGH_ENGAGEMENT_THRESHOLD_DY = 1000


def get_default_project_root():
    """默认项目根目录: 脚本所在目录向上 3 级 (scripts/ -> skill/ -> skills/ -> 项目搜索)"""
    # 也支持直接传入
    candidates = [
        Path.cwd(),
        Path.cwd() / "小红书抖音自动运营工具",
        Path(__file__).resolve().parent.parent.parent / "小红书抖音自动运营工具",
    ]
    for c in candidates:
        if (c / "config.yaml").exists():
            return c
    return None


def load_trending_data(trending_dir: Path) -> list:
    """从 data/trending/ 加载所有帖子"""
    if not trending_dir.exists():
        print(f"[WARN] 趋势数据目录不存在: {trending_dir}")
        return []

    all_posts = []
    for json_file in sorted(trending_dir.glob("*.json")):
        if json_file.name == "patterns.json":
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                all_posts.extend(data)
            elif isinstance(data, dict):
                all_posts.append(data)
        except Exception as e:
            print(f"[WARN] 加载 {json_file.name} 失败: {e}")

    print(f"[INFO] 共加载 {len(all_posts)} 条趋势帖子")
    return all_posts


def filter_high_engagement(posts: list, platform: str) -> list:
    """筛选高互动帖子"""
    threshold = HIGH_ENGAGEMENT_THRESHOLD_XHS if platform == "xhs" else HIGH_ENGAGEMENT_THRESHOLD_DY
    high_posts = []
    for p in posts:
        plat = p.get("platform", "")
        if platform == "xhs" and not ("xiaohongshu" in plat or "xhs" in plat):
            continue
        if platform == "dy" and not ("douyin" in plat or "dy" in plat):
            continue

        likes = p.get("likes", 0) or 0
        comments = p.get("comments", 0) or 0
        engagement = likes + comments * 2

        if likes >= threshold or engagement >= threshold * 1.5:
            high_posts.append(p)

    return high_posts


def extract_structures_ai(posts: list, platform: str, ai_chat_fn) -> list:
    """使用 AI 提取爆款结构"""
    platform_name = "小红书" if platform == "xhs" else "抖音"

    posts_text_parts = []
    for i, p in enumerate(posts):
        title = p.get("title", "无标题")
        likes = p.get("likes", 0)
        comments = p.get("comments", 0)
        body = p.get("body", p.get("description", ""))
        body_short = (body[:200] + "...") if len(body) > 200 else body
        posts_text_parts.append(
            f"【帖子{i + 1}】\n标题: {title}\n点赞: {likes}  评论: {comments}\n内容摘要: {body_short}"
        )
    posts_text = "\n\n".join(posts_text_parts)

    system_prompt = (
        f"你是一个专业的内容运营专家，擅长分析{platform_name}平台的爆款内容结构。\n"
        f"请分析以下高互动{platform_name}帖子，提取爆款内容结构模式。\n\n"
        f"请严格按照以下 JSON 格式输出（不要输出其他内容）：\n"
        '{\n  "structures": [\n    {\n'
        '      "id": "平台_结构类型（如 xhs_lowprice_surprise）",\n'
        '      "name": "结构名称",\n'
        '      "description": "结构描述",\n'
        '      "title_templates": ["标题模板1（用{{价格}}、{{区域}}等占位符）"],\n'
        '      "hook_templates": ["开头钩子模板1"],\n'
        '      "body_structure": "正文结构描述",\n'
        '      "tag_strategy": "标签策略描述",\n'
        '      "applicable_scenarios": ["适用场景1", "适用场景2"],\n'
        '      "performance_stats": {"avg_likes": 0, "avg_comments": 0, "sample_count": 0}\n'
        '    }\n  ]\n}\n\n'
        f"请提取3-5个最具代表性的爆款结构。"
    )

    user_message = (
        f"以下是 {len(posts)} 条高互动{platform_name}帖子数据，请分析并提取爆款结构：\n\n{posts_text}"
    )

    try:
        raw = ai_chat_fn(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=3000,
        )

        # 清理 markdown 代码块
        if raw.strip().startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        result = json.loads(raw.strip())
        structures = result.get("structures", [])

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for s in structures:
            s["platform"] = platform
            s["collected_at"] = now_str

        return structures

    except json.JSONDecodeError as e:
        print(f"[ERROR] AI 返回 JSON 解析失败: {e}")
        return []
    except Exception as e:
        print(f"[ERROR] 结构提取失败: {e}")
        return []


def merge_structures(new_structures: list, structures_file: Path) -> dict:
    """合并新结构到已有结构库（按 id 去重）"""
    existing = {"structures": []}
    if structures_file.exists():
        try:
            with open(structures_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass

    merged = {s["id"]: s for s in existing.get("structures", []) if "id" in s}
    for s in new_structures:
        sid = s.get("id")
        if sid:
            merged[sid] = s

    final = list(merged.values())
    output = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_structures": len(final),
        "xhs_count": sum(1 for s in final if s.get("platform") == "xhs"),
        "dy_count": sum(1 for s in final if s.get("platform") == "dy"),
        "structures": final,
    }

    structures_file.parent.mkdir(parents=True, exist_ok=True)
    with open(structures_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    return output


def generate_markdown_report(data: dict) -> str:
    """生成飞书 Markdown 报告"""
    today = datetime.now().strftime("%Y-%m-%d")
    structures = data.get("structures", [])
    xhs = [s for s in structures if s.get("platform") == "xhs"]
    dy = [s for s in structures if s.get("platform") == "dy"]

    lines = [
        f"# 爆款结构库 - {today} 更新",
        "",
        f"> 共 {len(structures)} 个结构 | 小红书 {len(xhs)} 个 | 抖音 {len(dy)} 个",
        f"> 更新时间: {data.get('updated_at', '')}",
        "",
    ]

    for platform_name, platform_structures in [("小红书", xhs), ("抖音", dy)]:
        if not platform_structures:
            continue

        lines.append(f"## {platform_name}平台 ({len(platform_structures)} 个)")
        lines.append("")

        for i, s in enumerate(platform_structures, 1):
            stats = s.get("performance_stats", {})
            lines.append(f"### {i}. {s.get('name', '未命名')}")
            lines.append(f"- **ID**: `{s.get('id', '')}`")
            lines.append(f"- **描述**: {s.get('description', '')}")

            templates = s.get("title_templates", [])
            if templates:
                lines.append(f"- **标题模板**: {' / '.join(templates[:3])}")

            hooks = s.get("hook_templates", [])
            if hooks:
                lines.append(f"- **开头钩子**: {hooks[0]}")

            lines.append(f"- **正文结构**: {s.get('body_structure', '')}")
            lines.append(f"- **标签策略**: {s.get('tag_strategy', '')}")
            lines.append(
                f"- **效果**: 平均点赞 {stats.get('avg_likes', 'N/A')}，"
                f"平均评论 {stats.get('avg_comments', 'N/A')}"
            )
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="爆款元素采集与分析")
    parser.add_argument("--project-root", type=str, default=None, help="项目根目录路径")
    parser.add_argument("--output-md", type=str, default=None, help="Markdown 报告输出路径")
    args = parser.parse_args()

    # 确定项目根目录
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = get_default_project_root()

    if not project_root or not (project_root / "config.yaml").exists():
        print("[ERROR] 找不到项目根目录（需要 config.yaml）。请用 --project-root 指定。")
        sys.exit(1)

    print(f"[INFO] 项目根目录: {project_root}")

    # 导入项目 AI 模块
    sys.path.insert(0, str(project_root))
    from agents.news_config import ai_chat_completion

    # 1. 加载趋势数据
    trending_dir = project_root / "data" / "trending"
    all_posts = load_trending_data(trending_dir)

    if not all_posts:
        print("[WARN] 没有趋势数据。请确保 data/trending/ 目录中有 JSON 文件。")
        print("[HINT] 可先运行: python -m agents.daily_news --type all")
        sys.exit(0)

    # 2. 筛选高互动帖子
    xhs_high = filter_high_engagement(all_posts, "xhs")
    dy_high = filter_high_engagement(all_posts, "dy")
    print(f"[INFO] 高互动帖子: 小红书 {len(xhs_high)} 条, 抖音 {len(dy_high)} 条")

    # 3. AI 提取爆款结构
    all_new = []
    if xhs_high:
        print("[INFO] 分析小红书高互动帖子...")
        xhs_structures = extract_structures_ai(xhs_high, "xhs", ai_chat_completion)
        all_new.extend(xhs_structures)
        print(f"[INFO] 提取小红书结构: {len(xhs_structures)} 个")

    if dy_high:
        print("[INFO] 分析抖音高互动帖子...")
        dy_structures = extract_structures_ai(dy_high, "dy", ai_chat_completion)
        all_new.extend(dy_structures)
        print(f"[INFO] 提取抖音结构: {len(dy_structures)} 个")

    if not all_new:
        print("[WARN] 未提取到任何爆款结构")
        sys.exit(0)

    # 4. 合并到结构库
    structures_file = project_root / "data" / "viral_structures.json"
    result = merge_structures(all_new, structures_file)
    print(f"[INFO] 结构库已更新: {structures_file}")
    print(f"  小红书: {result['xhs_count']} 个")
    print(f"  抖音:   {result['dy_count']} 个")
    print(f"  总计:   {result['total_structures']} 个")

    # 5. 生成 Markdown 报告
    md_content = generate_markdown_report(result)

    if args.output_md:
        md_path = Path(args.output_md)
    else:
        md_path = project_root / "data" / "trending" / f"viral_report_{datetime.now().strftime('%Y-%m-%d')}.md"

    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"[INFO] Markdown 报告: {md_path}")
    print(f"\n[DONE] 爆款结构库更新完成!")


if __name__ == "__main__":
    main()
