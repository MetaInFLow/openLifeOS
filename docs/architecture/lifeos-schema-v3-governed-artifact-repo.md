# LifeOS Schema v3 Governed Artifact Repo Design

日期：2026-06-13

## 背景

当前 LifeOS v2 已经把数字生命拆成 `identity/`、`metabolism/`、`runtime/`、`evolution/`、`capabilities/` 等层，但随着材料提取、InnerAtlas、PSP、Taste Generator、Meta Skill 和对外表达同时进入链路，v2 的顶层边界开始不够干净：

- 原始资料、证据索引、organ 输入包和语义产物容易混在 `metabolism/` 或 `identity/`。
- `DESIGN.md` 只覆盖 UI/设计投影，无法表达文本审美、图像审美、品牌表达和界面审美的统一 taste model。
- `capabilities/` 同时承担 runtime capability、稳定 Meta Skill、候选 Skill 和 memory 的部分语义，晋升边界不够明确。
- 对外表达散落在 public profile、work、README、website 等位置，缺少公开 claim 的证据治理。
- repo 缺少一个面向人和 agent 的总说明书，说明哪些是真相源、哪些是 organ 产物、哪些是公开表达。

v3 的目标是把 openLifeOS 重新定义为一个治理后的长期智能核心产物库，而不是原始资料库或单一生成目录。

## 设计原则

1. **材料系统是证据工厂，不是 LifeOS 语义生成器。** 它只负责 raw source、processed document、tag、evidence unit、value signal 和 organ input packet。
2. **InnerAtlas、PSP、Taste Generator、IPO Reverse 是语义产物 owner。** 材料系统不得直接写 `INNERATLAS_REPORT.xml`、`PSP_REPORT.xml`、`DESIGN_TASTE.xml` 或稳定 Meta Skill。
3. **openLifeOS repo 保存治理后的长期产物和可追溯真相源。** 原始资料可以留在外部系统，也可以 local-only 放入 `sources/raw/`，但必须有 catalog、authority 和 visibility 说明。
4. **对外表达是 projection，不是真相源。** `publication/` 只能消费 identity、PSP、taste、meta-skills 和 sources 中可公开的证据。
5. **Meta Skill 晋升必须经过证据绑定、IPO Reverse 和 owner alignment。** 候选 Skill 与稳定 Meta Skill 在目录上分开。
6. **Taste 是一等系统。** 文本审美、图像审美、界面审美和品牌表达属于同一个 taste domain，不再被 `DESIGN.md` 的 UI 语义限制。

## v3 顶层结构

```text
CATALOG.md
LIFEOS_STATUS.yml
artifacts/
sources/
identity/
taste/
meta-skills/
publication/
runtime/
evolution/
capabilities/
identities/
work/
integrations/
security/
docs/
governance/
legacy/
```

### `CATALOG.md`

根级说明书。它回答：

- 这个 LifeOS 的主要入口是什么。
- 哪些目录是真相源，哪些是 organ 产物，哪些是 projection。
- agent 应该先读什么，再读什么。
- 新材料如何进入 `sources/`，如何变成 organ input packet。
- 哪些内容可以公开，哪些只能 local-only。

### `sources/`

真相源和材料目录层，不做语义结论。

```text
sources/
  CATALOG.md
  authority.yml
  raw/
  processed/
  indexes/
  packets/
```

- `raw/`：授权原始资料暂存。默认 local-only，可为空。
- `processed/`：转录、清洗、processed MD。可重建，不是结论。
- `indexes/`：source_id、hash、外部路径、权限、tag database snapshot。
- `packets/`：给 InnerAtlas、PSP、Taste Generator、IPO Reverse 的 organ input packet。
- `authority.yml`：定义哪些源是 authoritative、visibility、allowed targets 和 token policy。

### `identity/`

身份和人物模型产物层，由 organ system 生成和维护：

- `identity/inneratlas/`：InnerAtlas 自我发现和定位源产物。
- `identity/psp/`：PSP person model、证据成熟度和版本。
- `identity/avatar-description/`：面向产品/UI/runtime 的当前读模型。
- `identity/wenxin/`：兼容 ledger、公开派生摘要和 Skill recommendations。
- `identity/memories/` 与 `identity/cognition/` 保持 v2 语义。

### `taste/`

全局审美系统入口，承载比 v2 `identity/design/` 更宽的 taste model。

```text
taste/
  current.yml
  text/
  image/
  interface/
  brand/
  references/
```

- `text/`：文本审美、语气、表达结构、写作 DNA。
- `image/`：图像审美、摄影/插画偏好、构图、质感、色彩。
- `interface/`：界面审美、信息密度、组件、动效、导航、可用性。
- `brand/`：个人或组织品牌表达变量。
- `references/`：like/maybe/avoid 证据索引。

兼容规则：v3 仍保留 `DESIGN.md` 和 `identity/design/current/DESIGN_TASTE.xml` 作为既有工具链入口；`taste/current.yml` 是新的一等入口，指向当前 text/image/interface/brand/taste artifacts。

### `meta-skills/`

治理后的稳定 Meta Skill 层。

```text
meta-skills/
  current.yml
  skills/
  candidates/
```

- `skills/`：已晋升、可复用、证据绑定清楚的 Meta Skills。
- `candidates/`：尚未通过 IPO Reverse 和 owner alignment 的候选 skill 草稿。
- `current.yml`：当前可用 Meta Skill registry。

兼容规则：`capabilities/` 继续承载 durable capabilities 和 capability-local memory；`meta-skills/` 只承载“可复用判断、路由、方法论、review gate”的稳定 Meta Skill。

### `publication/`

对外表达层。

```text
publication/
  current.yml
  profile/
  bio/
  positioning/
  website/
  media-kit/
  talks/
  articles/
  public-claims.yml
```

所有公开 claim 都必须能追溯到 approved evidence 或 organ artifact。`publication/` 不反向成为 InnerAtlas、PSP 或 Taste 的证据源，除非 owner 明确把某个公开产物作为材料重新摄入 `sources/`。

### `governance/`

实例级治理层。

```text
governance/
  README.md
  schemas/
  policies/
  decisions/
```

`docs/` 继续保存人类说明、架构文档和标准；`governance/` 保存实例内 schema snapshot、policy、ADR 和治理决策。factory 级 schema 仍在根 repo 的 `schemas/` 和 `migrations/`。

## 数据流

```text
raw materials
-> sources/raw or external source pointer
-> sources/processed
-> tag database / sources/indexes
-> evidence units / value signals
-> sources/packets/<organ>/
-> evolution/organ-systems/<organ>
-> identity / taste / meta-skills / publication drafts
-> owner alignment and registry update
```

关键约束：

- `sources/packets/` 是材料系统与 organ systems 的边界。
- organ systems 可以读取 packet 并生成自己的 timestamped artifact。
- organ systems 更新 current entrypoint 时，必须同步更新局部 registry 和 `artifacts/current.yml`。
- `publication/` 只能从已治理 artifact 生成，不直接读取私密 raw source。

## `artifacts/current.yml` v3 扩展

v3 在现有 artifact registry 中新增四类顶层 artifact：

- `sources`：source catalog、authority 和 packet registry。
- `taste`：新 taste system current entrypoint。
- `meta_skills`：稳定 Meta Skill registry。
- `publication`：对外表达 current registry 和 public claims。

旧 `design` artifact 保留，用于兼容 `DESIGN.md` 和 `identity/design/current/DESIGN_TASTE.xml`。

## 迁移策略

v3 迁移是结构增强，不做语义迁移：

1. 新增 `CATALOG.md`、`sources/`、`taste/`、`meta-skills/`、`publication/`、`governance/`。
2. 更新 `LIFEOS_STATUS.yml` 为 `lifeos_schema: v3` 和 `schema_revision: 0005_lifeos_schema_v3_governed_artifact_repo`。
3. 如果已有 `artifacts/current.yml`，追加 v3 registry sections；不覆盖现有 active artifact。
4. 不移动 `identity/design/`，只让 `taste/current.yml` 指向兼容入口。
5. 不把 `capabilities/` 移入 `meta-skills/`，只新增清晰晋升目录。
6. 不把原始资料自动复制进 `sources/raw/`。

## 生成链路改动

factory 侧必须同步调整：

- `assets/avatar-skill-template*/`：fresh init 生成 v3 目录、catalog、registry。
- `schemas/lifeos.schema.v3.yml`：声明 v3 顶层结构和兼容层。
- `scripts/init_avatar_repo.py`：新实例默认写入 v3 status metadata。
- `scripts/validate_avatar_repo.py`：允许并要求 v3 governed layers。
- `scripts/doctor_avatar_repo.py`：Skeleton gate 检查 v3 required paths，Routing gate 要求 `AGENT.md` 引用新入口。
- `scripts/migrate_lifeos_schema.py`：新增 0005 revision，`latest/head` 指向 v3。
- `migrations/versions/0005_lifeos_schema_v3_governed_artifact_repo.py`：只做确定性结构创建和文本追加。

## 验收标准

- fresh init 后 `validate_avatar_repo.py --strict-v2` 或等价 strict gate 不再误报 v3 顶层目录。
- `doctor_avatar_repo.py --json` 的 required skeleton gate 能看到 v3 目录。
- `migrate_lifeos_schema.py <repo> --to latest` 可以从 0004 升级到 0005。
- `artifacts/current.yml` 能解析 `sources`、`taste`、`meta_skills`、`publication`。
- `CATALOG.md` 和 `sources/CATALOG.md` 明确说明真相源、organ packet 和 projection 边界。
