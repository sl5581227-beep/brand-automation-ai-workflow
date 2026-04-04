---
name: Cost-Tracker
description: 跟踪即梦AI使用成本，支持配额管理和成本统计。
trigger: 成本统计|配额管理|费用追踪
---

# Cost-Tracker v4.1

## 功能

1. 记录每次即梦AI调用
2. 计算预估费用
3. 每日/每周汇总
4. 配额阈值警告

## 价格参考（即梦AI官网）

- 视频生成：约 0.5元/秒（5秒片段 ≈ 2.5元）
- 以实际官网价格为准

## 使用方式

```python
from cost_tracker import CostTracker

tracker = CostTracker()
tracker.record(
    product_id="qingshang_coconut_water",
    duration_seconds=5,
    generation_time=120
)

# 检查配额
if tracker.check_quota():
    print("配额充足")
else:
    print("超出配额，暂停任务")
```

## 日志文件

- `logs/cost_daily.json` - 每日汇总
- `logs/cost_weekly.json` - 每周汇总
