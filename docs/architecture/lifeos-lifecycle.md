# LifeOS Lifecycle Architecture

openLifeOS 的生命周期不是初始化进度条。

初始化 gate 回答“骨架、协议、权限和入口是否齐”；生命周期回答“这个数字生命现在活到哪一阶段、主要活动从哪里产生、下一轮成长应该进入哪一层”。

## 核心判断

- `runtime/sessions/` 是 LifeOS 活动源头：真实任务、对话、执行、失败、反馈和复盘都先作为 session 发生。
- `runtime/runtime-skills/` 和 `runtime/runtime-lessons/` 是运行中的能力与经验队列，不自动等于长期能力。
- `evolution/ipo/` 负责把完成产物和 session evidence 逆向拆解成可复用 IPO、方法论和升级证据。
- `capabilities/` 只接收经过 review 的稳定能力、能力图谱和可安装/可复用 Skill 绑定。
- `identity/`、`identities/`、`work/` 提供人格、身份投影和工作场景边界，但不替代 session evidence。

Canonical flow:

```text
metabolism/inbox
-> runtime/sessions
-> runtime/runtime-skills
-> runtime/runtime-lessons
-> evolution/ipo
-> capabilities
```

## Lifecycle Stages

| Stage | 名称 | 数字生命状态 | 主要证据 |
| --- | --- | --- | --- |
| 0 | Kernel Newborn | 刚初始化，只有身体结构；没有人格、能力、经历和作品。 | `identity/`、`evolution/`、`capabilities/`、`identities/`、`work/`、`runtime/`、`metabolism/` 的空骨架。 |
| 1 | Evidence Intake | GitHub、Feishu、聊天、文档等原材料进入系统，但还没有 Wenxin/PSP 结论。 | `metabolism/inbox/` source manifest、材料用途说明、待消化摘要。 |
| 2 | Wenxin Complete | 第一轮自我认知形成，原始事实变成 identity 结论。 | `identity/wenxin/` reports、conclusions、versions。 |
| 3 | PSP Complete | 更深的人物模型形成，能描述如何思考、判断和表达。 | `identity/psp/` fingerprints、reasoning/decision/communication patterns、PSP artifact。 |
| 4 | Cloud Runtime | 部署到运行现场，第一次出现真实 session，work 开始增长。 | `runtime/sessions/` task、actions、outputs、observations；`work/` reports/projects/posts。 |
| 5 | Runtime Skill | 多个 session 中长出临时或局部可复用能力。 | `runtime/runtime-skills/` concrete workflow candidates。 |
| 6 | Runtime Lesson | session 产生局部经验，但还没有成为稳定能力。 | `runtime/runtime-lessons/` lesson-event、failure pattern、owner feedback。 |
| 7 | IPO Running | IPO 消费 sessions、runtime skills 和 runtime lessons，修改或提出能力升级。 | `evolution/ipo/` reverse reports、promotion evidence、owner alignment。 |
| 8 | Meta Skill Formation | 多个 runtime skill 融合为稳定 capability 或 distilled meta skill。 | `capabilities/` capability map、promoted skill binding、installable Skill package references。 |

Stage 0-8 是数字生命年龄和成熟状态，不是初始化步骤。一个 LifeOS 可以 scaffold 100%，但仍停在 Stage 0；也可能已经有 Wenxin/PSP，但因为没有真实 session 而还没进入 Runtime 阶段。

## First-Class Layers

生成 repo 的一等 lifecycle layers：

- `identity/`：代表谁、边界是什么、当前 person model 入口在哪里。
- `metabolism/`：授权材料、认知碎片和外部来源的代谢系统，包含 `inbox/`、`processing/` 和 `extracted/`。
- `runtime/`：真实 session、运行技能、运行 lessons 和执行证据。
- `evolution/`：IPO Reverse、alignment、mutations 和 `organ-systems/` 中 Wenxin/PSP/IPO/Taste Generator 等能力生产系统。
- `capabilities/`：review 后的能力、Skill 绑定、能力地图和可复用产物。
- `identities/`：founder、teacher、author、speaker 等社会身份投影的行为边界、账号、权限、目标和上下文。
- `work/`：项目、任务域、产出物和工作场景索引。

兼容与治理 layers：

- `identity/cognition/`：认知对象 schema、bindings、数据契约和世界观。
- `identity/memories/`：长期自我认知、稳定事实和私有 wiki 入口。
- `runtime/memory/`：session context、working lessons 和临时观察。
- `capabilities/*/memory/`：能力局部经验库、样例和验收标准。
- `integrations/`：GitHub、Feishu/Lark、Hermes、data source 和权限配置。
- `security/`：禁入材料、secret 策略和 visibility policy。
- `docs/`：人类可读说明、证据成熟度和 self-evolution 标准。
- `artifacts/`：latest registry、current entrypoint 和版本索引。
- `legacy/`：历史或无法归类的旧结构材料。

## Doctor Semantics

doctor report 必须同时报告两类状态：

1. **Scaffold/progress completion**：确定性文件、协议、权限和入口是否齐。
2. **Lifecycle stage/age**：LifeOS 当前处于 Stage 0-8 哪一段、从 start date 到现在的 age，以及为什么这样判断。

`100%` progress 只表示结构/协议门禁通过，不表示内容成熟、人格成熟、能力成熟或数字生命进入 Stage 8。内容成熟仍由 `docs/evidence-sufficiency.md`、`docs/self-evolution-output-standards.md` 和 Skill-level semantic review 判断。
