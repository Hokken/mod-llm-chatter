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
</style>
</head>
<body>
<div class="left" id="leftPanel">
  <div class="hdr">LLM Log Viewer
    <span id="title-total"></span></div>
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

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        path = parsed.path

        if path == '/':
            self._send_html(INDEX_HTML)
        elif path == '/api/logs':
            self._send_json(_api_logs(qs))
        elif path == '/api/stats':
            self._send_json(_api_stats())
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
    print(f"Log file : {LOG_PATH}")
    print(
        f"Viewer   : http://localhost:{args.port}"
    )

    server = HTTPServer(('0.0.0.0', args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
