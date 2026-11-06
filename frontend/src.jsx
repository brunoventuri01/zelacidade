import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';

function App(){
  const [items,setItems]=useState([]); const [form,setForm]=useState({kind:'Buraco',description:'',latitude:'',longitude:''});
  const load=()=>fetch('/api/v1/occurrences').then(r=>r.json()).then(setItems);
  useEffect(load,[]);
  async function submit(e){e.preventDefault(); const body={...form,latitude:form.latitude?+form.latitude:null,longitude:form.longitude?+form.longitude:null}; await fetch('/api/v1/occurrences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); setForm({...form,description:''}); load();}
  return <main><header><span>🏙️</span><div><h1>ZelaCidade</h1><p>Cuidar da cidade começa por enxergar seus problemas.</p></div></header><section className="card"><h2>Registrar ocorrência</h2><form onSubmit={submit}><input value={form.kind} onChange={e=>setForm({...form,kind:e.target.value})} placeholder="Tipo" required/><textarea value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Descreva o problema" required/><div><input value={form.latitude} onChange={e=>setForm({...form,latitude:e.target.value})} placeholder="Latitude"/><input value={form.longitude} onChange={e=>setForm({...form,longitude:e.target.value})} placeholder="Longitude"/></div><button>Enviar ocorrência</button></form></section><section><h2>Ocorrências recentes</h2><div className="grid">{items.map(x=><article key={x.id}><b>{x.kind}</b><p>{x.description}</p><small>{new Date(x.created_at).toLocaleString('pt-BR')} · {x.source}</small></article>)}</div></section><footer>Global Solution 2026.2 · FIAP</footer></main>}
createRoot(document.getElementById('root')).render(<App/>);
