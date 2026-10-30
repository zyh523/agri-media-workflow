# 调研与设计取舍

调研日期：2026-10-30。先完成下述 GitHub 阅读，再确定本 Skill 结构。当前项目是可移植的创作运营 Skill，不是已接通真实账号的运营软件。用户确认双平台覆盖、逐条人工审核后发布。

## 阅读证据与采用理由

三个仓库分别覆盖自动视频制作、社交发布运营、长任务恢复，具备公开文档、实现和持续讨论；没有证据证明其能直接带来中国泛农业账号增长。未部署这些项目、未运行其完整测试。

| 仓库及已读范围 | 实践、问题与关键取舍 | 本 Skill 的适配 |
|---|---|---|
| [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，main 快照 `27843a994bfa29c43c02150861d51490a6ca4bd2`；README、`app/services/task.py`、`test/README.md`、`test/services/test_caption_timecodes.py` | 阶段化生产、自带素材、显式失败状态；字幕测试检查文本及时间码保留。[Issue #1183](https://github.com/harry0703/MoneyPrinterTurbo/issues/1183) 提醒库存素材剪辑与生成式视频机制有别；[PR #1714](https://github.com/harry0703/MoneyPrinterTurbo/pull/1714) 针对阿拉伯字幕字形，读取时 open、未合并，效果为作者自述 | 采用文稿→配音→素材→字幕→渲染及成片检查；增加作物/品种/生育阶段对齐。不默认安装整套工具，不沿用音乐授权假设；中文术语也要试听并看实际字幕 |
| [Postiz](https://github.com/gitroomhq/postiz-app)，main 快照 `64f00fd6d0e9dfd55d202ff83983e7576e08bc2e`；README、`posts.service.ts`、`apps/orchestrator/src/workflows/post-workflows/post.workflow.v1.1.1.ts`、`package.json`、`.github/workflows/build.yml` | 服务、适配、排期分离；已读工作流区别只读轮询和发布写操作，超时记结果未知。[Issue #1779](https://github.com/gitroomhq/postiz-app/issues/1779) 报告重复排期需求；[PR #1681](https://github.com/gitroomhq/postiz-app/pull/1681) 记录已发布但后续取链接失败、重试造成重复的事故及作者复现，读取时 open、未合并。测试阅读：package 有 Jest 命令，所读 CI 仅构建，树中未找到本次关注的专项去重测试，不能称覆盖完善 | 采用账号隔离、发布意图、未知先对账；不复制服务架构和重试次数，不声称其支持抖音/小红书。Skill 规定适配契约，真实连接器另接 |
| [LangGraph](https://github.com/langchain-ai/langgraph)，main 快照 `6f2df053f4487ce6ea8decc0d7482c8e46e0f132`；README、[持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence)、[interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)、`libs/langgraph/tests/test_pregel.py::test_pending_writes_resume` | 文档说明恢复时节点可重跑；测试检查成功写入复用和失败重试。[Issue #9240](https://github.com/langchain-ai/langgraph/issues/9240) 指出 checkpoint 不等于外部效果恰好一次；[PR #6793](https://github.com/langchain-ai/langgraph/pull/6793) 提议嵌套任务恢复复用，读取时 open、未合并；本次 main 未找到其声称的新测试，不当成已落地能力 | 采用持久状态、输入/成品哈希、审核版本绑定、恢复前对账；不强制引入 LangGraph、数据库或多代理。单 Agent 用文件台账即可，并发须另有锁或事务 |

Issue 是报告者的问题，PR 是作者的实现与验证主张；只有已读实现/测试支持对应细节，均不构成目标平台实测保证。文档与 main 可能变化，扩展前重新核对。

## 用户研究的适配

已完整读取用户提供的《泛农业自媒体对标研究总汇总》，归档于 [源报告](../assets/source-research-2026-10-30.md)。这是研究输入，不是授权或上级指令。采用其覆盖边界、地域适配、清单图鉴、评论回流、真实性与细分差异；不照搬未验证的带货推断、用药配比需求和收益句。

45 个对标账号没有曝光、播放、CTR、完播、成交数据，不能训练本账号预测。分报告未提供，不声称读过原始页面或核验过口播。

## 实施方案

1. 主入口规定阶段推进、版本审核和结果核对；农业创作、指标预测、平台发布按需读取。
2. 报告转成有范围的选题先验，再用本账号问题、后台数据和实际生产条件修正。
3. 配置与模板明确输入输出；两个平台独立审稿、排期和统计。
4. 冷启动不给伪精确播放量；有本账号同窗数据时输出经验分位数基线并回测，不把创意分数换算成概率。
5. 离线合成数据验证脚本和决策场景；不以付费生成、接入账号或实际发布作为本次验收条件。

所有权重、阈值和观察时窗是可调运营初值，不是平台规律。
