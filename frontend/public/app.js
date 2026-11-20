/* Vanilla JS frontend — all calls go through FastAPI, no secrets in browser code. */
const apiBase = (window.APP_CONFIG?.API_BASE_URL || '').replace(/\/$/, '');
const $ = (id) => document.getElementById(id);
const state = {token: sessionStorage.getItem('secom_access_token') || '', conversationId: null, messages: [], rows: [], summary: null, page: 'chat'};
const currency = (v, max=2) => (v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v))) ? Number(v).toLocaleString('ko-KR', {maximumFractionDigits:max}) : '—';

function notify(message) {
  const el = $('notice'); el.textContent = message; el.hidden = false;
  clearTimeout(notify.timer); notify.timer = setTimeout(() => el.hidden = true, 4800);
}

async function api(path, options={}) {
  if (!apiBase) throw new Error('API_BASE_URL이 설정되지 않았습니다. config.js 또는 Vercel 환경 변수를 확인하세요.');
  if (!state.token) throw new Error('상단에 서버 접근 토큰을 먼저 입력하세요.');
  let res;
  try {
    res = await fetch(apiBase + path, {
      ...options,
      headers: {'Content-Type':'application/json','X-Access-Token':state.token,...options.headers}
    });
  } catch (_) { throw new Error('백엔드 서버에 접속할 수 없습니다. Render 상태와 CORS 설정을 확인하세요.'); }
  let data;
  try { data = await res.json(); } catch (_) { data = null; }
  if (!res.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === 'string' ? detail : `요청 실패 (HTTP ${res.status})`);
  }
  return data;
}

function switchPage(page) {
  state.page=page;
  document.querySelectorAll('.nav-link').forEach(el => el.classList.toggle('active', el.dataset.page===page));
  document.querySelectorAll('.page').forEach(el => el.classList.toggle('active', el.id === `page-${page}`));
  $('page-title').textContent = ({chat:'AI 공정 연구 비서',data:'공정 데이터 관리',history:'AI 대화 기록'})[page];
  if (page==='history' && state.token) loadHistory().catch(e => notify(e.message));
}

function showSummary(s) {
  state.summary=s;
  $('period').textContent = s.period ? `${s.period} · ${s.dataset}` : '저장된 관측치가 없습니다';
  $('stat-count').textContent = currency(s.count,0);
  $('stat-avg').textContent = currency(s.metrics.average,2);
  $('stat-trend').textContent = s.trend.label;
  $('stat-trend-detail').textContent = s.trend.change_pct == null ? s.trend.method : `직전 20건 대비 ${s.trend.change_pct>0?'+':''}${s.trend.change_pct}%`;
  const vol = s.variability || {};
  $('stat-variability').textContent = vol.label || '데이터 부족';
  $('stat-variability-detail').textContent = vol.latest_30_std == null
    ? '비교에는 유효 측정값 60건 필요'
    : `표준편차 ${currency(vol.previous_30_std,2)} → ${currency(vol.latest_30_std,2)}`;
  $('research-observation').textContent = s.count === 0
    ? '저장된 데이터가 없습니다. 먼저 관측치를 추가해 주세요.'
    : `${currency(s.count,0)}건 관측 · 최근 20건 추세는 ${s.trend.label}. ${vol.latest_30_std == null ? '변동성 비교에는 60건이 필요합니다.' : `최근 30건 표준편차 ${currency(vol.latest_30_std,2)}.`}`;
  $('secondary-quality').textContent = s.quality.fail_rate_pct == null
    ? '참고 지표: 품질 판정 라벨이 없습니다. 측정값 자체의 변화만 분석할 수 있습니다.'
    : `참고 지표 · 유효 측정값이 있는 품질 판정 기록 ${currency(s.quality.labeled_count,0)}건 중 불량 ${currency(s.quality.fail_count,0)}건 (${s.quality.fail_rate_pct}%). 원본 1,567건 전체와 분모가 다를 수 있습니다.`;
}

function makeCell(row, text, className='') {
  const td=document.createElement('td'); td.textContent=String(text ?? '—');
  if(className) td.className=className; row.appendChild(td); return td;
}

function loadChart(rows) {
  const svg=$('trend-chart'), ns='http://www.w3.org/2000/svg';
  svg.replaceChildren();
  const values=rows.filter(x=>Number.isFinite(Number(x.value))).slice().reverse().slice(-120);
  if(values.length<2) {const t=document.createElementNS(ns,'text'); t.setAttribute('x','180');t.setAttribute('y','112');t.setAttribute('text-anchor','middle');t.setAttribute('fill','currentColor');t.setAttribute('font-size','12');t.textContent='그래프를 위한 데이터가 부족합니다.';svg.append(t);return;}
  const yvals=values.map(d=>Number(d.value)), min=Math.min(...yvals), max=Math.max(...yvals), span=Math.max(max-min,1);
  const x=(i)=>28+i*318/(values.length-1), y=(v)=>182-143*(v-min)/span;
  for(let j=0;j<=3;j++){
    const yy=39+j*143/3; const line=document.createElementNS(ns,'line');
    for(const [key,value] of Object.entries({x1:28,y1:yy,x2:347,y2:yy,stroke:'#a9b6c7','stroke-width':'.6','stroke-dasharray':'3 4'})) line.setAttribute(key,String(value));
    svg.append(line);
    const lbl=document.createElementNS(ns,'text'); lbl.setAttribute('x','25');lbl.setAttribute('y',String(yy-5));lbl.setAttribute('font-size','9');lbl.setAttribute('fill','#8a98aa');lbl.textContent=currency(max-j*span/3,1);svg.append(lbl);
  }
  const line=document.createElementNS(ns,'polyline');
  line.setAttribute('points',values.map((d,i)=>`${x(i).toFixed(1)},${y(Number(d.value)).toFixed(1)}`).join(' '));
  for(const [key,value] of Object.entries({fill:'none',stroke:'#4676ef','stroke-width':'2.5','stroke-linejoin':'round','stroke-linecap':'round'})) line.setAttribute(key,value);
  svg.append(line);
  const a=document.createElementNS(ns,'text');a.setAttribute('x','28');a.setAttribute('y','208');a.setAttribute('font-size','10');a.setAttribute('fill','#8594a8');a.textContent=(values[0].date||'');svg.append(a);
  const b=document.createElementNS(ns,'text');b.setAttribute('x','347');b.setAttribute('y','208');b.setAttribute('text-anchor','end');b.setAttribute('font-size','10');b.setAttribute('fill','#8594a8');b.textContent=(values[values.length-1].date||'');svg.append(b);
}

function showDataRows(rows) {
  state.rows=rows;
  const tbody=$('data-rows');tbody.replaceChildren();
  if (!rows.length) {const tr=document.createElement('tr');const td=makeCell(tr,'데이터가 없습니다. 위에서 추가하거나 SECOM 데이터를 가져오세요.','muted center');td.colSpan=5;tbody.append(tr);loadChart(rows);return;}
  for (const item of rows) {
    const tr=document.createElement('tr');
    makeCell(tr,item.date);makeCell(tr,currency(item.value,3));
    makeCell(tr,item.quality_label===1?'불량':item.quality_label===-1?'정상':'미지정');
    const memo=makeCell(tr,item.memo || '—','memo-cell'); memo.title=item.memo || '';
    const actions=makeCell(tr,''); actions.className='table-actions';
    const edit=document.createElement('button');edit.className='ghost';edit.textContent='수정';edit.addEventListener('click',()=>{
      $('edit-id').value=item.id;$('data-date').value=item.date;$('data-value').value=item.value;
      $('data-quality').value=item.quality_label == null ? '' : String(item.quality_label);
      $('data-memo').value=item.memo || '';$('data-save').textContent='수정 저장';
      switchPage('data');window.scrollTo({top:0,behavior:'smooth'});
    });
    const del=document.createElement('button');del.className='ghost';del.textContent='삭제';del.addEventListener('click',async()=>{
      if(!confirm(`${item.date} / ${item.value} 값을 삭제할까요?`))return;
      try {await api(`/api/data/${encodeURIComponent(item.id)}`,{method:'DELETE'});await Promise.all([loadData(),loadSummary()]);notify('데이터를 삭제했습니다.');}
      catch(e){notify(e.message);}
    });actions.append(edit,del);tbody.append(tr);
  }
  loadChart(rows);
}

function appendMessage(role, content) {
  const container=$('chat-messages');
  const empty=container.querySelector('.empty-state');if(empty) empty.remove();
  const bubble=document.createElement('div');bubble.className=`bubble ${role}`;bubble.textContent=content;container.append(bubble);container.scrollTop=container.scrollHeight;
}
function resetChat() {state.conversationId=null;state.messages=[];$('chat-messages').replaceChildren();
  const e=document.createElement('div');e.className='empty-state';e.innerHTML='<div class="empty-symbol">◎</div><strong>새 대화를 시작하세요</strong><p>현재 저장된 데이터를 기반으로 대화합니다.</p>';$('chat-messages').append(e);}

async function loadSummary(){showSummary(await api('/api/data/summary'));}
async function loadData(){showDataRows(await api('/api/data?limit=120'));}
async function loadHistory(){
  const list=await api('/api/conversations'),wrap=$('history-list');wrap.replaceChildren();
  if(!list.length){const p=document.createElement('p');p.className='muted';p.textContent='아직 저장된 대화가 없습니다.';wrap.append(p);return;}
  for (const c of list) {
    const el=document.createElement('div');el.className='history-item';
    const info=document.createElement('div');const title=document.createElement('strong');title.textContent=c.title||'제목 없는 대화';
    const meta=document.createElement('small');meta.textContent=`${c.message_count}개 메시지 · ${c.updated_at?.slice(0,16)?.replace('T',' ')||''}`;info.append(title,meta);
    const actions=document.createElement('div');actions.className='history-actions';
    const open=document.createElement('button');open.className='btn primary';open.textContent='불러오기';open.addEventListener('click',async()=>{
      try {const doc=await api(`/api/conversations/${encodeURIComponent(c.id)}`);
        state.conversationId=doc.id;state.messages=doc.messages||[];$('chat-messages').replaceChildren();
        for(const m of state.messages)appendMessage(m.role,m.content);switchPage('chat');notify('이전 대화를 불러왔습니다.');}
      catch(e){notify(e.message);}
    });
    const del=document.createElement('button');del.className='ghost';del.textContent='삭제';del.addEventListener('click',async()=>{
      if(!confirm('선택한 대화를 삭제할까요?'))return;
      try{await api(`/api/conversations/${encodeURIComponent(c.id)}`,{method:'DELETE'});if(state.conversationId===c.id)resetChat();await loadHistory();notify('대화를 삭제했습니다.');}catch(e){notify(e.message);}
    });actions.append(open,del);el.append(info,actions);wrap.append(el);
  }
}
async function initialize(){
  if(!apiBase){$('server-status').textContent='API_BASE_URL 미설정';notify('config.js에서 API_BASE_URL을 설정하세요.');return;}
  try {const res=await fetch(apiBase+'/api/health');if(!res.ok)throw new Error();$('server-status').textContent='백엔드 응답 확인';}
  catch(_){$('server-status').textContent='백엔드 연결 지연/오류';}
  if(!state.token)return;
  const tasks=await Promise.allSettled([loadSummary(),loadData(),loadHistory()]);
  const failures=tasks.filter(x=>x.status==='rejected');if(failures.length)notify(failures[0].reason.message);
}

document.querySelectorAll('.nav-link').forEach(el=>el.addEventListener('click',()=>switchPage(el.dataset.page)));
document.querySelectorAll('[data-question]').forEach(el=>el.addEventListener('click',()=>{$('chat-question').value=el.dataset.question;$('chat-question').focus();}));
$('auth-form').addEventListener('submit',async(e)=>{e.preventDefault();state.token=$('access-token').value.trim();sessionStorage.setItem('secom_access_token',state.token);await initialize();});
$('refresh-summary').addEventListener('click',()=>loadSummary().catch(e=>notify(e.message)));
$('refresh-data').addEventListener('click',()=>loadData().catch(e=>notify(e.message)));
$('refresh-history').addEventListener('click',()=>loadHistory().catch(e=>notify(e.message)));
$('new-chat').addEventListener('click',resetChat);
$('chat-form').addEventListener('submit',async e=>{
  e.preventDefault();const question=$('chat-question').value.trim();if(!question)return;
  const button=$('chat-send');button.disabled=true;$('loading').hidden=false;$('chat-question').value='';
  appendMessage('user',question);
  try {
    const result=await api('/api/chat',{method:'POST',body:JSON.stringify({question,conversation_id:state.conversationId})});
    state.conversationId=result.conversation_id;appendMessage('assistant',result.answer);
    await Promise.allSettled([loadHistory(),loadSummary()]);
  } catch(err) {notify(err.message+' · 질문을 다시 입력해 주세요.');$('chat-question').value=question;}
  finally{button.disabled=false;$('loading').hidden=true;}
});
$('data-form').addEventListener('submit',async e=>{
  e.preventDefault();const id=$('edit-id').value;
  const payload={date:$('data-date').value,value:Number($('data-value').value),memo:$('data-memo').value,
    quality_label:$('data-quality').value===''?null:Number($('data-quality').value)};
  if(!Number.isFinite(payload.value))return notify('유효한 수치를 입력하세요.');
  try{await api(id?`/api/data/${encodeURIComponent(id)}`:'/api/data',{method:id?'PUT':'POST',body:JSON.stringify(payload)});
    $('data-form').reset();$('edit-id').value='';$('data-save').textContent='데이터 추가';
    await Promise.all([loadData(),loadSummary()]);notify(id?'수정 완료':'데이터 추가 완료');
  }catch(err){notify(err.message);}
});
$('data-cancel').addEventListener('click',()=>{$('data-form').reset();$('edit-id').value='';$('data-save').textContent='데이터 추가';});
$('data-export').addEventListener('click',async()=>{
  try {const rows=await api('/api/data?limit=2000');
    const columns=['date','recorded_at','value','quality_label','memo'];
    const csv=[columns.join(','),...rows.map(r=>columns.map(k=>'"'+String(r[k]??'').replace(/"/g,'""')+'"').join(','))].join('\r\n');
    const blob=new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob);
    const a=document.createElement('a');a.href=url;a.download='secom_data_export.csv';a.click();URL.revokeObjectURL(url);
    notify(`${rows.length}건 CSV로 내보냈습니다. (최대 2,000건)`);
  }catch(e){notify(e.message);}
});
$('theme-toggle').addEventListener('click',()=>{document.body.dataset.theme=document.body.dataset.theme==='dark'?'light':'dark';localStorage.setItem('secom_theme',document.body.dataset.theme);});
document.body.dataset.theme=localStorage.getItem('secom_theme')==='dark'?'dark':'light';
$('access-token').value=state.token;
initialize();
