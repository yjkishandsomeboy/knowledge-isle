import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from knowledge_isle_dev_agent.config import AgentSettings
from knowledge_isle_dev_agent.database import AgentDatabase
from knowledge_isle_dev_agent.github import GitHubClient
from knowledge_isle_dev_agent.runner import DevelopmentAgent

settings = AgentSettings.load()
database = AgentDatabase(settings.data_dir / "agent.db")
github = GitHubClient(settings.gh_path, settings.github_repo, settings.repo_root)
agent = DevelopmentAgent(settings, database, github)
poller_task: asyncio.Task[None] | None = None
github_error: str | None = None


async def poller() -> None:
    global github_error
    while True:
        try:
            await agent.poll_once()
            github_error = None
        except Exception as error:
            github_error = str(error)[-1000:]
        await asyncio.sleep(settings.poll_seconds)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    global github_error, poller_task
    try:
        await asyncio.to_thread(github.check_auth)
        await asyncio.to_thread(github.ensure_labels)
    except Exception as error:
        github_error = str(error)[-1000:]
    poller_task = asyncio.create_task(poller())
    yield
    poller_task.cancel()


app = FastAPI(title="Knowledge Isle Dev Agent", docs_url=None, lifespan=lifespan)


class MergeConfirmation(BaseModel):
    issue_number: int


@app.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD)


@app.get("/api/status")
async def status() -> dict[str, object]:
    return {
        "running": agent.lock.locked(),
        "pollSeconds": settings.poll_seconds,
        "repo": settings.github_repo,
        "codexPath": str(settings.codex_path),
        "githubError": github_error,
        "runs": database.list_runs(),
    }


@app.get("/api/runs/{run_id}")
async def run_detail(run_id: int) -> dict[str, object]:
    run = database.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/api/poll")
async def poll_now() -> dict[str, int | None]:
    return {"runId": await agent.poll_once()}


@app.post("/api/runs/{run_id}/approve")
async def approve(run_id: int) -> dict[str, bool]:
    try:
        await agent.approve_merge(run_id)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"ok": True}


@app.post("/api/runs/{run_id}/merge")
async def merge(run_id: int, payload: MergeConfirmation) -> dict[str, bool]:
    try:
        await agent.confirm_merge(run_id, payload.issue_number)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {"ok": True}


DASHBOARD = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Knowledge Isle / Dev Agent</title>
  <style>
    :root{--ink:#161812;--paper:#e9e7dc;--acid:#d7ff3f;--line:#383a32;--muted:#75786d;--danger:#df5c48}
    *{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Mono","Cascadia Code",monospace}
    body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.2;background-image:linear-gradient(rgba(0,0,0,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(0,0,0,.08) 1px,transparent 1px);background-size:32px 32px}
    .shell{min-height:100vh;display:grid;grid-template-columns:280px 1fr;position:relative}.rail{padding:32px 24px;border-right:2px solid var(--ink);display:flex;flex-direction:column;justify-content:space-between;background:#d8d6ca}
    .brand{font:800 27px Georgia,serif;line-height:.9}.brand small{display:block;font:11px monospace;letter-spacing:.22em;margin-top:13px}.lamp{display:flex;align-items:center;gap:9px;font-size:12px}.dot{width:10px;height:10px;border-radius:50%;background:var(--muted)}.dot.live{background:var(--acid);box-shadow:0 0 0 4px rgba(215,255,63,.3)}
    main{padding:34px clamp(24px,5vw,72px)}header{display:flex;justify-content:space-between;align-items:end;border-bottom:2px solid;padding-bottom:24px}h1{font:700 clamp(42px,7vw,92px)/.82 Georgia,serif;margin:0;letter-spacing:-.06em}button{font:700 12px monospace;text-transform:uppercase;letter-spacing:.08em;border:2px solid var(--ink);background:var(--acid);padding:13px 16px;cursor:pointer;box-shadow:4px 4px 0 var(--ink)}button:hover{transform:translate(2px,2px);box-shadow:2px 2px 0 var(--ink)}
    .meta{display:flex;gap:24px;margin:18px 0 34px;color:var(--muted);font-size:12px}.grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(290px,.7fr);gap:24px}.panel{border:2px solid var(--ink);background:rgba(249,248,240,.9)}.panel-title{padding:12px 16px;border-bottom:2px solid;font-size:11px;letter-spacing:.18em;text-transform:uppercase;background:var(--ink);color:white}.runs{min-height:450px}.run{padding:18px;border-bottom:1px solid var(--line);display:grid;grid-template-columns:62px 1fr auto;gap:14px;cursor:pointer}.run:hover{background:var(--acid)}.run strong{font-size:14px}.run p{margin:6px 0 0;color:var(--muted);font-size:11px}.badge{align-self:start;border:1px solid;padding:5px 7px;font-size:10px;text-transform:uppercase}.detail{padding:18px;min-height:450px}.event{border-left:3px solid;padding:0 0 18px 14px;margin-left:4px;font-size:11px}.event time{color:var(--muted);display:block;margin-top:5px}.actions{display:grid;gap:12px;margin-top:25px}.actions button{width:100%}.actions .danger{background:var(--danger);color:white}.empty{padding:34px;color:var(--muted)}input{width:100%;border:2px solid;padding:12px;background:white;font:14px monospace}
    @media(max-width:850px){.shell{grid-template-columns:1fr}.rail{border-right:0;border-bottom:2px solid;flex-direction:row}.grid{grid-template-columns:1fr}h1{font-size:48px}}
  </style>
</head>
<body><div class="shell"><aside class="rail"><div><div class="brand">Knowledge<br>Isle<small>DEV AGENT / LOCAL</small></div></div><div class="lamp"><i class="dot" id="lamp"></i><span id="agent-state">IDLE</span></div></aside>
<main><header><div><h1>Build<br>control.</h1></div><button onclick="pollNow()">立即检查 Issues</button></header><div class="meta"><span id="repo">REPO / —</span><span id="interval">POLL / —</span><span>BOUND / 127.0.0.1</span></div>
<div class="grid"><section class="panel runs"><div class="panel-title">Execution ledger</div><div id="runs"><div class="empty">正在读取运行记录…</div></div></section><aside class="panel"><div class="panel-title">Run inspection</div><div class="detail" id="detail"><div class="empty">选择一条运行记录查看阶段与审核操作。</div></div></aside></div></main></div>
<script>
let current=null;async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});if(!r.ok){const b=await r.json();throw new Error(b.detail||r.statusText)}return r.json()}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function refresh(){const s=await api('/api/status');document.querySelector('#repo').textContent='REPO / '+s.repo;document.querySelector('#interval').textContent='POLL / '+Math.round(s.pollSeconds/60)+' MIN';document.querySelector('#lamp').className='dot '+(s.running?'live':'');document.querySelector('#agent-state').textContent=s.githubError?'GITHUB ERROR':(s.running?'EXECUTING':'IDLE');document.querySelector('#runs').innerHTML=s.githubError?`<div class="empty">GitHub 连接异常：${esc(s.githubError)}</div>`:(s.runs.length?s.runs.map(r=>`<article class="run" onclick="selectRun(${r.id})"><b>#${r.issue_number}</b><div><strong>${esc(r.issue_title)}</strong><p>${esc(r.updated_at)}</p></div><span class="badge">${esc(r.status)}</span></article>`).join(''):'<div class="empty">暂无任务。为 GitHub Issue 添加 agent-ready 标签即可进入队列。</div>');if(current)await selectRun(current,false)}
async function selectRun(id,set=true){if(set)current=id;const r=await api('/api/runs/'+id);const events=r.events.map(e=>`<div class="event"><b>${esc(e.message)}</b><time>${esc(e.created_at)}</time></div>`).join('');let actions='';if(r.status==='awaiting_review'){actions=`<div class="actions"><button onclick="approve(${id})">第一步：批准合并</button>${r.merge_approved?`<input id="issue-confirm" placeholder="输入 Issue 编号 #${r.issue_number}"><button class="danger" onclick="mergeRun(${id})">最终确认并合并</button>`:''}</div>`}document.querySelector('#detail').innerHTML=`<h2>#${r.issue_number} ${esc(r.issue_title)}</h2><p class="badge">${esc(r.status)}</p>${r.pr_url?`<p><a target="_blank" href="${esc(r.pr_url)}">打开 Pull Request ↗</a></p>`:''}${r.error?`<pre>${esc(r.error)}</pre>`:''}<hr>${events}${actions}`}
async function pollNow(){try{const x=await api('/api/poll',{method:'POST'});alert(x.runId?'已领取任务 Run #'+x.runId:'没有新的 agent-ready Issue');await refresh()}catch(e){alert(e.message)}}
async function approve(id){if(!confirm('确认你已经在 GitHub 审核代码差异与测试结果？'))return;await api(`/api/runs/${id}/approve`,{method:'POST'});await selectRun(id)}
async function mergeRun(id){const n=Number(document.querySelector('#issue-confirm').value);if(!confirm('最终确认：这将合并 PR 并删除远程分支。继续？'))return;try{await api(`/api/runs/${id}/merge`,{method:'POST',body:JSON.stringify({issue_number:n})});await refresh()}catch(e){alert(e.message)}}
refresh();setInterval(refresh,5000)
</script></body></html>"""
