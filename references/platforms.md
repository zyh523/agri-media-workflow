# 抖音与小红书的独立适配

以下是制作初值和验证方法，不是最新平台算法或接口保证。正式操作时读取当前官方创作规范、AI/演绎/广告标识说明、目标账号后台提示与实际上传预览，记录 URL、访问时间、账号适用范围；无法验证的字段写未知，不能编造接口或限制。平台规则发生变化时更新运行目录记录，不自动改 Skill 源文件。

## 平台适配表

| 项 | 抖音初始策略 | 小红书初始策略 |
|---|---|---|
| 入口 | 先试清楚的首帧和实际动作；看后台留存后调整 | 先试能检索的问题词和信息封面；看后台搜索和打开数据后调整 |
| 文案 | 一句主承诺，条件前置，口播与镜头对应 | 让标题/封面/正文构成可保存的条件清单或过程索引 |
| 制作 | 可从竖屏 9:16、1080×1920 母版试作，上传要求现场核对 | 使用同一母版须重新检查封面裁切、文字区和笔记预览；不把图文规范当视频规范 |
| 测量 | 以后台实际可取的播放、留存、关注等为准 | 区分曝光、打开/播放、收藏和搜索；以字段官方定义为准 |
| 评论 | 按作品目标判断技术、共鸣或购买需求 | 同样按实际需求分类，收藏高不自动代表成交 |

这些是基于用户报告和运营设计的待验证假设，不等于“抖音只娱乐、小红书只干货”。同题可用不同包装，但各自有独立 payload、审核、发布记录和定窗数据。不可为了跨发省略技术条件。

## 连接器契约

对每个真实账号记录以下能力及证据：

```text
read_identity → platform, account_id, display_name, scopes, checked_at
read_policy → upload limits, disclosures, prohibited categories, source, checked_at
create_draft → remote_draft_id, preview, raw_receipt
submit_or_schedule → remote_job_id/post_id, status, receipt
get_status → processing/review/published/rejected/unknown, evidence
list_recent_posts → ids, times, metadata, coverage boundary
read_metrics → raw fields, definition, window, captured_at, source
```

这是适配要求，**不是已经实现的 API**。不支持某项就降级到可用界面或明确缺口。平台只支持人工最终提交时，准备好草稿、预览、参数和用户待办；不能声称完成发布。浏览器使用应遵守当前平台和宿主约束，遇登录/验证交用户。

## 指标映射

保留 `raw_metric_name, normalized_name, definition, numerator, denominator, window_hours, captured_at, source`。图标未标含义、数值未显示时写 null 和原因；不猜成收藏/分享。字段叫点击不一定是作品点击，播放次数不等于独立观众。

CTR 仅在有**同口径内容点击与对应曝光**时计算；若后台提供视频播放但无点击，不能用播放/曝光冒称 CTR。平台自带 CTR 优先保留其原始定义。完播率、平均观看时长和互动率也要保留实际分母；无法确认则只报告计数。

一个平台的 24h 和另一个平台的 7d 不横比；跨平台优先比各自同类基线的相对表现，不能因绝对计数大就称策略更优。广告与自然、置顶与普通、图文与视频分层，官方未给可比定义时保留并列展示。
