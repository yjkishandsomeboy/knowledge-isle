# Knowledge Isle 本地开发 Agent

本地 Agent 由两个角色组成：Planner Agent 定时只读审计项目、创建 GitHub Issues；Dev Agent 自动读取带 `agent-ready` 标签的 Issues，调用本机 Codex 在独立 worktree 中开发，完成验证后创建 Pull Request。

```text
定时审计 → 风险分级 → 创建 Issue → 低风险自动开发 → 测试 → PR → 人工审核合并
```

## 安全边界

- 管理页面只监听 `127.0.0.1:8787`，不对局域网或公网开放。
- 一次只执行一个 Issue，不直接修改 `main`。
- Planner 只审计基于 `origin/main` 创建的临时干净 worktree，不接触本地 `.env`、运行数据或未跟踪私密文件；同时使用 `read-only` 沙箱，每 24 小时最多创建 3 个 Issue，并通过指纹和开放 Issue 标题去重。
- 文档、测试、明确 Bug、小型 UI 和小范围代码质量任务可自动添加 `agent-ready`。
- 数据库、认证授权、依赖升级、删除、部署和架构重构只创建待审核 Issue，不自动开发。
- Codex 使用 `workspace-write` 沙箱，不能自动 commit、push、合并或部署。
- 编排器只在全部质量门禁通过后自动 commit、push 和创建 PR。
- PR 合并需要：质量门禁通过、管理页初次批准、输入正确 Issue 编号并最终确认。
- 禁止提交 `.env`、Token、API Key 和私密文档。

## 首次准备

1. 安装 GitHub CLI：

   ```powershell
   winget install --id GitHub.cli
   ```

2. 关闭并重新打开 PowerShell，然后通过浏览器登录：

   ```powershell
   gh auth login --web --git-protocol https
   gh auth status
   ```

   不要把 Token 写入项目或发送给其他人。

3. Agent 首次启动会自动创建 GitHub Issue 标签：

   ```text
   agent-ready
   agent-running
   agent-review
   agent-done
   agent-blocked
   agent-planned
   agent-needs-approval
   risk-low
   risk-medium
   risk-high
   ```

## 启动

手动启动并打开管理页：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-agent/start.ps1
```

管理页：<http://127.0.0.1:8787>

安装登录后自动启动任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-agent/install-task.ps1
```

注册计划任务需要 Windows 管理员权限。如果出现 `Access is denied`，请用管理员身份打开 PowerShell 后重新执行。

卸载自动启动任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-agent/uninstall-task.ps1
```

## 使用流程

1. Planner 启动后会每 24 小时自动审计；也可在管理页点击“立即规划下一步”。
2. Planner 最多创建 3 个证据明确的 Issue。低风险任务自动添加 `agent-ready`，中高风险任务添加 `agent-needs-approval`。
3. 对待审核 Issue，人工确认安全后移除 `agent-needs-approval` 并添加 `agent-ready`。
4. Dev Agent 最多等待 10 分钟后领取；也可在管理页点击“立即检查 Issues”。
5. 查看阶段日志，完成后打开 Agent 创建的 PR 审核代码。
6. 回到管理页先点击“批准合并”。
7. 输入正确 Issue 编号并完成最终确认。

管理页的 Planner 区域会显示上次审计状态、创建数量、风险等级以及任务是自动开发还是等待批准。手动启动 Planner 前会再次提示它可能创建真实 GitHub Issues。

如果任务因本机工具或网络故障进入 `agent-blocked`，修复原因后在 GitHub 移除 `agent-blocked` 标签并保留 `agent-ready`。Agent 会复用原运行记录重新执行，不会创建重复记录。

可选环境变量：

```powershell
$env:DEV_AGENT_PLANNER_INTERVAL_HOURS = "24"
$env:DEV_AGENT_PLANNER_MAX_TASKS = "3"
$env:DEV_AGENT_UV_PATH = "C:\Users\你的用户名\.local\bin\uv.exe"
$env:DEV_AGENT_PNPM_PATH = "D:\Node_js\pnpm.CMD"
```

`DEV_AGENT_PLANNER_MAX_TASKS` 在程序内硬限制为最多 3，避免配置错误造成大量 Issues。

数据和日志保存在被 Git 忽略的 `data/dev-agent/`，开发 worktree 位于仓库同级的 `knowledge-isle-agent-worktrees/`。

## Issue 编写模板

```markdown
## 目标
清楚描述需要实现或修复的内容。

## 约束
- 不允许改变的行为
- 涉及的目录或技术栈

## 验收标准
- [ ] 可观察的功能结果
- [ ] 必须通过的测试
- [ ] 是否需要更新文档
```
