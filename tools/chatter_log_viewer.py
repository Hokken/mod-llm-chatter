#!/usr/bin/env python3
"""
LLM Request Log Viewer - zero-dependency web app.

Reads the JSONL log produced by chatter_request_logger
and presents it in a filterable, searchable web UI.

Run on the HOST (not in Docker):
    python chatter_log_viewer.py [--log PATH] [--port 5555]

No external dependencies — uses only stdlib.
"""

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

LOG_PATH = None  # set from CLI args
SNAPSHOT_DIR = None  # derived from LOG_PATH


def _read_entries():
    """Read all JSONL entries from the log file.

    Returns list of dicts, newest-first.
    """
    if LOG_PATH is None or not LOG_PATH.exists():
        return []
    entries = []
    with open(LOG_PATH, 'r', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.reverse()
    return entries


def _api_logs(qs):
    page = int((qs.get('page') or ['1'])[0])
    per_page = int((qs.get('per_page') or ['50'])[0])
    label_filter = (qs.get('label') or [''])[0]
    search = (qs.get('search') or [''])[0]

    entries = _read_entries()

    all_labels = sorted(set(
        e.get('label', '') for e in entries
    ))

    if label_filter:
        entries = [
            e for e in entries
            if e.get('label', '') == label_filter
        ]
    if search:
        sl = search.lower()
        entries = [
            e for e in entries
            if (
                sl in (e.get('prompt') or '').lower()
                or sl in (
                    e.get('response') or ''
                ).lower()
                or sl in (
                    e.get('label') or ''
                ).lower()
                or sl in (
                    e.get('model') or ''
                ).lower()
            )
        ]

    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    page_entries = entries[start:end]

    return {
        'entries': page_entries,
        'total': total,
        'page': page,
        'per_page': per_page,
        'labels': all_labels,
    }


def _api_memories(qs):
    """Return memories from the DB snapshot file."""
    page = int((qs.get('page') or ['1'])[0])
    per_page = int(
        (qs.get('per_page') or ['50'])[0]
    )
    bot_filter = (qs.get('bot') or [''])[0]
    type_filter = (qs.get('type') or [''])[0]

    entries = []
    if SNAPSHOT_DIR is not None:
        path = SNAPSHOT_DIR / 'db_memories.json'
        try:
            with open(
                path, 'r', encoding='utf-8'
            ) as fh:
                data = json.load(fh)
                entries = data.get('rows', [])
        except Exception:
            entries = []

    # Collect unique bot names/guids for filter
    all_bots = sorted(set(
        e.get('bot_name', '')
        or str(e.get('bot_guid', ''))
        for e in entries
    ))

    # Collect unique memory types
    all_types = sorted(set(
        e.get('memory_type', '')
        for e in entries
        if e.get('memory_type')
    ))

    if bot_filter:
        entries = [
            e for e in entries
            if (
                (e.get('bot_name', '')
                    == bot_filter)
                or (
                    str(e.get('bot_guid', ''))
                    == bot_filter
                )
            )
        ]

    if type_filter:
        entries = [
            e for e in entries
            if (
                e.get('memory_type', '')
                == type_filter
            )
        ]

    total = len(entries)
    start = (page - 1) * per_page
    end = start + per_page
    page_entries = entries[start:end]

    return {
        'entries': page_entries,
        'total': total,
        'page': page,
        'per_page': per_page,
        'bots': all_bots,
        'types': all_types,
    }


def _api_stats():
    entries = _read_entries()
    total = len(entries)
    labels = {}
    providers = {}
    total_dur = 0
    for e in entries:
        lbl = e.get('label', '') or '(none)'
        labels[lbl] = labels.get(lbl, 0) + 1
        prov = e.get('provider', '') or '(none)'
        providers[prov] = providers.get(prov, 0) + 1
        total_dur += e.get('duration_ms', 0)
    avg_dur = (
        int(total_dur / total) if total > 0 else 0
    )
    return {
        'total': total,
        'labels': labels,
        'avg_duration_ms': avg_dur,
        'providers': providers,
    }


def _api_dbstate():
    """Read DB snapshot files written by the bridge."""
    result = {}
    for key, fname in [
        ('memories', 'db_memories.json'),
        ('queue', 'db_queue.json'),
        ('messages', 'db_messages.json'),
    ]:
        if SNAPSHOT_DIR is None:
            result[key] = {
                'rows': [], 'updated': None
            }
            continue
        path = SNAPSHOT_DIR / fname
        try:
            with open(
                path, 'r', encoding='utf-8'
            ) as fh:
                result[key] = json.load(fh)
        except Exception:
            result[key] = {
                'rows': [], 'updated': None
            }
    return result


DBSTATE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DB State - LLM Log Viewer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#ccc;
  font-family:'Consolas','Monaco',monospace;
  font-size:13px;overflow:auto}
a{color:#e94560}
.hdr{background:#0f3460;padding:6px 10px;
  font-weight:bold;font-size:14px;color:#e94560;
  display:flex;align-items:center;gap:10px;
  position:sticky;top:0;z-index:10}
.hdr a{font-size:11px;color:#ccc;
  text-decoration:none}
.nav-links{margin-left:auto;display:flex;gap:8px}
.refresh-bar{background:#16213e;padding:5px 10px;
  display:flex;gap:8px;align-items:center;
  font-size:11px;color:#888;position:sticky;
  top:34px;z-index:9}
.refresh-bar label{cursor:pointer;
  display:flex;align-items:center;gap:3px}
.refresh-bar input[type=checkbox]{
  width:14px;height:14px}
.updated{color:#555;font-size:10px}
.section{margin:12px 8px}
.section-hdr{background:#0f3460;
  padding:5px 10px;font-weight:bold;
  font-size:12px;color:#e94560;
  display:flex;align-items:center;gap:8px;
  border-radius:3px 3px 0 0}
.section-hdr .count{color:#888;
  font-size:11px;font-weight:normal}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;
  font-size:11px;background:#16213e}
th{background:#111;color:#888;padding:4px 8px;
  text-align:left;white-space:nowrap;
  font-weight:bold;letter-spacing:0.05em}
td{padding:3px 8px;border-bottom:1px solid #222;
  white-space:nowrap;max-width:260px;
  overflow:hidden;text-overflow:ellipsis}
tr:hover td{background:#1a2a4e}
tr.fm-row td{background:#3a2a00}
tr.fm-row:hover td{background:#4a3500}
.badge{padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:bold;
  display:inline-block}
.st-pending{background:#8c6d00;color:#ffe}
.st-done{background:#1b5e20;color:#dfd}
.st-cancelled{background:#444;color:#aaa}
.st-delivered{background:#1b5e20;color:#dfd}
.st-undelivered{background:#8b0000;color:#fdd}
.st-active{background:#2e7d32;color:#dfd}
.st-inactive{background:#555;color:#aaa}
.fm-badge{background:#8c6000;color:#ffe;
  padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:bold}
.filter-row{background:#16213e;
  padding:4px 8px;display:flex;gap:6px;
  align-items:center;flex-wrap:wrap;
  border-top:1px solid #222}
.filter-row select,.filter-row input{
  background:#1a1a2e;color:#ccc;
  border:1px solid #444;padding:2px 6px;
  font-size:11px;font-family:inherit;
  border-radius:3px}
.empty{color:#555;padding:8px 12px;
  font-style:italic}
</style>
</head>
<body>
<div class="hdr">DB State Diagnostic
  <span id="ts-info" class="updated"></span>
  <div class="nav-links">
    <a href="/">LLM Logs</a>
    <a href="/memories"
      style="color:#e94560">Bot Memories</a>
  </div>
</div>
<div class="refresh-bar">
  <label><input type="checkbox"
    id="autoRefresh" checked> Auto (10s)</label>
  <span id="refresh-ts"></span>
</div>

<!-- MEMORIES section -->
<div class="section">
  <div class="section-hdr">
    llm_bot_memories
    <span class="count" id="mem-count"></span>
  </div>
  <div class="filter-row">
    <select id="mem-type-filter"
      onchange="applyMemFilter()">
      <option value="">All types</option>
    </select>
    <input id="mem-search"
      placeholder="Search name / guid / memory..."
      oninput="applyMemFilter()"
      style="width:200px">
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>bot_guid</th>
        <th>bot_name</th>
        <th>player_guid</th>
        <th>memory_type</th>
        <th>memory</th>
        <th>mood</th>
        <th>active</th>
        <th>used</th>
        <th>created_at</th>
      </tr></thead>
      <tbody id="mem-body"></tbody>
    </table>
    <div id="mem-empty" class="empty"
      style="display:none">No rows</div>
  </div>
</div>

<!-- QUEUE section -->
<div class="section">
  <div class="section-hdr">
    llm_chatter_queue
    <span class="count" id="q-count"></span>
  </div>
  <div class="filter-row">
    <select id="q-status-filter"
      onchange="applyQueueFilter()">
      <option value="">All statuses</option>
      <option value="pending">pending</option>
      <option value="done">done</option>
      <option value="cancelled">cancelled</option>
    </select>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>id</th>
        <th>status</th>
        <th>request_type</th>
        <th>bot1_guid</th>
        <th>bot2_guid</th>
        <th>created_at</th>
      </tr></thead>
      <tbody id="q-body"></tbody>
    </table>
    <div id="q-empty" class="empty"
      style="display:none">No rows</div>
  </div>
</div>

<!-- MESSAGES section -->
<div class="section">
  <div class="section-hdr">
    llm_chatter_messages
    <span class="count" id="msg-count"></span>
  </div>
  <div class="filter-row">
    <select id="msg-del-filter"
      onchange="applyMsgFilter()">
      <option value="">All</option>
      <option value="0">Undelivered</option>
      <option value="1">Delivered</option>
    </select>
    <input id="msg-search"
      placeholder="Search bot_guid / message..."
      oninput="applyMsgFilter()"
      style="width:200px">
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>id</th>
        <th>bot_guid</th>
        <th>delivered</th>
        <th>deliver_at</th>
        <th>message</th>
      </tr></thead>
      <tbody id="msg-body"></tbody>
    </table>
    <div id="msg-empty" class="empty"
      style="display:none">No rows</div>
  </div>
</div>

<script>
function esc(s){
  if(s===null||s===undefined)return '';
  const d=document.createElement('div');
  d.textContent=String(s);return d.innerHTML;
}
function fmtTs(s){
  if(!s)return '';
  try{
    const d=new Date(s);
    const p=n=>String(n).padStart(2,'0');
    return p(d.getHours())+':'+p(d.getMinutes())
      +':'+p(d.getSeconds());
  }catch(e){return s;}
}
function trunc(s,n){
  if(!s)return '';
  s=String(s);
  return s.length>n?s.substring(0,n)+'...':s;
}

let allMem=[],allQueue=[],allMsg=[];

function statusBadge(st){
  const cls={
    pending:'st-pending',
    done:'st-done',
    cancelled:'st-cancelled',
  }[st]||'st-cancelled';
  return '<span class="badge '+cls
    +'">'+esc(st)+'</span>';
}

function renderMem(rows){
  const tbody=document.getElementById('mem-body');
  const empty=document.getElementById('mem-empty');
  document.getElementById('mem-count')
    .textContent='('+rows.length+' rows)';
  if(!rows.length){
    tbody.innerHTML='';
    empty.style.display='block';
    return;
  }
  empty.style.display='none';
  let h='';
  for(const r of rows){
    const fm=r.memory_type==='first_meeting';
    const used=r.used===1||r.used===true;
    h+='<tr class="'+(fm?'fm-row':'')+'">'
      +'<td>'+esc(r.bot_guid)+'</td>'
      +'<td>'+esc(r.bot_name||'')+'</td>'
      +'<td>'+esc(r.player_guid)+'</td>'
      +'<td>'+(fm
        ?'<span class="fm-badge">first_meeting'
          +'</span>'
        :esc(r.memory_type))
      +'</td>'
      +'<td title="'+esc(r.memory||'')+'">'
        +esc(trunc(r.memory||'',60))+'</td>'
      +'<td>'+esc(r.mood||'')+'</td>'
      +'<td><span class="badge '
        +(r.active?'st-active':'st-inactive')
        +'">'+(r.active?'yes':'no')+'</span></td>'
      +'<td><span class="badge '
        +(used?'st-active':'st-inactive')
        +'">'+(used?'yes':'no')+'</span></td>'
      +'<td>'+esc(fmtTs(r.created_at))+'</td>'
      +'</tr>';
  }
  tbody.innerHTML=h;
}

function renderQueue(rows){
  const tbody=document.getElementById('q-body');
  const empty=document.getElementById('q-empty');
  document.getElementById('q-count')
    .textContent='('+rows.length+' rows)';
  if(!rows.length){
    tbody.innerHTML='';
    empty.style.display='block';
    return;
  }
  empty.style.display='none';
  let h='';
  for(const r of rows){
    h+='<tr>'
      +'<td>'+esc(r.id)+'</td>'
      +'<td>'+statusBadge(r.status)+'</td>'
      +'<td>'+esc(r.request_type||'')+'</td>'
      +'<td>'+esc(r.bot1_guid||'')+'</td>'
      +'<td>'+esc(r.bot2_guid||'')+'</td>'
      +'<td>'+esc(fmtTs(r.created_at))+'</td>'
      +'</tr>';
  }
  tbody.innerHTML=h;
}

function renderMsg(rows){
  const tbody=document.getElementById('msg-body');
  const empty=document.getElementById('msg-empty');
  document.getElementById('msg-count')
    .textContent='('+rows.length+' rows)';
  if(!rows.length){
    tbody.innerHTML='';
    empty.style.display='block';
    return;
  }
  empty.style.display='none';
  let h='';
  for(const r of rows){
    const del=r.delivered===1||r.delivered===true;
    h+='<tr>'
      +'<td>'+esc(r.id)+'</td>'
      +'<td>'+esc(r.bot_guid)+'</td>'
      +'<td><span class="badge '
        +(del?'st-delivered':'st-undelivered')
        +'">'+(del?'yes':'no')+'</span></td>'
      +'<td>'+esc(fmtTs(r.deliver_at))+'</td>'
      +'<td title="'+esc(r.message||'')+'">'
        +esc(trunc(r.message||'',80))+'</td>'
      +'</tr>';
  }
  tbody.innerHTML=h;
}

function populateMemTypeFilter(){
  const types=[...new Set(
    allMem.map(r=>r.memory_type||'')
  )].filter(Boolean).sort();
  const sel=document.getElementById(
    'mem-type-filter');
  const cur=sel.value;
  let opts='<option value="">All types</option>';
  for(const t of types){
    opts+='<option value="'+esc(t)+'"'
      +(t===cur?' selected':'')+'>'+esc(t)
      +'</option>';
  }
  sel.innerHTML=opts;
}

function applyMemFilter(){
  const type=document.getElementById(
    'mem-type-filter').value;
  const search=document.getElementById(
    'mem-search').value.toLowerCase();
  let rows=allMem;
  if(type)rows=rows.filter(
    r=>r.memory_type===type);
  if(search)rows=rows.filter(r=>
    String(r.bot_guid||'').includes(search)
    ||String(r.bot_name||'')
      .toLowerCase().includes(search)
    ||String(r.memory||'')
      .toLowerCase().includes(search)
  );
  renderMem(rows);
}

function applyQueueFilter(){
  const st=document.getElementById(
    'q-status-filter').value;
  let rows=allQueue;
  if(st)rows=rows.filter(r=>r.status===st);
  renderQueue(rows);
}

function applyMsgFilter(){
  const del=document.getElementById(
    'msg-del-filter').value;
  const search=document.getElementById(
    'msg-search').value.toLowerCase();
  let rows=allMsg;
  if(del!==''){
    const want=del==='1';
    rows=rows.filter(r=>
      (r.delivered===1||r.delivered===true)
        ===want);
  }
  if(search)rows=rows.filter(r=>
    String(r.bot_guid||'').includes(search)
    ||String(r.message||'')
      .toLowerCase().includes(search)
  );
  renderMsg(rows);
}

function fetchState(){
  fetch('/api/dbstate')
    .then(r=>r.json()).then(data=>{
    allMem=(data.memories&&data.memories.rows)||[];
    allQueue=(data.queue&&data.queue.rows)||[];
    allMsg=(data.messages&&data.messages.rows)||[];

    populateMemTypeFilter();
    applyMemFilter();
    applyQueueFilter();
    applyMsgFilter();

    const upd=data.memories&&data.memories.updated;
    document.getElementById('refresh-ts')
      .textContent='Last snapshot: '
        +(upd?new Date(upd).toLocaleTimeString()
          :'unknown');
  }).catch(()=>{});
}

fetchState();
setInterval(()=>{
  if(document.getElementById('autoRefresh')
    .checked){fetchState();}
},10000);
</script>
</body>
</html>"""


INDEX_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>LLM Request Log Viewer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#ccc;
  font-family:'Consolas','Monaco',monospace;
  font-size:13px;display:flex;height:100vh;
  overflow:hidden}
a{color:#e94560}
.left{width:35%;min-width:200px;display:flex;
  flex-direction:column}
.vdivider{width:4px;background:#222;
  cursor:col-resize;flex-shrink:0}
.vdivider:hover,.vdivider.dragging{background:#e94560}
.right{flex:1;min-width:300px;display:flex;
  flex-direction:column;overflow:hidden}
.hdr{background:#0f3460;padding:6px 10px;
  font-weight:bold;font-size:14px;color:#e94560;
  display:flex;align-items:center;gap:8px}
.hdr span{color:#ccc;font-weight:normal;
  font-size:12px}
.filter-bar{background:#16213e;padding:6px 8px;
  display:flex;gap:6px;align-items:center;
  flex-wrap:wrap}
.filter-bar select,.filter-bar input{
  background:#1a1a2e;color:#ccc;
  border:1px solid #444;
  padding:3px 6px;font-size:12px;
  font-family:inherit;border-radius:3px}
.filter-bar select{max-width:140px}
.filter-bar input{flex:1;min-width:100px}
.filter-bar label{font-size:11px;color:#888;
  display:flex;align-items:center;gap:3px;
  cursor:pointer}
.filter-bar input[type=checkbox]{
  width:14px;height:14px}
.entry-list{flex:1;overflow-y:auto;
  background:#16213e}
.entry{padding:5px 8px;
  border-bottom:1px solid #222;
  cursor:pointer;display:flex;
  flex-direction:column;gap:2px}
.entry:hover{background:#1a2a4e}
.entry.selected{background:#0f3460}
.entry-row1{display:flex;align-items:center;
  gap:6px}
.entry-ts{color:#888;font-size:11px;
  white-space:nowrap}
.badge{padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:bold;
  display:inline-block}
.dur-badge{color:#fff}
.dur-green{background:#1b5e20}
.dur-yellow{background:#8c6d00}
.dur-red{background:#8b0000}
.entry-row2{font-size:11px;color:#777;
  white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.stats-bar{background:#0f3460;padding:4px 8px;
  font-size:11px;color:#888;display:flex;gap:12px}
.detail-hdr{background:#0f3460;padding:8px 12px;
  display:flex;flex-wrap:wrap;gap:8px;
  align-items:center;font-size:12px;flex-shrink:0}
.detail-hdr .badge{font-size:11px}
.prompt-pane{flex:1;display:flex;
  flex-direction:column;overflow:hidden;
  min-height:150px}
.response-pane{flex:0 0 200px;min-height:150px;
  display:flex;flex-direction:column;
  overflow:hidden}
.divider{height:3px;background:#222;
  cursor:row-resize;flex-shrink:0}
.divider:hover{background:#444}
.section-title{background:#16213e;
  padding:4px 10px;font-weight:bold;
  font-size:12px;color:#e94560;
  display:flex;align-items:center;gap:8px;
  flex-shrink:0}
.section-title button{background:#333;
  color:#ccc;border:1px solid #555;
  padding:2px 8px;cursor:pointer;
  font-size:11px;font-family:inherit;
  border-radius:3px;transition:background 0.2s,
  border-color 0.2s}
.section-title button:hover{background:#555}
.section-title button.copied{background:#1b5e20;
  border-color:#27ae60;color:#fff}
.section-pills{display:flex;gap:4px;
  flex-wrap:wrap;margin-left:auto}
.section-pill{font-size:9px;font-weight:bold;
  padding:1px 5px;border-radius:3px;
  letter-spacing:0.05em;opacity:0.85}
.prompt-body{padding:8px 10px;flex:1;
  overflow-y:auto}
.response-body{padding:8px 10px;flex:1;
  overflow-y:auto;white-space:pre-wrap;
  word-break:break-word;font-size:12px;
  line-height:1.5}
.response-body pre{white-space:pre-wrap;
  word-break:break-word;font-family:inherit;
  font-size:12px;line-height:1.5;margin:0}
.null-badge{background:#8b0000;color:#fff;
  padding:4px 12px;font-weight:bold;
  border-radius:4px;display:inline-block;
  margin:8px}
.pager{background:#16213e;padding:4px 8px;
  display:flex;gap:6px;align-items:center;
  font-size:11px;color:#888}
.pager button{background:#333;color:#ccc;
  border:1px solid #555;padding:2px 8px;
  cursor:pointer;font-size:11px;
  font-family:inherit;border-radius:3px}
.pager button:hover{background:#555}
.pager button:disabled{opacity:0.4;
  cursor:default}
/* Prompt block styling */
.prompt-block{border-left:3px solid transparent;
  padding:4px 8px 4px 10px;margin-bottom:2px;
  position:relative}
.prompt-block-label{font-size:9px;
  font-weight:bold;letter-spacing:0.08em;
  opacity:0.6;display:block;margin-bottom:2px}
.prompt-block pre{white-space:pre-wrap;
  word-break:break-word;font-family:inherit;
  font-size:12px;line-height:1.5;margin:0}
.prompt-identity{border-color:#4a90e2;
  background:rgba(74,144,226,0.08)}
.prompt-traits{border-color:#9b59b6;
  background:rgba(155,89,182,0.08)}
.prompt-context{border-color:#1abc9c;
  background:rgba(26,188,156,0.08)}
.prompt-task{border-color:#e67e22;
  background:rgba(230,126,34,0.08)}
.prompt-rules{border-color:#27ae60;
  background:rgba(39,174,96,0.08)}
.prompt-format{border-color:#95a5a6;
  background:rgba(149,165,166,0.08)}
.prompt-style{border-color:#f39c12;
  background:rgba(243,156,18,0.08)}
.ctx-table{width:100%;border-collapse:collapse;
  font-size:11px}
.ctx-table td{padding:2px 6px;
  border-bottom:1px solid #222}
.ctx-table td:first-child{color:#888;
  white-space:nowrap;width:100px;
  font-weight:bold}
.ctx-table td:last-child{color:#ccc;
  word-break:break-word}
.ctx-section{background:#16213e;padding:4px 10px;
  flex-shrink:0;display:none}
.ctx-section .ctx-title{font-size:11px;
  color:#e94560;font-weight:bold;
  margin-bottom:3px}
</style>
</head>
<body>
<div class="left" id="leftPanel">
  <div class="hdr">LLM Log Viewer
    <span id="title-total"></span>
    <a href="/export"
      style="margin-left:auto;font-size:11px;
        color:#ccc;text-decoration:none;
        background:#333;padding:2px 8px;
        border:1px solid #555;border-radius:3px"
      >Export Debug Log</a>
    <a href="/memories"
      style="font-size:11px;
        color:#e94560;text-decoration:none">
      Bot Memories</a>
    <a href="/dbstate"
      style="font-size:11px;
        color:#e94560;text-decoration:none">
      DB State</a></div>
  <div class="filter-bar">
    <select id="labelFilter"><option value="">
      All labels</option></select>
    <input id="searchBox" placeholder="Search...">
    <label><input type="checkbox" id="autoRefresh"
      checked> Auto</label>
  </div>
  <div class="entry-list" id="entryList"></div>
  <div class="pager">
    <button id="prevBtn" disabled>&lt; Prev</button>
    <span id="pageInfo"></span>
    <button id="nextBtn">Next &gt;</button>
  </div>
  <div class="stats-bar" id="statsBar"></div>
</div>
<div class="vdivider" id="vdivider"></div>
<div class="right">
  <div class="detail-hdr" id="detailHdr">
    Select an entry</div>
  <div class="ctx-section" id="ctxSection">
    <div class="ctx-title">Context</div>
    <table class="ctx-table">
      <tbody id="ctxBody"></tbody>
    </table>
  </div>
  <div class="prompt-pane" id="promptPane">
    <div class="section-title">
      <span>Prompt</span>
      <span class="section-pills"
        id="promptPills"></span>
      <button id="copyPromptBtn"
        onclick="copyPrompt()">Copy</button>
    </div>
    <div class="prompt-body" id="promptBody"></div>
  </div>
  <div class="divider" id="divider"></div>
  <div class="response-pane" id="responsePane">
    <div class="section-title">Response
      <button id="copyResponseBtn"
        onclick="copyResponse()">Copy</button>
    </div>
    <div class="response-body"
      id="responseBody"></div>
  </div>
</div>
<script>
const PALETTE=[
  '#4a6fa5','#6b4a8a','#4a8a6b','#8a6b4a',
  '#5a7a9a','#7a5a6a','#5a8a7a','#8a7a5a'
];
function hashColor(s){
  let h=0;
  for(let i=0;i<s.length;i++)
    h=((h<<5)-h)+s.charCodeAt(i);
  return PALETTE[Math.abs(h)%PALETTE.length];
}
function durClass(ms){
  if(ms<500)return 'dur-green';
  if(ms<=2000)return 'dur-yellow';
  return 'dur-red';
}
function fmtTs(iso){
  try{
    const d=new Date(iso);
    const p=n=>String(n).padStart(2,'0');
    return p(d.getHours())+':'+p(d.getMinutes())
      +':'+p(d.getSeconds());
  }catch(e){return iso;}
}
function esc(s){
  if(!s)return '';
  const d=document.createElement('div');
  d.textContent=s;return d.innerHTML;
}

let page=1,perPage=50,selectedIdx=-1,entries=[];
let allLabels=[];

/* --- Copy with green flash --- */
function flashCopied(btn){
  btn.classList.add('copied');
  btn.textContent='Copied';
  setTimeout(()=>{
    btn.classList.remove('copied');
    btn.textContent='Copy';
  },1500);
}

function copyPrompt(){
  const els=document.querySelectorAll(
    '#promptBody .prompt-block pre');
  const parts=[];
  els.forEach(el=>{parts.push(el.textContent);});
  const text=parts.join('\n');
  const btn=document.getElementById('copyPromptBtn');
  navigator.clipboard.writeText(text)
    .then(()=>flashCopied(btn)).catch(()=>{});
}

function copyResponse(){
  const el=document.getElementById('responseBody');
  if(!el)return;
  const btn=document.getElementById(
    'copyResponseBtn');
  navigator.clipboard.writeText(el.textContent)
    .then(()=>flashCopied(btn)).catch(()=>{});
}

/* --- Prompt section classifier --- */
const SECTION_COLORS={
  identity:'#4a90e2',traits:'#9b59b6',
  context:'#1abc9c',task:'#e67e22',
  rules:'#27ae60',format:'#95a5a6',
  style:'#f39c12'
};
const SECTION_LABELS={
  identity:'IDENTITY',traits:'TRAITS',
  context:'CONTEXT',task:'TASK',
  rules:'RULES',format:'FORMAT',
  style:'STYLE',other:''
};

function classifyLine(line,state){
  const t=line.trim();
  if(t==='')return state;

  /* Format */
  if(/respond with|your response must|return json|valid json|output format/i.test(t))
    return 'format';
  if(/["']message["']|["']action["']/i.test(t))
    return 'format';
  if(state==='format'&&/^["{]/.test(t))
    return 'format';

  /* Rules */
  if(/^rules:|^guidelines:/i.test(t))
    return 'rules';
  if(state==='rules'&&/^-\s/.test(t))
    return 'rules';
  if(state==='rules'&&/^[A-Z]/.test(t)
    &&!/^-/.test(t)&&t.length>30)
    return 'other';

  /* Style / Length */
  if(/^length:|^style:|^sound like|length mode:/i
    .test(t))return 'style';

  /* Identity */
  if(/^you are [A-Z]|^playing as|^your name is/i
    .test(t))return 'identity';
  if(state==='identity'
    &&!/^your (personality|tone|mood|task|goal)/i
      .test(t)
    &&!/^party|^group|^recent|^zone|^location/i
      .test(t)
    &&!/^you just|^say |^write |^generate /i
      .test(t)
    &&!/^reply|^react|^respond/i.test(t)
    &&!/^-\s/.test(t)
    &&t.length>0)
    return 'identity';

  /* Traits */
  if(/^your (personality|tone|mood|traits):/i
    .test(t))return 'traits';
  if(/creative twist:|background feelings/i
    .test(t))return 'traits';
  if(/race flavor|speaking style/i.test(t))
    return 'traits';
  if(/personality traits/i.test(t))
    return 'traits';
  if(state==='traits'&&/^-\s/.test(t))
    return 'traits';

  /* Context */
  if(/^party members:|^group members:/i.test(t))
    return 'context';
  if(/^recent chat:|^chat history:/i.test(t))
    return 'context';
  if(/^zone:|^location:|^area:/i.test(t))
    return 'context';
  if(/^nearby|^you are in|^currently in/i.test(t))
    return 'context';
  if(/^the dungeon|^the raid|^the battleground/i
    .test(t))return 'context';
  if(/\[context\]|\[location\]|\[zone\]/i.test(t))
    return 'context';
  if(/^\[/.test(t))return 'context';
  if(state==='context'&&/^-\s/.test(t))
    return 'context';

  /* Task */
  if(/^you just |^say a |^write a /i.test(t))
    return 'task';
  if(/^generate |^reply to|^react to/i.test(t))
    return 'task';
  if(/^your task|^your goal/i.test(t))
    return 'task';
  if(/^now respond|^respond to/i.test(t))
    return 'task';

  return state;
}

function highlightPrompt(text){
  if(!text)return {html:'',counts:{}};
  const lines=text.split('\n');

  let blocks=[];
  let curType='other';
  let curLines=[];

  for(let i=0;i<lines.length;i++){
    const line=lines[i];
    const newType=classifyLine(line,curType);

    if(newType!==curType&&curLines.length>0){
      if(curLines.some(l=>l.trim())){
        blocks.push(
          {type:curType,lines:curLines});
      }
      curLines=[];
    }
    curType=newType;
    curLines.push(line);
  }
  if(curLines.some(l=>l.trim())){
    blocks.push({type:curType,lines:curLines});
  }

  /* Count sections for pills */
  const counts={};
  for(const b of blocks){
    if(b.type!=='other'){
      counts[b.type]=(counts[b.type]||0)+1;
    }
  }

  let html='';
  for(const block of blocks){
    const label=SECTION_LABELS[block.type]||'';
    const cls='prompt-block prompt-'+block.type;
    const content=esc(block.lines.join('\n'));
    html+='<div class="'+cls+'">';
    if(label){
      html+='<span class="prompt-block-label">'
        +label+'</span>';
    }
    html+='<pre>'+content+'</pre></div>';
  }
  return {html:html,counts:counts};
}

function renderPills(counts){
  const el=document.getElementById('promptPills');
  if(!el)return;
  let html='';
  const order=['identity','traits','context',
    'task','rules','format','style'];
  for(const t of order){
    if(!counts[t])continue;
    const c=SECTION_COLORS[t]||'#555';
    const lbl=SECTION_LABELS[t]||t;
    html+='<span class="section-pill"'
      +' style="background:'+c+'22;color:'+c
      +';border:1px solid '+c+'44">'
      +lbl+(counts[t]>1
        ?' x'+counts[t]:'')+'</span>';
  }
  el.innerHTML=html;
}

function fetchLogs(){
  const label=document.getElementById(
    'labelFilter').value;
  const search=document.getElementById(
    'searchBox').value;
  const url='/api/logs?page='+page
    +'&per_page='+perPage
    +'&label='+encodeURIComponent(label)
    +'&search='+encodeURIComponent(search);
  fetch(url).then(r=>r.json()).then(data=>{
    entries=data.entries;
    const total=data.total;
    const maxPage=Math.max(1,
      Math.ceil(total/perPage));
    document.getElementById('pageInfo').textContent=
      'Page '+page+' / '+maxPage
      +' ('+total+' entries)';
    document.getElementById('prevBtn').disabled=
      (page<=1);
    document.getElementById('nextBtn').disabled=
      (page>=maxPage);
    document.getElementById('title-total')
      .textContent=total+' entries';

    if(data.labels&&data.labels.length>0){
      const sel=document.getElementById(
        'labelFilter');
      const cur=sel.value;
      const opts=['<option value="">All labels'
        +'</option>'];
      data.labels.forEach(l=>{
        const s=(l===cur)?' selected':'';
        opts.push('<option value="'
          +esc(l)+'"'+s+'>'+esc(l||'(empty)')
          +'</option>');
      });
      sel.innerHTML=opts.join('');
    }

    renderList();
  }).catch(()=>{});
}

function renderList(){
  const el=document.getElementById('entryList');
  let html='';
  entries.forEach((e,i)=>{
    const cls=(i===selectedIdx)?'entry selected'
      :'entry';
    const lbl=e.label||'';
    const lc=hashColor(lbl);
    const dc=durClass(e.duration_ms||0);
    const model=(e.model||'').substring(0,24);
    const prov=e.provider||'';
    html+='<div class="'+cls
      +'" onclick="selectEntry('+i+')">'
      +'<div class="entry-row1">'
      +'<span class="entry-ts">'
      +esc(fmtTs(e.timestamp))+'</span>'
      +'<span class="badge" style="background:'
      +lc+'">'+esc(lbl||'--')+'</span>'
      +'<span class="badge dur-badge '+dc+'">'
      +(e.duration_ms||0)+'ms</span>'
      +'</div>'
      +'<div class="entry-row2">'
      +esc(prov)+' / '+esc(model)+'</div>'
      +'</div>';
  });
  el.innerHTML=html;
}

function selectEntry(i){
  selectedIdx=i;
  renderList();
  const e=entries[i];
  if(!e)return;

  const lc=hashColor(e.label||'');
  const dc=durClass(e.duration_ms||0);
  let hdr='<span class="entry-ts">'
    +esc(e.timestamp)+'</span> '
    +'<span class="badge" style="background:'
    +lc+'">'+esc(e.label||'--')+'</span> '
    +'<span class="badge dur-badge '+dc+'">'
    +(e.duration_ms||0)+'ms</span> '
    +'<span style="color:#888">'
    +esc(e.provider||'')+' / '
    +esc(e.model||'')+'</span>';
  document.getElementById('detailHdr')
    .innerHTML=hdr;

  /* --- Context metadata section --- */
  const CTX_FIELDS=[
    ['zone_name','Zone'],
    ['zone_flavor','Zone flavor'],
    ['subzone_name','Subzone'],
    ['subzone_lore','Subzone lore'],
    ['speaker_talent','Speaker talent'],
    ['target_talent','Target talent']
  ];
  const ctxSec=document.getElementById('ctxSection');
  const ctxBody=document.getElementById('ctxBody');
  let ctxHtml='';
  for(const [k,label] of CTX_FIELDS){
    const v=e[k];
    if(v&&String(v).trim()){
      ctxHtml+='<tr><td>'+esc(label)
        +'</td><td>'+esc(String(v))
        +'</td></tr>';
    }
  }
  /* Memories: array of strings */
  if(Array.isArray(e.memories)&&e.memories.length){
    e.memories.forEach((m,i)=>{
      ctxHtml+='<tr><td>Memory '+(i+1)
        +'</td><td style="font-style:italic">'
        +esc(String(m))+'</td></tr>';
    });
  }
  if(ctxHtml){
    ctxBody.innerHTML=ctxHtml;
    ctxSec.style.display='block';
  }else{
    ctxBody.innerHTML='';
    ctxSec.style.display='none';
  }

  const result=highlightPrompt(e.prompt||'');
  document.getElementById('promptBody')
    .innerHTML=result.html;
  renderPills(result.counts);

  const rb=document.getElementById('responseBody');
  if(!e.response&&e.response!==''){
    rb.innerHTML='<span class="null-badge">'
      +'NULL RESPONSE</span>';
  }else if(e.response===''){
    rb.innerHTML='<span class="null-badge">'
      +'EMPTY RESPONSE</span>';
  }else{
    const trimmed=(e.response||'').trim();
    if(trimmed.charAt(0)==='{'){
      try{
        const parsed=JSON.parse(trimmed);
        const pretty=JSON.stringify(parsed,null,2);
        rb.innerHTML='<pre>'+esc(pretty)+'</pre>';
      }catch(ex){
        rb.innerHTML='<pre>'
          +esc(e.response)+'</pre>';
      }
    }else{
      rb.innerHTML='<pre>'
        +esc(e.response)+'</pre>';
    }
  }
}

function fetchStats(){
  fetch('/api/stats').then(r=>r.json()).then(
    data=>{
    document.getElementById('statsBar')
      .textContent='Total: '+data.total
      +' | Avg: '+data.avg_duration_ms+'ms';
  }).catch(()=>{});
}

/* --- Divider drag to resize --- */
(function(){
  const divider=document.getElementById('divider');
  const prompt=document.getElementById('promptPane');
  const response=document.getElementById(
    'responsePane');
  let dragging=false,startY=0,startPH=0,startRH=0;

  divider.addEventListener('mousedown',function(e){
    dragging=true;startY=e.clientY;
    startPH=prompt.offsetHeight;
    startRH=response.offsetHeight;
    document.body.style.cursor='row-resize';
    document.body.style.userSelect='none';
    e.preventDefault();
  });
  document.addEventListener('mousemove',function(e){
    if(!dragging)return;
    const dy=e.clientY-startY;
    const newPH=Math.max(100,startPH+dy);
    const newRH=Math.max(100,startRH-dy);
    prompt.style.flex='0 0 '+newPH+'px';
    response.style.flex='0 0 '+newRH+'px';
  });
  document.addEventListener('mouseup',function(){
    if(!dragging)return;
    dragging=false;
    document.body.style.cursor='';
    document.body.style.userSelect='';
  });
})();

/* --- Vertical divider drag to resize columns --- */
(function(){
  const vd=document.getElementById('vdivider');
  const left=document.getElementById('leftPanel');
  let dragging=false,startX=0,startW=0;
  vd.addEventListener('mousedown',function(e){
    dragging=true;startX=e.clientX;
    startW=left.offsetWidth;
    vd.classList.add('dragging');
    document.body.style.cursor='col-resize';
    document.body.style.userSelect='none';
    e.preventDefault();
  });
  document.addEventListener('mousemove',function(e){
    if(!dragging)return;
    const w=Math.max(200,Math.min(
      window.innerWidth-300,
      startW+(e.clientX-startX)));
    left.style.width=w+'px';
  });
  document.addEventListener('mouseup',function(){
    if(!dragging)return;
    dragging=false;
    vd.classList.remove('dragging');
    document.body.style.cursor='';
    document.body.style.userSelect='';
  });
})();

document.getElementById('prevBtn')
  .addEventListener('click',()=>{
    if(page>1){page--;selectedIdx=-1;fetchLogs();}
  });
document.getElementById('nextBtn')
  .addEventListener('click',()=>{
    page++;selectedIdx=-1;fetchLogs();
  });
document.getElementById('labelFilter')
  .addEventListener('change',()=>{
    page=1;selectedIdx=-1;fetchLogs();
  });
let searchTimer=null;
document.getElementById('searchBox')
  .addEventListener('input',()=>{
    clearTimeout(searchTimer);
    searchTimer=setTimeout(()=>{
      page=1;selectedIdx=-1;fetchLogs();
    },400);
  });

fetchLogs();
fetchStats();

setInterval(()=>{
  if(document.getElementById('autoRefresh').checked){
    fetchLogs();fetchStats();
  }
},30000);
</script>
</body>
</html>"""


MEMORIES_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Bot Memories - LLM Log Viewer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#ccc;
  font-family:'Consolas','Monaco',monospace;
  font-size:13px;display:flex;height:100vh;
  overflow:hidden}
a{color:#e94560}
.left{width:35%;min-width:200px;display:flex;
  flex-direction:column}
.vdivider{width:4px;background:#222;
  cursor:col-resize;flex-shrink:0}
.vdivider:hover,.vdivider.dragging{
  background:#e94560}
.right{flex:1;min-width:300px;display:flex;
  flex-direction:column;overflow:hidden}
.hdr{background:#0f3460;padding:6px 10px;
  font-weight:bold;font-size:14px;color:#e94560;
  display:flex;align-items:center;gap:8px}
.hdr span{color:#ccc;font-weight:normal;
  font-size:12px}
.filter-bar{background:#16213e;padding:6px 8px;
  display:flex;gap:6px;align-items:center;
  flex-wrap:wrap}
.filter-bar select{
  background:#1a1a2e;color:#ccc;
  border:1px solid #444;
  padding:3px 6px;font-size:12px;
  font-family:inherit;border-radius:3px;
  max-width:160px}
.entry-list{flex:1;overflow-y:auto;
  background:#16213e}
.entry{padding:6px 8px;
  border-bottom:1px solid #222;
  cursor:pointer;display:flex;
  flex-direction:column;gap:3px}
.entry:hover{background:#1a2a4e}
.entry.selected{background:#0f3460}
.entry-row1{display:flex;align-items:center;
  gap:6px}
.entry-ts{color:#888;font-size:11px;
  white-space:nowrap}
.badge{padding:1px 6px;border-radius:3px;
  font-size:10px;font-weight:bold;
  display:inline-block}
.badge-first_meeting{background:#2e7d32;
  color:#fff}
.badge-player_message{background:#1565c0;
  color:#fff}
.badge-boss_kill{background:#c62828;color:#fff}
.badge-quest_complete{background:#e65100;
  color:#fff}
.badge-default{background:#4a4a6a;color:#ccc}
.badge-active{background:#2e7d32;color:#fff}
.badge-inactive{background:#555;color:#aaa}
.badge-used{background:#1565c0;color:#fff}
.badge-unused{background:#555;color:#aaa}
.entry-row2{font-size:11px;color:#999;
  white-space:nowrap;overflow:hidden;
  text-overflow:ellipsis}
.pager{background:#16213e;padding:4px 8px;
  display:flex;gap:6px;align-items:center;
  font-size:11px;color:#888}
.pager button{background:#333;color:#ccc;
  border:1px solid #555;padding:2px 8px;
  cursor:pointer;font-size:11px;
  font-family:inherit;border-radius:3px}
.pager button:hover{background:#555}
.pager button:disabled{opacity:0.4;
  cursor:default}
.detail-hdr{background:#0f3460;padding:8px 12px;
  display:flex;flex-wrap:wrap;gap:8px;
  align-items:center;font-size:12px;
  flex-shrink:0}
.detail-body{flex:1;overflow-y:auto;
  padding:12px 16px}
.detail-section{margin-bottom:12px}
.detail-label{font-size:10px;font-weight:bold;
  letter-spacing:0.08em;color:#888;
  margin-bottom:3px}
.detail-value{font-size:13px;line-height:1.5;
  color:#ddd;white-space:pre-wrap;
  word-break:break-word}
.detail-grid{display:grid;
  grid-template-columns:100px 1fr;gap:4px 12px;
  font-size:12px}
.detail-grid .lbl{color:#888;font-weight:bold}
.detail-grid .val{color:#ccc}
.mood-badge{background:#3e2723;color:#bcaaa4;
  padding:1px 6px;border-radius:3px;
  font-size:10px}
.emote-badge{background:#1b3a2a;color:#81c784;
  padding:1px 6px;border-radius:3px;
  font-size:10px}
</style>
</head>
<body>
<div class="left" id="leftPanel">
  <div class="hdr">Bot Memories
    <span id="title-total"></span>
    <a href="/"
      style="margin-left:auto;font-size:11px;
        color:#e94560;text-decoration:none">
      LLM Logs</a>
    <a href="/dbstate"
      style="font-size:11px;
        color:#e94560;text-decoration:none">
      DB State</a></div>
  <div class="filter-bar">
    <select id="botFilter">
      <option value="">All bots</option></select>
    <select id="typeFilter">
      <option value="">All types</option></select>
  </div>
  <div class="entry-list" id="entryList"></div>
  <div class="pager">
    <button id="prevBtn" disabled>&lt; Prev</button>
    <span id="pageInfo"></span>
    <button id="nextBtn">Next &gt;</button>
  </div>
</div>
<div class="vdivider" id="vdivider"></div>
<div class="right">
  <div class="detail-hdr" id="detailHdr">
    Select a memory event</div>
  <div class="detail-body" id="detailBody"></div>
</div>
<script>
function esc(s){
  if(!s)return '';
  const d=document.createElement('div');
  d.textContent=s;return d.innerHTML;
}
function fmtTs(iso){
  try{
    const d=new Date(iso);
    const p=n=>String(n).padStart(2,'0');
    return p(d.getHours())+':'+p(d.getMinutes())
      +':'+p(d.getSeconds());
  }catch(e){return iso;}
}
function fmtTsFull(iso){
  try{
    const d=new Date(iso);
    return d.toLocaleString();
  }catch(e){return iso;}
}
function typeBadgeClass(mtype){
  const cls={
    first_meeting:'badge-first_meeting',
    player_message:'badge-player_message',
    boss_kill:'badge-boss_kill',
    quest_complete:'badge-quest_complete',
  }[mtype];
  return cls||'badge-default';
}
function truncate(s,n){
  if(!s)return '';
  return s.length>n?s.substring(0,n)+'...':s;
}
function botDisplay(e){
  return e.bot_name||('guid:'+e.bot_guid)||'?';
}

let page=1,perPage=50,selectedIdx=-1,entries=[];

function fetchMemories(){
  const bot=document.getElementById(
    'botFilter').value;
  const type=document.getElementById(
    'typeFilter').value;
  const url='/api/memories?page='+page
    +'&per_page='+perPage
    +'&bot='+encodeURIComponent(bot)
    +'&type='+encodeURIComponent(type);
  fetch(url).then(r=>r.json()).then(data=>{
    entries=data.entries;
    const total=data.total;
    const maxPage=Math.max(1,
      Math.ceil(total/perPage));
    document.getElementById('pageInfo')
      .textContent='Page '+page+' / '+maxPage
      +' ('+total+' events)';
    document.getElementById('prevBtn')
      .disabled=(page<=1);
    document.getElementById('nextBtn')
      .disabled=(page>=maxPage);
    document.getElementById('title-total')
      .textContent=total+' events';

    /* Populate bot dropdown */
    if(data.bots&&data.bots.length>0){
      const sel=document.getElementById('botFilter');
      const cur=sel.value;
      const opts=['<option value="">All bots'
        +'</option>'];
      data.bots.forEach(b=>{
        const s=(b===cur)?' selected':'';
        opts.push('<option value="'+esc(b)+'"'
          +s+'>'+esc(b||'(empty)')+'</option>');
      });
      sel.innerHTML=opts.join('');
    }
    /* Populate type dropdown */
    if(data.types&&data.types.length>0){
      const sel=document.getElementById(
        'typeFilter');
      const cur=sel.value;
      const opts=['<option value="">All types'
        +'</option>'];
      data.types.forEach(t=>{
        const s=(t===cur)?' selected':'';
        opts.push('<option value="'+esc(t)+'"'
          +s+'>'+esc(t)+'</option>');
      });
      sel.innerHTML=opts.join('');
    }

    renderList();
  }).catch(()=>{});
}

function renderList(){
  const el=document.getElementById('entryList');
  let html='';
  entries.forEach((e,i)=>{
    const cls=(i===selectedIdx)?'entry selected'
      :'entry';
    const bot=botDisplay(e);
    const mtype=e.memory_type||'';
    const mem=e.memory||'';
    const active=e.active===1||e.active===true;
    const used=e.used===1||e.used===true;

    html+='<div class="'+cls
      +'" onclick="selectEntry('+i+')">'
      +'<div class="entry-row1">'
      +'<span class="entry-ts">'
      +esc(fmtTs(e.created_at))+'</span>';

    if(mtype){
      html+='<span class="badge '
        +typeBadgeClass(mtype)+'">'
        +esc(mtype)+'</span>';
    }

    html+='<span class="badge '
      +(active?'badge-active':'badge-inactive')
      +'">'+(active?'active':'inactive')
      +'</span>';

    html+='<span class="badge '
      +(used?'badge-used':'badge-unused')
      +'">'+(used?'used':'unused')+'</span>';

    html+='</div>'
      +'<div class="entry-row2">'
      +esc(bot);
    if(mem){
      html+=' &mdash; '
        +esc(truncate(mem,80));
    }
    html+='</div></div>';
  });
  el.innerHTML=html;
}

function selectEntry(i){
  selectedIdx=i;
  renderList();
  const e=entries[i];
  if(!e)return;

  const mtype=e.memory_type||'';
  const active=e.active===1||e.active===true;
  const used=e.used===1||e.used===true;
  let hdr='<span class="entry-ts">'
    +esc(fmtTsFull(e.created_at))+'</span> '
    +'<span class="badge '
    +typeBadgeClass(mtype)+'">'
    +esc(mtype)+'</span>';
  document.getElementById('detailHdr')
    .innerHTML=hdr;

  let body='<div class="detail-section">'
    +'<div class="detail-label">MEMORY</div>'
    +'<div class="detail-value">'
    +esc(e.memory||'(empty)')+'</div></div>';

  body+='<div class="detail-section">'
    +'<div class="detail-grid">'
    +'<span class="lbl">Bot</span>'
    +'<span class="val">'
    +esc(botDisplay(e))+'</span>'
    +'<span class="lbl">Bot GUID</span>'
    +'<span class="val">'
    +(e.bot_guid||'')+'</span>'
    +'<span class="lbl">Player GUID</span>'
    +'<span class="val">'
    +(e.player_guid||'')+'</span>'
    +'<span class="lbl">Group ID</span>'
    +'<span class="val">'
    +(e.group_id||'')+'</span>'
    +'<span class="lbl">Type</span>'
    +'<span class="val">'
    +'<span class="badge '
    +typeBadgeClass(mtype)+'">'
    +esc(mtype)+'</span></span>'
    +'<span class="lbl">Active</span>'
    +'<span class="val">'
    +'<span class="badge '
    +(active?'badge-active':'badge-inactive')
    +'">'+(active?'Yes':'No')
    +'</span></span>'
    +'<span class="lbl">Used</span>'
    +'<span class="val">'
    +'<span class="badge '
    +(used?'badge-used':'badge-unused')
    +'">'+(used?'Yes':'No')
    +'</span></span>';

  if(e.mood){
    body+='<span class="lbl">Mood</span>'
      +'<span class="val">'
      +'<span class="mood-badge">'
      +esc(e.mood)+'</span></span>';
  }
  if(e.emote){
    body+='<span class="lbl">Emote</span>'
      +'<span class="val">'
      +'<span class="emote-badge">'
      +esc(e.emote)+'</span></span>';
  }
  if(e.session_start){
    body+='<span class="lbl">Session</span>'
      +'<span class="val">'
      +esc(e.session_start)+'</span>';
  }

  body+='</div></div>';

  document.getElementById('detailBody')
    .innerHTML=body;
}

/* --- Vertical divider drag --- */
(function(){
  const vd=document.getElementById('vdivider');
  const left=document.getElementById('leftPanel');
  let dragging=false,startX=0,startW=0;
  vd.addEventListener('mousedown',function(e){
    dragging=true;startX=e.clientX;
    startW=left.offsetWidth;
    vd.classList.add('dragging');
    document.body.style.cursor='col-resize';
    document.body.style.userSelect='none';
    e.preventDefault();
  });
  document.addEventListener('mousemove',function(e){
    if(!dragging)return;
    const w=Math.max(200,Math.min(
      window.innerWidth-300,
      startW+(e.clientX-startX)));
    left.style.width=w+'px';
  });
  document.addEventListener('mouseup',function(){
    if(!dragging)return;
    dragging=false;
    vd.classList.remove('dragging');
    document.body.style.cursor='';
    document.body.style.userSelect='';
  });
})();

document.getElementById('prevBtn')
  .addEventListener('click',()=>{
    if(page>1){page--;selectedIdx=-1;
      fetchMemories();}
  });
document.getElementById('nextBtn')
  .addEventListener('click',()=>{
    page++;selectedIdx=-1;fetchMemories();
  });
document.getElementById('botFilter')
  .addEventListener('change',()=>{
    page=1;selectedIdx=-1;fetchMemories();
  });
document.getElementById('typeFilter')
  .addEventListener('change',()=>{
    page=1;selectedIdx=-1;fetchMemories();
  });

fetchMemories();

setInterval(()=>{fetchMemories();},30000);
</script>
</body>
</html>"""


def _build_export(entries):
    """Build a plain-text debug export from entries.

    entries: list of dicts, newest-first (as from
    _read_entries). Covers the last 2 hours by
    default, or all entries if fewer.
    """
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=2)

    # Filter to last 2 hours
    recent = []
    for e in entries:
        ts_str = e.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(
                ts_str.replace('Z', '+00:00')
            )
        except (ValueError, AttributeError):
            continue
        if ts >= cutoff:
            recent.append(e)

    # recent is newest-first; reverse for chrono
    recent = list(reversed(recent))

    def fmt_ts(e):
        ts_str = e.get('timestamp', '')
        try:
            ts = datetime.fromisoformat(
                ts_str.replace('Z', '+00:00')
            )
            return ts.strftime('%H:%M:%S')
        except (ValueError, AttributeError):
            return ts_str[:8]

    def trunc(s, n=200):
        if not s:
            return ''
        s = str(s).replace('\n', ' ')
        if len(s) > n:
            return s[:n] + '...'
        return s

    lines = []
    lines.append('=== LLM CHATTER DEBUG EXPORT ===')
    lines.append(
        'Generated: '
        + now.strftime('%Y-%m-%d %H:%M:%S UTC')
    )
    lines.append(
        f'Entries: {len(recent)} (last 2 hours)'
    )
    lines.append('')

    # --- Errors & Warnings ---
    lines.append('=== ERRORS & WARNINGS ===')
    error_count = 0
    for e in recent:
        resp = e.get('response')
        label = e.get('label', '')
        is_err = (
            resp is None
            and e.get('duration_ms', 0) > 0
        )
        if is_err:
            bot = e.get('bot_name', '')
            lines.append(
                f'[{fmt_ts(e)}] [ERROR] '
                f'{label} | bot={bot} | '
                f'NULL response after '
                f'{e.get("duration_ms", 0)}ms'
            )
            error_count += 1
    if error_count == 0:
        lines.append('(none)')
    lines.append('')

    # --- Memory Events ---
    lines.append('=== MEMORY EVENTS ===')
    mem_labels = {
        'memory_generated',
        'memory_activated',
        'memory_discarded',
    }
    mem_count = 0
    mem_stats = {
        'generated': 0,
        'activated': 0,
        'discarded': 0,
    }
    for e in recent:
        label = e.get('label', '')
        if label not in mem_labels:
            continue
        mem_count += 1
        bot = (
            e.get('bot_name', '')
            or f'guid:{e.get("bot_guid", "?")}'
        )
        if label == 'memory_generated':
            mem_stats['generated'] += 1
            active = e.get('active', 0)
            mem = trunc(e.get('memory', ''), 120)
            mood = e.get('mood', '')
            mtype = e.get('memory_type', '')
            lines.append(
                f'[{fmt_ts(e)}] [GENERATED] '
                f'bot={bot} | type={mtype} | '
                f'mood={mood} | active={active}'
                f' | "{mem}"'
            )
        elif label == 'memory_activated':
            mem_stats['activated'] += 1
            rows = e.get('rows_activated', 0)
            gid = e.get('group_id', '')
            lines.append(
                f'[{fmt_ts(e)}] [ACTIVATED] '
                f'bot={bot} | {rows} rows '
                f'activated | group={gid}'
            )
        elif label == 'memory_discarded':
            mem_stats['discarded'] += 1
            rows = e.get('rows_discarded', 0)
            reason = e.get('reason', '')
            lines.append(
                f'[{fmt_ts(e)}] [DISCARDED] '
                f'bot={bot} | {rows} rows '
                f'discarded | reason={reason}'
            )
    if mem_count == 0:
        lines.append('(none)')
    lines.append('')

    # --- Identity Events ---
    lines.append('=== IDENTITY EVENTS ===')
    id_labels = {
        'identity_created', 'identity_reused',
        'tone_generated',
    }
    id_count = 0
    id_stats = {'created': 0, 'reused': 0, 'tone': 0}
    for e in recent:
        label = e.get('label', '')
        if label not in id_labels:
            continue
        id_count += 1
        bot = (
            e.get('bot_name', '')
            or f'guid:{e.get("bot_guid", "?")}'
        )
        if label == 'tone_generated':
            id_stats['tone'] += 1
            tone = e.get('tone', '')
            lines.append(
                f'[{fmt_ts(e)}] [TONE] '
                f'bot={bot} | tone={tone}'
            )
            continue
        traits = ','.join(filter(None, [
            e.get('trait1', ''),
            e.get('trait2', ''),
            e.get('trait3', ''),
        ]))
        ver = e.get('identity_version', '')
        if label == 'identity_created':
            id_stats['created'] += 1
            reason = e.get('reason', 'new')
            lines.append(
                f'[{fmt_ts(e)}] '
                f'[CREATED/{reason}] '
                f'bot={bot} | traits={traits}'
                f' | v{ver}'
            )
        else:
            id_stats['reused'] += 1
            role = e.get('role', '')
            role_s = (
                f' | role={role}' if role else ''
            )
            lines.append(
                f'[{fmt_ts(e)}] [REUSED] '
                f'bot={bot} | traits={traits}'
                f'{role_s} | v{ver}'
            )
    if id_count == 0:
        lines.append('(none)')
    lines.append('')

    # --- Recent LLM Calls ---
    lines.append('=== RECENT LLM CALLS (last 50) ===')
    non_llm = mem_labels | id_labels
    llm_entries = [
        e for e in recent
        if e.get('label', '') not in non_llm
    ]
    # Show last 50 (already chrono order)
    llm_tail = llm_entries[-50:]
    total_llm = 0
    total_dur = 0
    total_errors = 0
    for e in recent:
        if e.get('label', '') in non_llm:
            continue
        total_llm += 1
        total_dur += e.get('duration_ms', 0)
        if e.get('response') is None:
            total_errors += 1

    for e in llm_tail:
        label = e.get('label', '')
        bot = (
            e.get('bot_name', '')
            or e.get('context', '')
        )
        model = e.get('model', '')
        dur = e.get('duration_ms', 0)
        tokens = e.get('tokens', '')
        tok_s = (
            f' | tokens={tokens}' if tokens else ''
        )
        lines.append(
            f'[{fmt_ts(e)}] label={label} | '
            f'bot={bot} | model={model} | '
            f'{dur}ms{tok_s}'
        )
        prompt = trunc(e.get('prompt', ''), 200)
        resp = trunc(
            e.get('response', '') or '(null)', 200
        )
        lines.append(f'  PROMPT: {prompt}')
        lines.append(f'  RESPONSE: {resp}')
    if not llm_tail:
        lines.append('(none)')
    lines.append('')

    # --- Session Summary ---
    lines.append('=== SESSION SUMMARY ===')
    avg_dur = (
        int(total_dur / total_llm)
        if total_llm > 0 else 0
    )
    lines.append(
        f'Total LLM calls: {total_llm} | '
        f'Errors: {total_errors} | '
        f'Avg latency: '
        f'{avg_dur / 1000:.1f}s'
    )
    lines.append(
        f'Memory events: '
        f'generated={mem_stats["generated"]}, '
        f'activated={mem_stats["activated"]}, '
        f'discarded={mem_stats["discarded"]}'
    )
    lines.append(
        f'Identity events: '
        f'created={id_stats["created"]}, '
        f'reused={id_stats["reused"]}'
    )
    lines.append('')

    return '\n'.join(lines)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Suppress per-request access logs
        pass

    def _send_json(self, data):
        body = json.dumps(
            data, ensure_ascii=False
        ).encode('utf-8')
        self.send_response(200)
        self.send_header(
            'Content-Type', 'application/json'
        )
        self.send_header(
            'Content-Length', str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html):
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header(
            'Content-Type',
            'text/html; charset=utf-8'
        )
        self.send_header(
            'Content-Length', str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        self.send_response(404)
        self.end_headers()

    def _send_export(self):
        from datetime import datetime, timezone
        entries = _read_entries()
        text = _build_export(entries)
        body = text.encode('utf-8')
        ts = datetime.now(timezone.utc).strftime(
            '%Y%m%d_%H%M%S'
        )
        fname = f'chatter_debug_{ts}.txt'
        self.send_response(200)
        self.send_header(
            'Content-Type',
            'text/plain; charset=utf-8'
        )
        self.send_header(
            'Content-Disposition',
            f'attachment; filename={fname}'
        )
        self.send_header(
            'Content-Length', str(len(body))
        )
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = parsed.path

        if path == '/':
            self._send_html(INDEX_HTML)
        elif path == '/memories':
            self._send_html(MEMORIES_HTML)
        elif path == '/export':
            self._send_export()
        elif path == '/api/logs':
            self._send_json(_api_logs(qs))
        elif path == '/api/memories':
            self._send_json(_api_memories(qs))
        elif path == '/api/stats':
            self._send_json(_api_stats())
        elif path == '/dbstate':
            self._send_html(DBSTATE_HTML)
        elif path == '/api/dbstate':
            self._send_json(_api_dbstate())
        else:
            self._send_404()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='LLM Request Log Viewer'
    )
    parser.add_argument(
        '--log',
        default=os.path.join(
            os.path.dirname(
                os.path.abspath(__file__)
            ),
            'logs', 'llm_requests.jsonl'
        ),
        help='Path to JSONL log file'
    )
    parser.add_argument(
        '--port', type=int, default=5555,
        help='Port to listen on (default 5555)'
    )
    args = parser.parse_args()

    LOG_PATH = Path(args.log)
    SNAPSHOT_DIR = LOG_PATH.parent
    print(f"Log file : {LOG_PATH}")
    print(
        f"Viewer   : http://localhost:{args.port}"
    )

    server = HTTPServer(('0.0.0.0', args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
