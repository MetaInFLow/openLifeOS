---
name: openlifeos
description: openLifeOS 是长期人格与认知成长系统，用于把一个人的人格、技能、审美、经历、认知碎片和长期记忆沉淀为持续成长、持续连接、持续进化的长期智能核心。适用于自我理解、问心、PSP XML 建模、IPO 逆向复盘、Skill 蒸馏、长期记忆、审美偏好、人生经历沉淀、Dream Loop 复盘、知识重组、人格进化和主动对齐。
---

# openLifeOS

## Persistent Lifelong Intelligence Kernel

openLifeOS 是一个长期人格与认知成长系统。

它不是一次性 AI 聊天工具，而是人的长期认知与人格操作系统：把人格、技能、审美、经历、认知和长期记忆沉淀为一个会持续成长的智能核心。

## 运行原则

- 把 openLifeOS repo 当作长期智能核心的公开或半公开接口，不要当成原始私人资料库。
- 把当前 openLifeOS repo 当作 factory：协议、模板、脚本和校验门禁留在 root；具体数字分身实例默认生成到 `output/meta/<Target.LifeOS>/`。
- `output/meta/` 是本地产物区，生成内容默认不入仓；只有模板、脚本、references 和治理规则属于 factory 本体。
- 不编造履历、私人上下文、人格特征、客户、工作经历、语言指纹或未经验证的人格结论。
- 原始材料尽量留在原系统，只提交公开事实、授权证据、摘要索引或抽象后的不可逆结论。
- Memory 隔离采用三层规则：public surface 只放可开源派生产物，private collaboration 放可信协同记忆，local/server authority 保留原始敏感材料；具体规则见 `references/memory-isolation-model.md`。
- Skill 分 runtime skill 和 distilled meta skill：runtime skill 负责执行并产生证据，distilled meta skill 负责沉淀可复用判断；升级必须经过 IPO Reverse 复盘和 owner alignment，具体规则见 `references/skill-taxonomy-and-promotion.md`。
- 认知对象必须强分型：memory 只保存 declarative facts/claims/preferences，Skill 只保存 reusable procedure/judgment；混合材料写入前必须拆成 memory object + skill proposal，并通过 binding 关联。具体规则见 `references/cognition-object-taxonomy.md`。
- 区分“确定性骨架”和“基于证据生成的产物”：骨架定义路由，产物填充 identity、PSP XML/person model、技能、审美、经历和记忆。`SOUL.md` 当前暂停作为 LifeOS 源产物生成。
- 核心过程产物必须有 latest registry、current entrypoint 和 timestamped version：统一 latest 入口是 `artifacts/current.yml`；identity 层 active 入口是 `identity/current.yml`；产品/UI 默认读取的当前分身描述入口是 `identity/avatar-description/current.yml`。
- 用户未指定 visibility 时，默认 `local-only`；发布远端前需要用户明确确认。
- 当前工具链保留 `replicateme.yml`、`scripts/*avatar*` 等兼容性接口；语义上它们用于初始化 openLifeOS 的个人长期智能核心骨架。
- LifeOS lifecycle 和初始化 gate 分开：初始化 gate 判断骨架/协议/权限/入口是否齐；Stage 0-8 判断数字生命从 target seed 到 living system 的活跃度、成熟度和年龄。
- 当前结构契约是 LifeOS schema v2，入口为 `schemas/lifeos.schema.v2.yml`。v2 顶层只允许 lifecycle layers、governance layers 和 `legacy/`；`agents/`、`apps/`、`profiles/`、`scripts/`、`design/`、`life/`、`system/` 等 v1/v1.5 顶层必须迁移或归入 `legacy/`。
- schema 版本迁移必须走 `migrations/`：确定性文件移动、入口重命名和路径重写用 `scripts/migrate_lifeos_schema.py <LifeOS> --to latest` / `migrations/versions/*.py`；脚本按 `schema_revision` 像 Alembic 一样顺序补齐缺失 revision，并写入 `legacy/migration-reports/`。需要语义判断的新格式转换用 `migrations/skills/*/SKILL.md` 声明输入、输出和输出 schema。
- Session/runtime 是 LifeOS 活动源头。标准数据流是 `metabolism/inbox -> runtime/sessions -> runtime/runtime-skills -> runtime/runtime-lessons -> evolution/ipo -> capabilities`。
- 生成 repo 的一等 lifecycle layers 是 `identity/`、`metabolism/`、`runtime/`、`evolution/`、`capabilities/`、`identities/`、`work/`；`integrations/`、`security/`、`docs/`、`artifacts/` 是兼容和治理层。
- 用户侧入口保持简单：用户只需要要求“使用 $openlifeos 初始化我的 LifeOS”。初始化、配置、脚手架、进度判断和下一步推进由 agent 驱动。
- 用户个人输入可以走 TUI：`scripts/tui_avatar_config.py` 会引导填写 GitHub 权限、Feishu/Lark 权限、memory wiki、公开边界和推荐 Skill domain。不要让用户在 TUI 中输入任何 secret。
- 每轮交互必须先告诉用户当前阶段、这一阶段在做什么、这阶段需要/不需要什么材料、产出物会写到哪里。不要直接问“给我资料”；先说明资料将用于 Wenxin、PSP、memory、Skill recommendations 还是公开 profile。
- 支持匿名身份：`identity_mode=anonymous` 时，repo 名可以完全自定义，`display_name` 可以是公开标签，`psp_display_name` 是 PSP 化名，`person_id` 从化名生成或由用户指定。匿名模式下不要追问真实姓名，不要从本机上下文或外部 personal Skill 推断真人身份。
- 生成物中的认知对象契约放在 `identity/cognition/`，memory 分层放在 `identity/memories/`、`runtime/memory/` 和 `capabilities/*/memory/`，能力分层放在 `runtime/runtime-skills/`、`identity/wenxin/skill-summaries/` 和 `capabilities/`。
- 完整 self-evolution 生产系统安装在 `evolution/organ-systems/`，其中 `wenxin`、`psp`、`ipo-reverse` 和 `taste-generator` 来自各自 GitHub skill repo；`integrations/skill-sources/default-skills/` 只保留 openLifeOS bridge/兜底说明，不放同名副本。用户后续蒸馏出来的个人 runtime/meta skills 先进入 `runtime/runtime-skills/` 或 `identity/wenxin/skill-summaries/`；稳定后经 IPO/owner alignment 进入 `capabilities/`。需要事实和外部数据时通过 `identity/cognition/skill-bindings/` 声明，不写死进 `SKILL.md`。
- LifeOS 必须有根级 `LIFEOS_STATUS.yml` 作为全局状态标志。`development` 状态用于开发/上传版本，meta skill 可以是 submodule 或 editable working source；`delivery` 状态用于交付/消费版本，meta skill 应从 latest approved release archive 下载为普通 vendored 目录，并记录 source manifest。`DELIVERY.md` 是人类说明，`LIFEOS_STATUS.yml` 是机器可读真相源。
- `docs/skill-system/runtime-skill-candidates.md` 和 `identity/wenxin/skill-summaries/` 默认只是实例内能力层或候选 Skill，不等于 Codex 全局可发现/可安装 Skill。若要提升为可安装 Skill，必须迁移到独立 skill 包或安装目录，并在生成 avatar 的根 `AGENT.md` / `matrix.yml` 中建立绑定。
- 初始化和 synthesis 必须维护 `docs/evidence-sufficiency.md`。`openlifeos_progress.py` / `doctor_avatar_repo.py` 的 100% 只代表结构/协议门禁通过，不代表 LifeOS 内容成熟、人格成熟、能力成熟或 Stage 8；Output Gate 必须报告 maturity level、资料缺口、失败来源、未完成区域，以及 lifecycle stage/age。
- 新建 avatar 的 Evidence Intake 默认不得把本地 factory 的 `output/meta/`、其他 avatar repo、历史 `identity/wenxin/` / `identity/inneratlas/` 报告或旧问心结论当作原料。只使用用户本轮直接提供的材料，或用户明确授权的外部资料入口和限定范围；如果用户授权本地目录，默认排除 `output/meta/`。
- 内置生产系统更新配置写入 `integrations/skill-sources/default-skills/skill-updates.yml`，实例级历史更新脚本归入 `legacy/scripts/`；factory 级更新脚本保留在 root `scripts/`。更新必须先从 GitHub latest/ref 拉取到临时目录、生成 diff、经 owner 确认后再覆盖。

## 核心结构

### Persona｜人格

通过 PSP、问心、长期行为和决策模式分析，形成 PSP/person model。PSP XML 是人物模型源产物，固定承载本体九维、运行轴、授权边界、判断/表达模型、证据成熟度和 runtime 指令；`SOUL.md` 当前暂停作为 LifeOS 源产物生成，如目标 runtime 需要只能作为投影。

### Skills｜技能体系

通过问心、长期行为、工作流和重复动作发现长处、潜在能力、长期重复行为和方法论，沉淀为 Personal Skill System。

### Aesthetics｜审美系统

持续理解一个人喜欢什么、如何表达、审美结构与设计偏好，沉淀为全局 `DESIGN_TASTE.xml` 和 `DESIGN.md`。它不是项目 UI 配置，而是全局表达偏好和审美判断入口。`DESIGN_TASTE.xml` 是机器可读源产物，固定承载 reference choices、design variables、颜色、文字颜色、字体、字号、间距、栅格、布局、形状、深度、组件、导航、动效、媒体、证据呈现、可用性、响应式、do/don't、反偏好和迭代缺口；`DESIGN.md` 是从 XML 生成的人类/agent readable projection。标准生成机制是 Taste Generator：从 taste option 池和具体场景（如 personal website）生成 iframe 选择页，让 owner 标注 like/maybe/avoid，并选择字体、颜色、文字颜色、间距、栅格、圆角、动效、媒体、导航、可用性、证据呈现等变量，汇总选择和依据后先写 timestamped XML，再生成 timestamped Markdown 与当前入口。

### Artifacts｜过程产物与版本

每个生成实例必须维护：

- `artifacts/current.yml`：所有核心过程产物的统一 latest registry。
- `identity/current.yml`：identity 相关产物的 active registry。
- `identity/avatar-description/current.yml`：产品、UI 和 Runtime Handbook 默认读取的当前数字分身结构化描述；它总结 Wenxin、PSP XML 和 Design，不替代这些证据产物。
- `identity/inneratlas/current/INNERATLAS_REPORT.xml` + `identity/inneratlas/versions/INNERATLAS_REPORT.<timestamp>.xml`：InnerAtlas（问心）/identity source-of-truth；`identity/wenxin/` 只保留兼容 ledger、公开派生摘要和 Skill recommendations。
- `identity/psp/<person_id>/current/PSP_REPORT.xml` + `identity/psp/<person_id>/versions/PSP_REPORT.<timestamp>.xml`：PSP/person model 源产物。
- `identity/psp/<person_id>/current/EVIDENCE_MATURITY.xml` + `identity/psp/<person_id>/versions/EVIDENCE_MATURITY.<timestamp>.xml`：PSP 证据成熟度源产物。
- `SOUL.md`：暂停作为 LifeOS 源产物；runtime 适配可从 PSP XML 生成目标 runtime 投影。
- `identity/design/current/DESIGN_TASTE.xml` + `identity/design/DESIGN_TASTE-<timestamp>.xml`：全局审美系统源产物。
- `DESIGN.md` + `identity/design/DESIGN-<timestamp>.md`：由 DESIGN_TASTE XML 生成的人类/agent readable 投影。

更新规则：先写 timestamped artifact，再更新 current entrypoint、versions ledger、changelog、相关局部 registry 和 `artifacts/current.yml`；如果更新改变“当前分身是什么样”，同步刷新 `identity/avatar-description/current.yml`；不得静默覆盖 current 文件。

### Experiences｜经历与履历

通过长期项目、工作行为、学习记录、阅读内容、任务碎片和人生经历，持续理解一个人真正经历了什么。

### Lifecycle｜数字生命阶段

Stage 0-8 是数字生命生命周期，不是初始化进度条。

```text
metabolism/inbox
-> runtime/sessions
-> runtime/runtime-skills
-> runtime/runtime-lessons
-> evolution/ipo
-> capabilities
```

- Stage 0：刚初始化，只有身体结构。
- Stage 1-3：授权材料进入，Wenxin 形成自我认知，PSP 形成思考/判断/表达模型。
- Stage 4-6：session 真实发生，runtime skills 和 runtime lessons 开始形成。
- Stage 7-8：完成产物经 IPO Reverse 复盘，稳定能力进入 `capabilities/` 或进一步形成 Meta Skill。

`runtime/sessions/` 是判断 LifeOS 是否“活着”的核心证据；`capabilities/` 只接收经过 review、边界清楚、可复用的稳定能力。

## 核心循环

### Day Loop｜现实循环

人在现实世界中工作、阅读、学习、沟通、思考和创作，持续产生 Cognitive Fragments：

- 飞书消息。
- 某次任务中的思考。
- 公众号文章。
- 博客片段。
- 阅读感悟。
- Lessons。
- Insights。

### Dream Loop｜梦游循环

openLifeOS 在周期性复盘中执行：

1. **Reflection｜反思复盘**：通过 PSP、问心和 IPO Reverse 回顾行为、理解决策、总结经验、检查人格变化。
2. **Knowledge Relinking｜知识重组**：发现隐藏关联、打新标签、建立新 link、形成新的认知结构。
3. **Skill Evolution｜技能进化**：发现正在增长的 skill、正在形成的方法论和长期重复行为，并迭代 skill。
4. **Identity Evolution｜人格进化**：观察兴趣、决策、人格和长期目标变化，持续更新 PSP XML/person model。
5. **Active Alignment｜主动对齐**：主动发现新方向、新兴趣、新能力和新模式，并向用户提出对齐问题。

IPO Reverse 是复盘和 Dream Loop 的核心 self-evolution skill：从已完成产出物反推证据、隐性认知任务、方法论选择、中间思考资产和最终 IPO，用于沉淀 SOP、训练材料、Skill 蓝图和下一轮行动假设。

## 快速开始

当用户要创建新的 openLifeOS repo：

1. 先把自己当作初始化 driver，而不是把脚本清单交给用户。用户只需要给目标、材料范围和边界。每次开始前先输出阶段说明和正式启动介绍。
2. 收集或推断最小字段：
   - `repo_name`：通常是 `<Name>.Skill`、`<Name>.LifeOS` 或用户指定名称。
   - `identity_mode`：`named` 或 `anonymous`。用户说匿名、化名、不要暴露真实身份时使用 `anonymous`。
   - `owner_name`：长期智能核心代表的人、团队或组织；匿名模式可用 `Anonymous Owner` 或用户给的非真实标签。
   - `display_name`：对外/本地显示名；匿名模式可用公开标签。
   - `psp_display_name`：PSP/person model 使用的名字；匿名模式应使用化名。
   - `person_id`：用于 `identity/psp/<person_id>/` 的稳定 slug。
   - `github_owner`：如果之后要发布远端，对应 GitHub 用户或组织。
   - `visibility`：`public`、`private` 或 `local-only`。
   - `language`：`zh-CN` 或 `en-US`，默认 `zh-CN`。
   - `process_log_language`：过程日志语言，默认跟随 `language`；如果使用人的交互语言和产物语言不同，可以单独设置。
3. 推荐走配置链路，必要时由 agent 自己运行：

```bash
python scripts/tui_avatar_config.py --output replicateme.yml
python scripts/apply_avatar_config.py replicateme.yml
```

如果 YAML 里要求创建 GitHub 远端或 memory wiki repo：

```bash
python scripts/apply_avatar_config.py replicateme.yml --install-tools
gh auth login
python scripts/apply_avatar_config.py replicateme.yml --create-remotes
```

也可以直接生成骨架：

```bash
python scripts/init_avatar_repo.py output/meta/Target.LifeOS \
  --owner-name "Target Owner" \
  --display-name "Target Owner" \
  --identity-mode named \
  --psp-display-name "Target Owner" \
  --person-id target-owner \
  --github-owner MetaInFlow \
  --visibility local-only \
  --language zh-CN
```

英文 Skill 使用 `--language en-US`。

## 初始化 Driver 协议

openLifeOS 初始化不是一次脚手架生成，而是一个带进度判断的 agent-driven loop。

### 正式启动介绍模板

当用户说“使用 $openlifeos 初始化我的 LifeOS”或“开始启动流程”时，先输出：

```text
当前阶段：Target Gate。

我们现在在做什么：
- 先确认要为谁/哪个身份初始化 LifeOS。
- 只确定实名/匿名、repo 名、display name、PSP 化名、person_id、visibility 和语言。
- 这轮不需要个人资料、secret、私密正文或外部 personal Skill。

接下来的步骤：
1. Target Gate：确认目标身份。匿名模式可自定义 repo 名，并为 PSP 设置化名。
2. Boundary Gate：确认 local-only/private/public、禁入材料和 secret 策略。
3. Kernel Scaffold：生成 LifeOS 骨架、安装完整 PSP/Wenxin/Taste Generator self-evolution skill repo，并保留 default bridge skills。
4. Evidence Intake：解释材料用途，只接收 owner-approved evidence。
5. Synthesis：生成或更新问心、PSP、DESIGN.md、IPO Reverse 复盘、Skill recommendations 和 memory index。
6. Progress Gate：输出哪些步骤已完成、哪些还 open、下一步是什么。

四个 self-evolution Skill：
- 问心 Wenxin：回答“我是谁、我站在哪、离领域完整版差多少、我该往哪走”。
- PSP：把授权材料沉淀成人物模型、行为边界、置信度和验证样例；匿名身份使用 PSP 化名。
- IPO Reverse：从已完成产出反推证据、隐性认知任务、中间思考资产和可复用 IPO，用于升级 Skill/SOP。
- Taste Generator：生成场景化审美选择页，汇总 owner 的 like/maybe/avoid 和字体/字号/颜色/强调色/文字颜色/密度/间距/栅格/形状/动效/媒体/导航/可用性/证据呈现等变量，先更新 `DESIGN_TASTE.xml`，再生成全局 `DESIGN.md`。
```

每次初始化或更新时，agent 按这个顺序工作：

0. **Stage Notice**：先告诉用户“当前阶段是什么、我们在做什么、为什么需要这些输入、这轮不需要什么”。示例：`当前阶段：Target Gate。我们只确定 LifeOS 目标、实名/匿名、repo 名和 PSP 化名；这轮不需要个人材料。`
1. **Target Gate**：确认生成谁的 LifeOS，是否匿名，repo 名、display name、PSP 化名、person_id 和语言。匿名模式只使用用户给的标签/化名，不反推真实身份。
2. **Boundary Gate**：确认公开/私密边界、禁入材料、repo visibility 和 secret 策略。
3. **Kernel Scaffold**：在 `output/meta/<Target.LifeOS>/` 生成或更新 `AGENT.md`、`matrix.yml`、`agents/openai.yaml`、`artifacts/current.yml`、`DESIGN.md`、identity、PSP XML、metabolism、runtime、evolution、capabilities、identities、security、docs 和 integrations 层，并 best-effort 安装完整 PSP/Wenxin/Taste Generator self-evolution organ system。
4. **Evidence Intake**：只接收用户授权材料，先进入 `metabolism/inbox/` 或外部授权源索引，再抽取公开事实、认知碎片、经历、skill 证据和审美偏好。进入本阶段前必须说明每类材料用途：公开事实用于 profile，行为/判断样本用于 PSP，项目/产出用于 IPO Reverse 和 capability，审美样本用于 design/aesthetics，长期资料入口用于 memory index。新建 avatar 默认不读取 `output/meta/`、其他 avatar repo 或历史 Wenxin/InnerAtlas 报告。
5. **Synthesis Pass**：更新 Wenxin/identity、PSP XML/person model、`runtime/sessions` 派生 lesson、`evolution/ipo` 复盘产物、skill recommendations、capability map、memory index、design/aesthetics 和 active context。
6. **Progress Gate**：运行进度判断脚本，输出结构完成度、lifecycle stage/age、内容成熟度、资料缺口和阻塞项。脚本做确定性结构检查、生命周期启发式，并按 InnerAtlas、PSP、Skill recommendations、avatar-description 和 Design 的固定产物结构返回 `skill_content_maturity`；它不是事实真伪或人格结论的最终语义裁判。
6.5. **Skill Review Gate**：当需要判断“关键产出是否真实可靠、下一步该补什么”时，由本 Skill 读取 `artifacts/current.yml`、doctor JSON 的 `skill_review_surface` / `skill_content_maturity`、`docs/evidence-sufficiency.md`、`docs/self-evolution-output-standards.md`、Wenxin、PSP XML、Design 和 skill recommendations，人工语义 review 后写入 `docs/lifeos-content-review.md`。不得把事实真伪、owner alignment 和下一步策略完全下放给纯脚本启发式。
6.6. **Owner Alignment Gate**：当 `evolution/alignment/current.yml`、review 文档或任一 artifact 标记 `pending-owner-response`、`interaction_needed`、`owner_confirmation_required` 时，不能只生成问卷、HTML 或 review packet 后结束。必须在当前对话中主动提出 1-8 个自包含问题，问题内写完整 claim、选项、上下文和回答方式；不得要求用户“结合报告/上文回答”。如果用户已直接回答，先写 response artifact，再按版本规则更新相关 read model 或 source artifact。
7. **Output Gate**：必须产生真实产出，例如工作推进、决策建议、统筹计划、复盘报告、skill 迭代或方向澄清；同时必须披露 `docs/evidence-sufficiency.md` 中的 maturity level、使用/失败来源、未完成 LifeOS 区域，以及候选 Skill 是否只是实例内文件。若 Owner Alignment Gate 仍是 pending，最终回复必须直接包含下一组 owner 问题，不能只说“已生成问卷”。

进度判断脚本是初始化 Skill 的内置门禁：

```bash
python scripts/openlifeos_progress.py <target-lifeos-repo>
```

如果需要严格验收：

```bash
python scripts/openlifeos_progress.py <target-lifeos-repo> --strict
```

不要把这段作为用户必须手动执行的教程。默认由 agent 在每个阶段结束后主动运行，并根据输出继续推进。

### Skill Review Gate

当用户要求 review 进度、判断 AnthonyHF/openLifeOS 关键产出是否完备，或 `openlifeos_progress.py --json` 显示 `Skill-guided content review` 未完成时：

1. 先运行 `python scripts/openlifeos_progress.py <target-lifeos-repo> --json`，把结果作为结构状态、artifact path 索引和机器可解释的 `skill_content_maturity` 基线。
2. 读取 `skill_review_surface` 指向的当前入口和 active artifact；重点 review Wenxin、PSP XML、Design、skill recommendations 和 `docs/evidence-sufficiency.md`。
3. 读取 `docs/self-evolution-output-standards.md`，用 Skill 语义判断这些产物是否内容完备：证据边界是否诚实、关键字段是否真正填充、缺口是否具体、是否能支持下一步 agent 行为。
4. 输出并写入 `docs/lifeos-content-review.md`，必须包含 `skill_review`、`reviewed_artifacts`、`content_completeness`、`next_recommendations` 四个标记。
5. 下一步推荐必须综合 doctor 的内容成熟度缺口和 Skill review 的语义判断；不得只按字符串规则决定。

## Before / After 判断

如果用户问 openLifeOS 和 OpenClaw、Hermes、普通 agent/runtime 的区别，重点不是“功能更多”，而是“是否形成动态进化势能”。

核心 insight：

> Moat 是动态的进化势能，不是静态的 feature，也不是某个 release。

很多工具装完之后变成玩具，是因为 agent 不够强、不够全面、不会进化，进化后也没有稳定产出。openLifeOS 必须把 agent 放进长期人格、技能、记忆、复盘和产出循环里，让它真实地产生价值：做工作、做决策、做统筹、做复盘，或者帮助用户从迷茫中重新形成方向。

验收标准不是“初始化成功”，而是从熵增进入熵减：

- 碎片被结构化。
- 决策有依据。
- skill 会增长。
- 记忆能复用。
- 人格能对齐。
- 每轮迭代都有可见产出。

## 写死 vs 生成

写死文件是确定性骨架：

- 目录结构。
- `replicateme.yml` setup manifest。
- 根 `AGENT.md` 段落。
- `matrix.yml` schema。
- `agents/openai.yaml` metadata。
- 安全边界文本。
- 空白或 TODO profile 字段。
- `artifacts/current.yml`、`identity/avatar-description/current.yml`、`DESIGN.md`、`design/versions.yml`、`identity/memories/wiki-repo.yml`、`identity/wenxin/skill-recommendations.yml`、PSP XML current/version、Evidence Maturity XML 和 PSP update log 的 scaffold。
- `integrations/github.yml`、`integrations/feishu.yml`、`integrations/hermes.yml` 和 `security/permissions.yml` 的权限配置 scaffold。

生成文件需要目标对象的证据材料：

- Wenxin 自我发现报告、能力地图、gap 分析、未来路径和内外报告分层。
- 对外定位、bio、README 叙事或个人 BP。
- 根据 Wenxin 输出生成的个人 Skill 推荐路线图和技能蒸馏材料清单。
- PSP XML/person model、语言指纹、行为边界、授权边界、验证报告。
- `DESIGN.md`、memory area index 和 active context summary。`SOUL.md` 只在目标 runtime 需要时作为投影生成。
- Hermes 增量更新摘要、同步记录和回写 PR。
- Skill selection matrix、vendored skill source release 记录和外部 repo URL。
- docs cover image 或公开展示图。

## 验证门禁

最终答复前检查：

- 目标 repo 有 `AGENT.md`、`matrix.yml`、`agents/openai.yaml`、`identity/`、`metabolism/`、`runtime/`、`evolution/`、`capabilities/`、`identities/`、`security/` 和 `docs/`。
- 目标 repo 有 `artifacts/current.yml`，能看到 Avatar Description、Wenxin、PSP XML、design、recommendations 和 maturity 的最新版本入口。
- 尚未生成的产物清楚标记为 TODO。
- 没有复制 secret、原始私密转写、客户细节、合同数据或未授权 wiki 内容。
- 根 `AGENT.md` 能把 persona、skills、aesthetics、experiences、memory、security 和当前对齐状态问题路由到正确路径。
- `integrations/hermes.yml`、`identity/memories/wiki-repo.yml` 能说明增量证据如何进入 Wenxin/PSP/capability 更新循环。
- `identity/memories/wiki-repo.yml` 能说明 memory visibility、public mirror、协同方式和 authoritative source，且 public 层不包含私密正文。
- `capabilities/README.md`、`evolution/organ-systems/` 和 `matrix.yml` 能区分 runtime skills、distilled capabilities 和 self-evolution organ systems。
- `scripts/doctor_avatar_repo.py <target>` 能显示 required completion、overall completion、lifecycle stage/age，并清楚说明 100% progress 不等于内容/人格/能力成熟。
