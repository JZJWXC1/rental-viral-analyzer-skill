# 租房爆款分析 Skill

QoderWork Agent Skill，用于从小红书/抖音趋势数据中自动采集高互动帖子，AI 分析提取爆款内容结构（标题模板、开头钩子、正文结构、标签策略），存储到本地结构库并同步到飞书云文档。

## 功能

- 自动读取 `data/trending/` 中的趋势帖子数据
- 按平台阈值筛选高互动帖子（小红书 500 赞、抖音 1000 赞）
- 调用 Qwen AI 提取 3-5 个爆款内容结构
- 按 id 去重合并到本地 `viral_structures.json`
- 生成 Markdown 报告并通过 lark-cli 推送到飞书文件夹

## 目录结构

```
├── SKILL.md                          # Skill 指令文档
├── scripts/
│   └── collect_and_analyze.py        # 数据采集与分析脚本
└── README.md
```

## 使用方式

安装到 QoderWork 后，对 Agent 说以下关键词即可触发：

- "采集爆款元素"
- "更新爆款结构库"
- "分析趋势数据"
- "viral analysis"

## 依赖

- Python 3.12+
- 项目配置文件 `config.yaml`（含 DashScope API Key）
- lark-cli（飞书文档同步）
