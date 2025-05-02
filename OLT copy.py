# app.py
from flask import Flask, jsonify, render_template_string
import requests
import urllib3
import logging
from datetime import datetime


mes_atual = datetime.now().strftime('%Y%m')
# Suprimir logs do werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br" data-theme="light">
<head>
  <meta charset="UTF-8">
  <title>OLT Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>
  <style>
    :root {
      --primary: #0D47A1;
      --secondary: #1e85e5;
      --bg: #ECEFF1;
      --text: #263238;
      --hover: rgba(13,71,161,0.15);
      --shadow: rgba(0,0,0,0.1);
      --panel: #ffffff;
      --texto: #fff;
    }
    [data-theme="dark"] {
      --bg: #2C2C2C;
      --primary: #1a9eca;
      --secondary: #1ee2e5;
      --text: #FFFFFF;
      --hover: rgba(255,255,255,0.1);
      --shadow: rgba(0,0,0,0.2);
      --panel: #3A3A3A;
      --texto: #263238;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; padding-top: 60px;
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', sans-serif;
    }
    header {
      background: var(--primary);
      color: #fff;
      position: fixed; top: 0; width: 100%; z-index: 100;
      display: flex; align-items: center; justify-content: space-between;
      padding: 0.75rem 1.5rem;
      box-shadow: 0 2px 4px var(--shadow);
    }
    header .title {
      font-size: 1.4rem; font-weight: 600;
      display: flex; align-items: center;
    }
    header .title i { margin-right: 0.5rem; }
    #themeToggle {
      background: none; border: none;
      color: #fff; font-size: 1.2rem;
      cursor: pointer;
    }
    .container-fluid { padding: 2rem 1rem; }
    .filters {
      display: flex; flex-wrap: wrap;
      gap: 1rem; margin-bottom: 1.5rem;
      background: var(--panel);
      padding: 1rem; border-radius: 0.75rem;
      box-shadow: 0 2px 6px var(--shadow);
      align-items: center;
    }
    .filters .form-control,
    .filters .form-select {
      flex: 1; min-width: 180px;
      border-radius: 0.5rem;
      transition: 0.2s;
    }
    .filters .form-control:focus,
    .filters .form-select:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(13,71,161,0.15);
    }
    .btn-reset, .btn-export {
      background: var(--secondary); color: var(--texto);
      border: none; border-radius: 0.5rem;
      padding: 0.6rem 1rem;
    }
    .btn-reset:hover, .btn-export:hover {
      background: #00a9e6;
    }
    .table-wrapper {
      background: var(--panel);
      border-radius: 0.75rem;
      box-shadow: 0 2px 6px var(--shadow);
      overflow-x: auto;
    }
    table {
      width: 100%; border-collapse: collapse;
      margin: 0;
    }
    thead {
      background: var(--primary);
      color: #fff;
      cursor: pointer;
    }
    th, td {
      padding: 0.75rem 1rem;
      text-align: left;
      border-bottom: 1px solid var(--hover);
      font-size: 0.95rem;
    }
    tbody tr:hover { background: var(--hover); }
    td.status-down { color: #b00020; font-weight: 600; }
    td.status-up { color: #2e7d32; font-weight: 600; }
    td.reboot-true { color: #2e7d32; font-weight: 500; }
    td.reboot-false { color: #b00020; font-weight:
    .pagination {
      display: flex;
      justify-content: center;
      margin-top: 1rem;
      gap: 0.5rem;
    }
    .pagination button {
      padding: 0.5rem 0.75rem;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 0.5rem;
    }
    .pagination button.disabled {
      background: grey;
      cursor: not-allowed;
    }
                                  
  </style>
</head>
<body>
<header>
  <div class="title"><i class="fas fa-network-wired"></i>OLT Dashboard</div>
  <div>
    <button id="themeToggle"><i class="fas fa-moon"></i></button>
    <button id="beepToggle"><i class="fas fa-volume-up"></i></button>
  </div>
</header>

<div class="container-fluid">
  <div class="filters">
    <input id="filter-olt" class="form-control" placeholder="Filtrar OLT">
    <select id="filter-status" class="form-select">
      <option value="">Todos os status</option>
      <option value="DOWN">DOWN</option>
      <option value="UP">Normalizado</option>
    </select>
    <button class="btn-reset" onclick="resetFilters()">Limpar Filtros</button>
    <button class="btn-export" onclick="exportTable()">Baixar XLSX</button>
  </div>

  <div class="table-wrapper">
    <table id="olt-table">
      <thead>
        <tr>
          <th>Status</th><th>OLT</th><th>Modelo</th>
          <th id="sort-date">Data Queda &#x25BC;</th><th>Reboot</th><th>Normalizado</th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
  <div class="pagination" id="pagination"></div>
</div>

<script>
let allData = [], currentPage=1, rowsPerPage=10, sortAsc=false;
let beepAtivado=true, oldDown=new Set();

function formatarDataHora(d){
  if(!d) return '—';
  const dt=new Date(d);
  return dt.toLocaleDateString('pt-BR')+' '+dt.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
}

function beep(){
  if(!beepAtivado) return;
  const ctx=new (window.AudioContext||window.webkitAudioContext)();
  const osc=ctx.createOscillator(), gain=ctx.createGain();
  osc.type='sine';
  osc.frequency.setValueAtTime(400,ctx.currentTime);
  gain.gain.setValueAtTime(0.1,ctx.currentTime);
  osc.connect(gain); gain.connect(ctx.destination);
  osc.start(); osc.stop(ctx.currentTime+2);
}

function updateTable(){
  const tbody=document.querySelector('#olt-table tbody');
  const fO=filterOlt.value.toLowerCase(), fS=filterStatus.value;
  tbody.innerHTML='';
  let filt=allData.filter(r=>(!fO||r.olt.toLowerCase().includes(fO))&&(!fS||r.status===fS))
    .sort((a,b)=>{
      const da=new Date(a.data_queda), db=new Date(b.data_queda);
      return sortAsc?da-db:db-da;
    });
  const total=Math.ceil(filt.length/rowsPerPage);
  const start=(currentPage-1)*rowsPerPage;
  filt.slice(start,start+rowsPerPage).forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML=`
      <td class="status">${r.status==='DOWN'?'<i class="fas fa-circle text-danger me-1"></i>DOWN':'<i class="fas fa-circle text-success me-1"></i>UP'}</td>
      <td>${r.olt}</td><td>${r.modelo}</td>
      <td>${formatarDataHora(r.data_queda)}</td>
      <td class="${r.reboot==='true'?'reboot-true':'reboot-false'}">${r.reboot||'—'}</td>
      <td>${formatarDataHora(r.normalizado_em)}</td>`;
    tbody.appendChild(tr);
  });
  renderPagination(total);
}

function renderPagination(total){
  const p=document.getElementById('pagination'); p.innerHTML='';
  for(let i=1;i<=total;i++){
    const btn=document.createElement('button');
    btn.textContent=i;
    if(i===currentPage) btn.classList.add('disabled');
    btn.onclick=()=>{currentPage=i;updateTable();};
    p.appendChild(btn);
  }
}

function resetFilters(){ filterOlt.value=''; filterStatus.value=''; currentPage=1; updateTable(); }

async function fetchData(){
  const res=await fetch('/api/status'), data=await res.json();
  const downNow=new Set(data.filter(d=>d.status==='DOWN').map(d=>d.olt));
  for(let olt of downNow){
    if(!oldDown.has(olt)){
      beep();
      oldDown.add(olt);
      if(Notification.permission==='granted')
        new Notification('OLT DOWN',{body:`${olt} caiu!`});
    }
  }
  oldDown=new Set(downNow);
  allData=data; updateTable();
}

document.getElementById('sort-date').onclick=()=>{ sortAsc=!sortAsc; updateTable(); };
document.getElementById('themeToggle').onclick=()=>{
  const cur=document.documentElement.getAttribute('data-theme');
  const nxt=cur==='dark'?'light':'dark';
  document.documentElement.setAttribute('data-theme',nxt);
  localStorage.setItem('theme',nxt);
};
document.getElementById('beepToggle').onclick=()=>{
  beepAtivado=!beepAtivado;
  const ic=document.getElementById('beepToggle').querySelector('i');
  ic.classList.toggle('fa-volume-up');
  ic.classList.toggle('fa-volume-mute');
};
if(localStorage.getItem('theme'))
  document.documentElement.setAttribute('data-theme',localStorage.getItem('theme'));
if(Notification.permission!=='granted')
  Notification.requestPermission();

fetchData();
setInterval(fetchData,1000);

const filterOlt=document.getElementById('filter-olt');
const filterStatus=document.getElementById('filter-status');
filterOlt.oninput=()=>{currentPage=1;updateTable();};
filterStatus.onchange=()=>{currentPage=1;updateTable();};

function exportTable(){
  const ws=XLSX.utils.json_to_sheet(allData.map(r=>({
    Status:r.status, OLT:r.olt, Modelo:r.modelo,
    "Data Queda":formatarDataHora(r.data_queda),
    Reboot:r.reboot||'—',
    Normalizado:formatarDataHora(r.normalizado_em)
  })));
  const wb=XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb,ws,'OLTs');
  XLSX.writeFile(wb,'olts_dashboard.xlsx');
}
</script>
</body>
</html>
""")

@app.route('/api/status')
def get_status():
    try:
        url = f"https://cactiagregador.telesp.net.br/cacti/statusOlt/statusOlt-{mes_atual}.txt"
        resp = requests.get(url, verify=False)
        linhas = resp.text.strip().splitlines()
        olts = {}
        for l in linhas:
            partes = l.split(';')
            if len(partes) < 5: continue
            status, data, nome, reboot, modelo = partes
            reboot_value = reboot.split('_')[1].lower() if 'REBOOT_' in reboot else None
            if status == 'DOWN':
                olts[nome] = dict(status='DOWN', data_queda=data, olt=nome,
                                  reboot='', modelo=modelo, normalizado_em='')
            elif status == 'UP' and nome in olts:
                olts[nome].update(status='UP', normalizado_em=data, reboot=reboot_value)
        resultado = sorted(olts.values(), key=lambda x: x['data_queda'], reverse=True)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)