---
name: viral-element-analyzer
description: 从小红书/抖音趋势数据中采集高互动帖子，AI分析提取爆款内容结构（钩子模板、正文结构、标签策略），存储到本地结构库并同步到飞书云文档。当用户提到趋势采集、爆款分析、爆款元素、viral analysis、trending analysis、更新爆款结构库时使用。
---

# 爆款元素采集与分析

从租房领域趋势帖子中提取爆款内容结构，存储到本地 JSON 和飞书云文档。

## 项目路径

- 项目根目录: `C:\Users\吴志坚\.qoderwork\workspace\mq4sn3a8l69spk25\ali-agent\小红书抖音自动运营工具\`
- 趋势数据: `data/trending/` (JSON 文件，每条含 title/body/likes/comments/platform)
- 爆款结构库: `data/viral_structures.json`
- 飞书目标文件夹 token: `MCIafnQxMl05XCdouCpc1GzjnAf`

## 执行流程

### Step 1: 收集趋势数据

**优先读取本地数据:**
```bash
# 运行项目的趋势采集脚本（抓取小红书/抖音热帖）
cd "C:\Users\吴志坚\.qoderwork\workspace\mq4sn3a8l69spk25\ali-agent\小红书抖音自动运营工具"
python -X utf8 -m agents.daily_news --type all --summary-only
```

**若本地 `data/trending/` 为空或不存在:**
使用 WebSearch 搜索以下关键词，手动收集 10-20 条帖子数据:
- "小红书 租房 爆款 高赞"
- "抖音 租房 热门 万赞"
- "小红书 杭州租房 热门笔记"
- "抖音 看房vlog 热门"

每条帖子需要: `title`, `body`(摘要), `likes`, `comments`, `platform`(xhs/dy)

### Step 2: 筛选高互动帖子

按平台使用不同阈值:
- **小红书**: 点赞 >= 500 或 (点赞 + 评论*2) >= 750
- **抖音**: 点赞 >= 1000 或 (点赞 + 评论*2) >= 1500

按平台分组: `xhs_posts` 和 `dy_posts`。

### Step 3: AI 提取爆款结构

对每个平台的高互动帖子，调用 AI 分析。将帖子数据格式化为文本后，使用以下 system prompt:

```
你是一个专业的内容运营专家，擅长分析{平台名}平台的爆款内容结构。
请分析以下高互动帖子，提取爆款内容结构模式。

严格按以下 JSON 格式输出:
{
  "structures": [
    {
      "id": "平台_结构类型（如 xhs_lowprice_surprise）",
      "name": "结构名称",
      "description": "结构描述",
      "title_templates": ["标题模板（用{{价格}}、{{区域}}等占位符）"],
      "hook_templates": ["开头钩子模板"],
      "body_structure": "正文结构描述",
      "tag_strategy": "标签策略",
      "applicable_scenarios": ["适用场景"],
      "performance_stats": {"avg_likes": N, "avg_comments": N, "sample_count": N}
    }
  ]
}

提取 3-5 个最具代表性的爆款结构。
```

**AI 调用方式**: 使用项目现有的 DashScope API (Qwen3.7-Max):
```python
# 通过项目脚本调用
python -X utf8 -c "
import sys, json
sys.path.insert(0, '.')
from agents.news_config import ai_chat_completion
# ... 构建 messages 调用 ai_chat_completion(messages, temperature=0.5, max_tokens=3000)
"
```

### Step 4: 更新本地结构库

读取 `data/viral_structures.json`，按 `id` 去重合并新提取的结构:
- 新 id → 追加
- 已有 id → 覆盖更新
- 为每个结构附加 `platform` ("xhs"/"dy") 和 `collected_at` (当前时间)

保存格式:
```json
{
  "updated_at": "YYYY-MM-DD HH:MM:SS",
  "total_structures": N,
  "xhs_count": N,
  "dy_count": N,
  "structures": [...]
}
```

### Step 5: 同步到飞书

使用 lark-cli 创建 Markdown 文档到飞书文件夹:

```bash
lark-cli markdown +create \
  --name "爆款结构库_YYYY-MM-DD.md" \
  --folder-token MCIafnQxMl05XCdouCpc1GzjnAf \
  --file ./viral_report.md
```

**飞书文档格式:**

```markdown
# 爆款结构库 - YYYY-MM-DD 更新

> 共 N 个结构 | 小红书 X 个 | 抖音 Y 个

## 小红书平台 (X 个)

### 1. 结构名称
- **描述**: ...
- **标题模板**: 模板1 / 模板2
- **开头钩子**: 钩子1
- **正文结构**: ...
- **标签策略**: ...
- **效果**: 平均点赞 N，平均评论 N

---

## 抖音平台 (Y 个)
（同上格式）
```

**注意**: 若 lark-cli 未认证，提示用户先运行 `lark-cli auth login --domain drive,markdown --recommend`。

### Step 6: 输出汇总

向用户报告:
1. 分析了多少条帖子，筛选出多少条高互动
2. 新增/更新了哪些爆款结构（列出名称）
3. 本地 JSON 文件路径
4. 飞书文档链接

## 边界情况

- **无趋势数据**: 用 WebSearch 搜集，或提示用户手动放 JSON 到 `data/trending/`
- **AI 返回解析失败**: 打印原始响应，重试一次，仍失败则跳过该平台
- **飞书写入失败**: 仅保存本地文件，提示认证问题
- **结构库为空**: 直接创建新文件，不合并
