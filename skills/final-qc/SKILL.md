---
name: Final-QC
description: 对成片进行多维度质量评估(技术/流畅度/一致性/吸引力)，输出0-100综合分数和详细报告。
trigger: 评估成片|质量检测|视频打分|成片质检
---

## Instructions

1. **接收输入**
   - 视频文件路径
   - 脚本原文（用于一致性检查）

2. **评估维度**（每项0-100分）

   | 维度 | 权重 | 说明 |
   |------|------|------|
   | 技术质量 | 30% | 清晰度、噪点、压缩伪影 |
   | 运动流畅度 | 20% | 卡顿、跳帧检测 |
   | 文本-视频一致性 | 30% | 视频内容是否符合脚本描述 |
   | 吸引力 | 20% | 预测完播率 |

3. **调用MiniMax Video-01 API**
   ```python
   response = minimax.video_analyze(
     video_url=video_path,
     tasks=["quality", "motion", "consistency", "engagement"]
   )
   scores = response["scores"]
   
   final_score = (
     scores["technical"] * 0.3 +
     scores["motion"] * 0.2 +
     scores["consistency"] * 0.3 +
     scores["engagement"] * 0.2
   )
   ```

4. **生成报告**
   - 保存到 `metadata/final_reports/{tracking_id}_report.json`
   - 更新 `final_db.json` 中的 quality_score

5. **输出**
   ```
   🎬 成片质量评估报告
   
   **追踪码：** md5_hash
   **综合得分：** 82/100
   
   详细评分：
   ├── 技术质量：85/100 (30%) ████████░░
   ├── 运动流畅度：78/100 (20%) ███████░░░
   ├── 文本-视频一致性：85/100 (30%) ████████░░
   └── 吸引力：80/100 (20%) ████████░░
   
   **评估结论：** 合格，建议投放
   
   **报告保存：** metadata/final_reports/xxx_report.json
   ```

## 评估标准

| 分数区间 | 等级 | 结论 |
|----------|------|------|
| 90-100 | A+ | 优秀，可直接投放 |
| 80-89 | A | 良好，可投放 |
| 70-79 | B | 可用，需小幅优化 |
| 60-69 | C | 勉强可用 |
| <60 | D | 不合格，需重做 |

## 报告格式 (JSON)

```json
{
  "tracking_id": "md5_hash",
  "video_path": "final_videos/final_xxx.mp4",
  "evaluated_at": "2026-04-03T10:45:00Z",
  "scores": {
    "technical": 85,
    "motion": 78,
    "consistency": 85,
    "engagement": 80
  },
  "final_score": 82,
  "grade": "A",
  "recommendation": "良好，可投放",
  "issues": [],
  "script_consistency": {
    "matching_scenes": 4,
    "total_scenes": 5,
    "missing_content": []
  }
}
```

## 使用示例

**用户：** "评估 final_videos/final_20260403_xyz789.mp4 的质量"

**输出：** (完整评估报告)
