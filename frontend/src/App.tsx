import { useState } from "react";

type Condition = { id:number; field:string; op:string; value:string };
type Group = { id:number; logic:"AND"|"OR"; conditions:Condition[] };

const fields = [
  ["brand","Марка"],["model","Модель"],["generation","Поколение"],["body_type","Кузов"],
  ["year","Год"],["price_rub","Цена"],["mileage_km","Пробег"],["displacement_l","Объём"],
  ["cylinders","Цилиндры"],["power_hp","Мощность"],["fuel","Топливо"],["transmission","Коробка"],
  ["drivetrain","Привод"],["aspiration","Наддув"],["region","Регион"],["text","Текст объявления"]
];
const ops = [["eq","="],["ne","≠"],["gt",">"],["gte","≥"],["lt","<"],["lte","≤"],["contains","содержит"],["not_contains","не содержит"],["in","один из"],["not_in","не один из"],["between","между"],["exists","заполнено"]];
const sources=["autoru","avito","drom"];

export default function App() {
  const [groups,setGroups]=useState<Group[]>([{id:1,logic:"AND",conditions:[{id:1,field:"brand",op:"eq",value:""}]}]);
  const [sourceState,setSourceState]=useState<Record<string,boolean>>({autoru:true,avito:true,drom:true});
  const [status,setStatus]=useState("Готов к поиску");
  const [results,setResults]=useState<any[]>([]);

  const addCondition=(gid:number)=>{
    setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:[...g.conditions,{id:Date.now(),field:"model",op:"eq",value:""}]}:g));
  };
  const removeCondition=(gid:number,cid:number)=>{
    setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.filter(c=>c.id!==cid)}:g).filter(g=>g.conditions.length||gs.length===1));
  };
  const updateCondition=(gid:number,cid:number,key:keyof Condition,value:string)=>{
    setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.map(c=>c.id===cid?{...c,[key]:value}:c)}:g));
  };
  const addGroup=()=>setGroups(gs=>[...gs,{id:Date.now(),logic:"AND",conditions:[{id:Date.now()+1,field:"model",op:"eq",value:""}]}]);
  const removeGroup=(gid:number)=>setGroups(gs=>gs.length>1?gs.filter(g=>g.id!==gid):gs);
  const buildQuery=()=>{
    const params=new URLSearchParams();
    const selected=Object.entries(sourceState).filter(([,v])=>v).map(([k])=>k);
    selected.forEach(x=>params.append("sources",x));
    params.set("limit","50");
    params.set("filters",JSON.stringify({logic:"and",conditions:groups.map(g=>({logic:g.logic.toLowerCase(),conditions:g.conditions.filter(c=>c.value||c.op==="exists").map(c=>({field:c.field,operator:c.op,value:c.op==="between"?c.value.split(",").map(Number):c.value}))}))}));
    return params;
  };
  async function search(){
    setStatus("Ищу по источникам…");
    try {
      const r=await fetch("/api/search?"+buildQuery().toString());
      if(!r.ok) throw new Error();
      const data=await r.json();
      setResults(data.listings||[]);
      setStatus(`Найдено: ${data.total}`);
    } catch { setResults([]); setStatus("Поиск собран. Реальные объявления подключим следующим этапом."); }
  }

  return <main>
    <header><div className="logo">CAR<span>HUNTER</span></div><div className="status">{status}</div></header>
    <section className="hero"><h1>Найди машину<br/><em>без ограничений.</em></h1><p>Условия можно комбинировать как угодно: AND / OR, диапазоны, исключения и вложенные группы.</p></section>
    <section className="panel">
      <div className="sources"><b>Источники</b>{sources.map(x=><label key={x}><input type="checkbox" checked={sourceState[x]} onChange={e=>setSourceState({...sourceState,[x]:e.target.checked})}/>{x}</label>)}</div>
      {groups.map((g,gi)=><div className="filterGroup" key={g.id}>
        <div className="groupHead"><select value={g.logic} onChange={e=>setGroups(gs=>gs.map(x=>x.id===g.id?{...x,logic:e.target.value as "AND"|"OR"}:x))}><option>AND</option><option>OR</option></select><span>Группа условий {gi+1}</span><button className="ghost" onClick={()=>removeGroup(g.id)}>Удалить группу</button></div>
        {g.conditions.map((c,ci)=><div className="condition" key={c.id}>
          <select value={c.field} onChange={e=>updateCondition(g.id,c.id,"field",e.target.value)}>{fields.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
          <select value={c.op} onChange={e=>updateCondition(g.id,c.id,"op",e.target.value)}>{ops.map(([v,l])=><option key={v} value={v}>{l}</option>)}</select>
          {c.op!=="exists"&&<input placeholder={c.op==="between"?"например: 4,8":"значение"} value={c.value} onChange={e=>updateCondition(g.id,c.id,"value",e.target.value)}/>}
          <button className="ghost danger" onClick={()=>removeCondition(g.id,c.id)}>×</button>
          {ci<g.conditions.length-1&&<span className="join">{g.logic}</span>}
        </div>)}
        <button className="secondary" onClick={()=>addCondition(g.id)}>+ Условие</button>
      </div>)}
      <div className="actions"><button className="secondary" onClick={addGroup}>+ Группа</button><button onClick={search}>ИСКАТЬ</button></div>
    </section>
    <section className="results"><h2>Результаты</h2>{results.length===0?<p className="muted">Пока пусто. Реальные адаптеры источников будут подключены после конструктора поиска.</p>:results.map((x,i)=><article key={x.source+x.source_id+i}><b>{x.title}</b><span>{x.price_rub?.toLocaleString("ru-RU")} ₽</span><small>{x.year} · {x.mileage_km?.toLocaleString("ru-RU")} км · {x.source}</small></article>)}</section>
  </main>
}