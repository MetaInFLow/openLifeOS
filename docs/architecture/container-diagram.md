# Container Diagram - openLifeOS

```mermaid
C4Container
  title Container Diagram - openLifeOS Factory and Generated LifeOS Repo

  Person(owner, "Owner", "Approves identity, memory, and Skill boundaries")
  Person(agent, "AI Agent", "Runs initialization, tasks, retrospectives, and updates")

  System_Boundary(factory, "openLifeOS Factory Repo") {
    Container(rootSkill, "Root AGENT.md", "Markdown protocol", "Agent entrypoint and operating rules")
    Container(templates, "Avatar Templates", "Markdown/YAML templates", "Generated LifeOS repo skeleton")
    Container(scripts, "Scaffold and Doctor Scripts", "Python", "Init, apply config, validate, and progress checks")
    Container(refs, "Architecture References", "Markdown", "Blueprints, memory isolation, Skill taxonomy")
  }

  System_Boundary(lifeos, "Generated LifeOS Repo") {
    Container(identity, "Identity Layer", "Markdown/YAML", "Public profile, Wenxin, PSP/person model")
    Container(skills, "Skill Layer", "Skill repos and references", "Runtime skills, meta skills, self-evolution bridges")
    Container(memory, "Memory Layer", "Indexes and pointers", "Public-safe indexes and private source entrypoints")
    Container(integrations, "Integration Layer", "YAML", "GitHub, Feishu/Lark, Hermes permissions")
    Container(security, "Security Layer", "Markdown/YAML", "Visibility, banned material, secret policies")
    Container(docs, "Docs Layer", "Markdown/assets", "Public-safe human-facing diagrams and narrative")
  }

  System_Ext(privateMemory, "Private Memory Authority", "Private wiki, local vault, server-rsync", "Raw private bodies and source artifacts")
  System_Ext(runtimeRepo, "Runtime Skill Repos", "GitHub/submodules", "Execution skills and run evidence")
  System_Ext(metaRepo, "Distilled Meta Skill Repos", "GitHub/submodules", "Reusable judgment and methodology")

  Rel(owner, scripts, "Provides setup config")
  Rel(agent, rootSkill, "Reads rules")
  Rel(rootSkill, refs, "Routes to")
  Rel(scripts, templates, "Renders")
  Rel(scripts, lifeos, "Creates and validates")
  Rel(identity, skills, "Seeds recommendations")
  Rel(skills, memory, "Stores lessons and evidence pointers")
  Rel(memory, privateMemory, "Reads authorized sources")
  Rel(skills, runtimeRepo, "Links runtime execution")
  Rel(skills, metaRepo, "Links distilled methodology")
  Rel(integrations, privateMemory, "Defines access boundary")
  Rel(security, memory, "Constrains publication")
  Rel(docs, security, "Publishes only approved material")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```
