---
name: viral-copy-factory
description: 租房爆款文案工厂。从房源画像分析到AI内容生成（含美化）、去重评分、重试优化的完整流水线。爆款密码来自飞书报告。当用户提到生成租房文案、爆款文案、小红书笔记生成、抖音视频文案、内容创作、copywriter、写文案、一键生成内容时使用。
---

# 爆款文案工厂

完整的租房内容创作流水线：房源画像分析 → 飞书爆款密码注入 → AI美化生成 → 去重评分 → 重试优化 → 保存。

## 项目路径

- 项目根目录: `C:\Users\吴志坚\.qoderwork\workspace\mq4sn3a8l69spk25\ali-agent\小红书抖音自动运营工具\`
- 房源数据: `data/inventory_data_clean.json` 或 `data/inventory_data.json`
- 飞书爆款报告: `data/feishu_viral_report.md`（21个结构: 7小红书 + 14抖音）
- 流水线输出: `data/pipeline_output/`
- 配置文件: `config.yaml`（含 AI API 配置）

## 前置条件

运行前确认:
1. `config.yaml` 中有 `ai.api_key` 和 `ai.base_url`（DashScope 兼容接口）
2. `data/feishu_viral_report.md` 存在（由 viral-element-analyzer skill 生成）
3. 房源数据文件存在

## 执行方式

### 单条生成

```bash
cd "C:\Users\吴志坚\.qoderwork\workspace\mq4sn3a8l69spk25\ali-agent\小红书抖音自动运营工具"
python -X utf8 scripts/run_pipeline.py generate --platform xhs --property-index 0
python -X utf8 scripts/run_pipeline.py generate --platform douyin --property-index 3 --style B
python -X utf8 scripts/run_pipeline.py generate --platform xhs --property-index 5 --sublease
```

参数:
- `--platform`: `xhs`（小红书）或 `douyin`（抖音），必填
- `--property-index`: 房源索引（从0开始），必填
- `--style`: 内容风格 A/B/C/D（可选）— A=年轻人攻略 B=品质公寓 C=转租故事 D=区域指南
- `--sublease`: 个人转租模式，优先使用转租型爆款结构

### 批量生成

```bash
python -X utf8 scripts/run_pipeline.py batch --platform xhs --count 5
python -X utf8 scripts/run_pipeline.py batch --platform douyin --count 3 --style A
```

### 房源画像分析（仅分析不生成）

```bash
python -X utf8 scripts/run_pipeline.py analyze --property-index 0
```

### 查看历史

```bash
python -X utf8 scripts/run_pipeline.py history
```

## 流水线流程（内部机制，无需手动执行）

### 步骤 1: 房源画像分析

AI 分析房源数据，生成画像报告:
- 价格优势分析、户型特点、区域配套
- 目标人群推荐（如"刚毕业的大学生"）
- 推荐内容风格（A/B/C/D）
- 核心卖点提炼 + 真实缺点（增加可信度）

### 步骤 2: 爆款密码 + 生成 + 评分循环

**2a. 从飞书获取爆款密码**

自动读取 `data/feishu_viral_report.md`，解析出结构化爆款数据:
- 标题模板（如"月租{{价格}}住进{{区域}}{{房型}}！太香了"）
- 开头钩子、正文结构、标签策略
- 按平台和房源特征推荐 top 3 结构

**2b. AI 内容生成（含美化）**

生成即美化，输出即最终发布版本:

小红书输出: 封面文案x3 + 标题 + 正文(200-400字) + 标签x15
抖音输出: 标题x3 + 最终标题 + 正文(100-200字) + 标签x10 + 开头钩子

美化要求已内嵌在 prompt 中:
- emoji 点缀（每段1-2个，不堆砌）
- 短句+换行+分段，有节奏感
- 亲切口语化，像朋友分享真实体验
- 自然的互动引导结尾

写作禁区: 无 emoji 列表、无"姐妹们/家人们"、无震惊体、无感叹号堆叠、必须包含至少1个真实缺点

**2c. 去重评分（7维度/6维度，含去重）**

评分前自动扫描 `data/pipeline_output/` 已有内容，计算标题+正文+标签相似度。

| 维度 | 小红书 | 抖音 |
|------|--------|------|
| 封面/标题吸引力 | 18 | 22 |
| 正文真实感/口语化 | 18 | 18 |
| 信息完整性/传达 | 14 | 17 |
| 标签质量 | 15 | 15 |
| 去广告化 | 12 | - |
| 互动引导 | 13 | - |
| **内容去重** | **10** | **10** |
| **总分** | **100** | **100** |

**2d. 评分反馈循环**

- 得分 >= 80: 通过，保存
- 得分 < 80: 提取薄弱维度 + 去重方向 → 重写（最多3次）
- 3次仍未达标: 标记"需人工审核"

### 步骤 3: 保存结果

输出到 `data/pipeline_output/pipeline_{platform}_{index}_{timestamp}.json`

## 结果解读

脚本执行完毕后会输出:
1. 房源画像摘要
2. 使用的爆款结构名称
3. 每次生成的得分和判定
4. 去重检查结果（最高相似度、相似内容列表）
5. 最终内容预览（标题、正文长度、标签数）

JSON 输出包含:
- `content`: 生成的完整内容
- `score_report`: 评分详情（含各维度得分和去重结果）
- `used_structures`: 引用的爆款结构
- `viral_source`: "feishu_report"
- `needs_review`: 是否需人工审核

## 边界情况

- **飞书报告不存在**: 自动回退到本地 `viral_structures.json`
- **AI 调用失败**: 捕获异常，标记需人工审核
- **JSON 解析失败**: 保存原始文本，降级处理
- **评分器异常**: 跳过评分，直接保存
- **无历史内容**: 去重维度自动满分

## 与 viral-element-analyzer 的关系

- `viral-element-analyzer`: 采集趋势数据 → 提取爆款结构 → 更新飞书报告
- `viral-copy-factory`（本skill）: 读取飞书报告 → 生成内容 → 评分优化

两个 skill 共享 `data/feishu_viral_report.md` 和 `data/viral_structures.json`。
先跑 viral-element-analyzer 更新爆款密码，再跑 viral-copy-factory 生成文案。
