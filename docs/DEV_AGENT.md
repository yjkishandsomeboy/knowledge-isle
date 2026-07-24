# Knowledge Isle 本地开发 Agent

Dev Agent 在 Windows 本机自动读取带 `agent-ready` 标签的 GitHub Issues，调用本机 Codex 在独立 worktree 中开发，完成验证后创建 Pull Request。

## 安全边界

- 管理页面只监听 `127.0.0.1:8787`，不对局域网或公网开放。
- 一次只执行一个 Issue，不直接修改 `main`。
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

1. 在 GitHub 创建描述完整的 Issue。
2. 人工添加 `agent-ready` 标签。
3. Agent 最多等待 10 分钟后领取；也可在管理页点击“立即检查 Issues”。
4. 查看阶段日志，完成后打开 Agent 创建的 PR 审核代码。
5. 回到管理页先点击“批准合并”。
6. 输入正确 Issue 编号并完成最终确认。

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
