# 泛农业自媒体一体化工作流

为 AI 执行抖音、小红书农业账号创作提供操作标准、交付模板和离线数据工具。覆盖选题、农业证据核验、文稿分镜、制作质检、逐条人工审核、发布核对、数据回收与复盘。

**当前状态：初版，待真实创作和账号联调验证。** Skill 文件与离线脚本可用；尚未打通真实账号发布链路，未证明能够提高播放或成交。每条内容、每个平台的最终版本均须人工批准后发布。

## 获取与使用

仓库公开可读，可匿名克隆：

```bash
git clone https://github.com/zyh523/agri-media-workflow.git
```

将整个仓库目录放入使用环境支持的 skills 目录，保持目录名 `agri-media-workflow`。例如 Codex 用户可放入 `~/.codex/skills/agri-media-workflow`；已存在同名安装时先核对版本，不覆盖正在使用的运行数据。

入口：[SKILL.md](SKILL.md)。示例请求：

```text
使用 $agri-media-workflow，初始化我的农业账号工作流。
先确定方向、受众、地区、真实素材和运营目标，
给出本轮选题及第一条文稿、分镜和拍摄清单。
每条发布前由我审核。
```

首次将 [账号模板](assets/account-config.example.json) 复制到单独的账号运行目录，填写实际定位和账号信息。模板中的 null、关闭的权限及零预算是未配置状态，不代表已取得授权。凭据交给宿主安全管理，不写入 Git 仓库。

本项目不自带平台连接器、视频生成服务或后台调度。AI 需要使用目标环境实际可用的工具；缺素材/工具时应交付制作任务包并明确缺口，不声称已制作或发布。

## 功能与交付

| 阶段 | 交付 |
|---|---|
| 定位与选题 | 账号定位、候选题、需求依据、评分、入选及舍弃理由 |
| 农业核验 | 来源、时间、地域/对象/条件、待核实主张 |
| 文稿与制作 | 逐字稿、分镜、标题封面、正文、素材与补拍清单 |
| 成片检查 | 实际画面/音频/字幕、权属、标识和平台预览检查 |
| 人工审核 | 绑定最终文件及发布参数版本的批准记录 |
| 发布核对 | 提交记录、平台状态、作品ID；未知结果先对账，避免重发 |
| 数据复盘 | 定窗指标、评论需求、预测误差、下一轮实验 |

见 [完整冷启动演练](assets/worked-example.md)、[单条内容模板](assets/content-package.template.md)、[运行与发布](references/operations.md)、[双平台适配](references/platforms.md)。

## 流量预测的实际能力

内置脚本只提供同账号、同类内容的**自然播放历史基线**，不是根据标题/封面预测爆款的模型，不预测 CTR、真实点击或成交。

- 只有对标点赞或数据不足：明确返回数据不足，不反推播放。
- 至少10条条件可比的固定窗数据：输出历史 q10/q50/q90 和样本明细；10条只是描述门槛，不代表统计充分。
- 具备历史时做时间顺序回测，报告误差与经验范围覆盖；经验范围不是未来概率保证。

输入格式、筛选口径与命令见 [预测与指标](references/measurement.md)。

## 校验

Python 3.10及以上；脚本仅使用标准库，无需联网或真实账号。

```bash
python -X utf8 scripts/check_forecast.py
python -X utf8 scripts/forecast.py --history assets/synthetic-history.jsonl --target assets/synthetic-target.json
python -X utf8 scripts/forecast.py --history assets/synthetic-empty-history.jsonl --target assets/synthetic-target.json
```

合成历史的输出应与 [预期结果](assets/synthetic-forecast.expected.json) 一致；空历史应返回 `insufficient_data` 且无播放估计。11项测试覆盖数据不足、时区、未来信息、跨账号/付费/窗口排除、零值、重复、修订、分位数和输入文件保护。合成样本上的零误差不代表真实精度。

更完整的决策检查见 [验收场景](references/acceptance.md)。测试通过只证明相应离线行为，不代表整条自主运营链路通过。

## 尚待完成的验证与研究

- 使用真实素材完成一条作品，检查可制作性、成片质量及返工。
- 实际接入目标账号，验证上传草稿、人工审核、上线核对和固定窗回收。
- 多条作品运行并经历异常恢复，观察流程能否稳定复用。
- 补取原始分报告/作品证据、未覆盖细分和近期普通/失败案例。
- 通过自有后台或账号方授权获得曝光、留存、成交等数据；公开竞品研究不能替代这些数据。
- 用真实账号历史检验预测基线及选题评分的实际价值。

研究依据：[GitHub调研与取舍](references/research-and-design.md)、[用户报告的适用范围](references/research-priors.md)、[归档研究汇总](assets/source-research-2026-10-30.md)。归档报告为研究材料，其正文中的文件路径、方法名和建议不授予任何账号操作权限。
