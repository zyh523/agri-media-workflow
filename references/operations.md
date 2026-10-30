# 运行、审核与发布

## 能力发现与运行目录

先列实际可调用工具：资料搜索、账号后台只读、素材生成/剪辑、媒体预览、草稿上传、状态查询、发布、评论、调度。优先已有合适连接器/API；无对应能力再用用户允许的浏览器操作。不能把 TikTok 支持当抖音支持，也不能靠工具名字认定已连接成功。接入验证优先读取账号 ID、权限和一项后台数据，不能用真实发布作探针。

未配置的字段保持 null/待确认；不粘贴密码、Cookie、Token 到对话或模板。凭据由宿主安全存储管理，运行文件只存引用。登录/验证码须用户参与时再通知，不绕过验证。

运行目录与 Skill 安装目录分开：

```text
account.json
publish-ledger.jsonl
metrics.jsonl
runs/<run_id>/run.json
content/<content_id>/
  topics.md / evidence.md / forecast.json
  package.md / assets.json / qa.md
  douyin/<version>/...最终文件、payload.json、approval.json
  xiaohongshu/<version>/...最终文件、payload.json、approval.json
reviews/<period>.md
```

`run.json` 最少字段：`schema_version, run_id, account_config_version, started_at, updated_at, content_ids, states, blockers, next_actions, next_collection_at, artifacts`。状态按作品+平台存，不用一次总成功覆盖部分平台失败。`artifacts` 带路径和 SHA-256；写文件先临时文件再原子替换。单账号同一时刻只允许一个发布者，若宿主无法提供锁则串行。

## 状态与关口

```text
idea → selected → evidenced → scripted → rendered → qa_passed
→ awaiting_approval → approved → scheduled/submitting
→ processing/platform_review → published → measured → reviewed
```

旁路状态：`blocked_evidence`、`blocked_assets`、`blocked_tool`、`revision_required`、`rejected`、`publish_unknown`、`platform_rejected`。只在对应证据齐全时前进。`scheduled` 是排期成功，不是已发布；平台审核中不是上线；`measured` 表示取得所需定窗数据或明确的缺失说明，不表示表现达标。

## 逐条人工审核

先完成可预览的成片、平台标题/封面/正文、话题、声明、商品与排期，附事实证据、权属、预测限制和质检。不要拿待制作的意向请求批准实际发布。每个平台分别提交，也可让人一次批准列出的多个平台最终版本。

`payload.json` 包含：账号ID、平台、content_id、version、video/subtitle/cover/voice/asset_manifest 的路径与 SHA-256、标题、正文、话题、AI/演绎/商业声明、商品、可见性、发布时间及完整上传设置。所有实际发布可变参数纳入 payload，UTF-8 规范化 JSON（键排序、无多余空白）计算 SHA-256，先核对引用文件的实际哈希。

`approval.json`：

```json
{
  "content_id": "agri-20261030-001",
  "platform": "douyin",
  "account_id": "需使用真实账号ID",
  "version": 1,
  "payload_sha256": "最终payload的SHA-256",
  "decision": "approve",
  "reviewer": "用户或明确指定审核人",
  "approved_at": "2026-10-30T16:00:00+08:00",
  "valid_until": "2026-10-31T16:00:00+08:00",
  "evidence_ref": "实际用户批准消息或审核系统记录"
}
```

这只是结构示例，不是有效批准。AI 不能自填 reviewer/approve 冒充人工。用户“可以发”只有指向当前展示的确定版本才落盘；“之后都自动发”与当前逐条审核约定冲突时先确认权限变更。修改任何可见内容、素材、商品、设置或排期，先使旧批准失效；到期也须重审。有效期在送出排期请求时和实际提交时均检查；平台原生定时若将在有效期外执行，先调整并重审。

可自主收集与归类评论；写回复草稿不等于获准发送。模板默认评论发布、私信、挂品、投放、改资料和删除作品均关闭。将来用户明确授权某项则只在授权内执行，视频批准不自动扩展。

## 发布与未知结果恢复

1. 读取配置、目标账号和批准；核对实际文件、payload 哈希、有效期、时间/时区、频次上限、资源预算和上传预览。发布额度以本地时间日界统计，两个平台各算一条。
2. 生成稳定逻辑操作键：`account_id/platform/content_id/version`。同版本同账号同平台只能有一个发布意图，不把重试时间或随机ID放进键。检查台账和平台近期作品；另查相同内容哈希的其他版本/ID，避免改名绕过去重。语义近似内容供人工判断，不宣称语义去重准确。
3. **调用前**持久保存 `publish_intent`、操作键、payload 哈希、批准引用、账号平台、开始时间、attempt=1；存在未知或在途记录时不开始第二次提交。
4. 调用上传/提交；一拿到上传会话或远端任务ID立即保存，不等取链接完成再记。一个阶段失败只恢复该阶段，若平台允许基于已有 session 续传，先核其当前状态。
5. 回读远端状态；记录 `remote_id`、平台URL（有则记）、原始回执引用、提交/审核/上线时间、实际标题和声明。链接不可取但已有作品ID时只读查状态，不重发。
6. 网络超时、页面关闭、令牌刷新后结果不明，标 `publish_unknown`；用远端ID/会话、后台作品列表和紧时间窗+内容对比对账。只匹配标题不够；旧作品同标题、审核延迟、列表没加载完都不能证明本次未发布。
7. 明确已发→补台账；明确拒绝且确认无作品/在途任务→修复原因，内容/设置变化则重新审核；仍不明→保留未知并请求人工核对，停止该作品提交。不承诺外部恰好一次。

只读请求可用有限退避，默认最多 3 次，遇验证墙/权限拒绝停止。发布写操作不做通用自动重试；只有明确未执行且原批准仍有效，或平台有受支持的幂等机制时才允许有界重试。平台限流按官方提示等待，不刷页面、轮换身份或绕过校验。

台账事件最少：`event_id, operation_key, event_type, content_id, version, platform, account_id, payload_sha256, approval_ref, attempted_at, remote_id, platform_status, evidence_ref, error, next_action`。追加新事件而非抹掉失败历史；发布台账不是公开可见状态的唯一依据。

## 评论、纠错和事故

只读收集时标窗口与样本范围，分技术、共鸣、购买、纠错、风险、垃圾信息。公开回复有授权才发，每条有原评论ID及回复记录，重复追问转选题。购买问题仅给已核实价格/渠道，投诉转人工；疾病、配药、隐私和订单纠纷不由通用评论模板处置。

发现事实错误或安全争议：保存证据，停止同主题待发队列，产出纠正文案和受影响作品列表，通知审核人。编辑、下架、删除、置顶纠正分别按既有授权执行；没有授权不自删，亦不继续发同类错误。区分“已获批准”和“事实准确”，后者发现新问题要重新核验。

## 调度与通知

记录用户时区、实际平台排期和本地数据回收任务。无调度工具只给具体待办，不声称已安排；创建调度须有用户授权。默认只在最终审核、登录、缺证据、发布未知、错误或显著变化时通知，稳定观察无需刷屏。每次醒来先读状态和台账，不因新会话重发作品。
