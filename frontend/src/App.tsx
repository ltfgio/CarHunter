import { useEffect, useState } from "react";

type FieldMeta={field:string;label:string;type:string;unit?:string;operators:string[];options?:{value:string;label:string}[]};
type Condition={id:number;field:string;op:string;value:string};
type Group={id:number;logic:"AND"|"OR";conditions:Condition[]};
type Listing={source:string;source_id:string;url:string;title:string;price_rub?:number;year?:number;mileage_km?:number;brand?:string;model?:string;trim?:string;body_type?:string;engine_layout?:string;displacement_l?:number;power_hp?:number;torque_nm?:number;fuel?:string;transmission?:string;drivetrain?:string;seller_name?:string;seller_type?:string;region?:string;images?:string[]};

const opLabels:Record<string,string>={eq:"=",ne:"≠",gt:">",gte:"≥",lt:"<",lte:"≤",contains:"содержит",not_contains:"не содержит",in:"один из",not_in:"не один из",between:"между",exists:"заполнено"};
const sources=["autoru","avito","drom"];
const labels:Record<string,string>={autoru:"Auto.ru",avito:"Avito",drom:"Drom",petrol:"бензин",diesel:"дизель",hybrid:"гибрид",electric:"электро",manual:"МКПП",automatic:"АКПП",robot:"робот",cvt:"CVT",fwd:"передний",rwd:"задний",awd:"полный",turbo:"турбо",twin_turbo:"битурбо",supercharger:"компрессор"};

function fmt(n?:number){return n==null?"—":n.toLocaleString("ru-RU");}
function engine(x:Listing){const bits=[x.displacement_l&&`${x.displacement_l} л`,x.engine_layout&&x.engine_layout.replaceAll("_"," "),x.power_hp&&`${x.power_hp} л.с.`].filter(Boolean);return bits.join(" · ")||"Двигатель не указан";}

export default function App(){
  const [fields,setFields]=useState<FieldMeta[]>([]);
  const [groups,setGroups]=useState<Group[]>([{id:1,logic:"AND",conditions:[{id:1,field:"brand",op:"eq",value:""}]}]);
  const [sourceState,setSourceState]=useState<Record<string,boolean>>({autoru:true,avito:true,drom:true});
  const [status,setStatus]=useState("Готов к поиску");
  const [results,setResults]=useState<Listing[]>([]);

  useEffect(()=>{fetch("/api/filter-fields").then(r=>r.json()).then(setFields).catch(()=>setStatus("Не удалось загрузить каталог фильтров"));},[]);
  const meta=(field:string)=>fields.find(x=>x.field===field);
  const addCondition=(gid:number)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:[...g.conditions,{id:Date.now(),field:fields[0]?.field||"brand",op:"eq",value:""}]}:g));
  const removeCondition=(gid:number,cid:number)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.filter(c=>c.id!==cid)}:g).filter(g=>g.conditions.length||gs.length===1));
  const updateCondition=(gid:number,cid:number,key:keyof Condition,value:string)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.map(c=>c.id===cid?{...c,[key]:value,...(key==="field"?{op:"eq",value:""}:{})}:c)}:g));
  const addGroup=()=>setGroups(gs=>[...gs,{id:Date.now(),logic:"AND",conditions:[{id:Date.now()+1,field:fields[0]?.field||"brand",op:"eq",value:""}]}]);
  const removeGroup=(gid:number)=>setGroups(gs=>gs.length>1?gs.filter(g=>g.id!==gid):gs);

  async function search(){
    setStatus("Ищу по источникам…");
    const filters={logic:"and",conditions:groups.map(g=>({logic:g.logic.toLowerCase(),conditions:g.conditions.filter(c=>c.value||c.op==="exists").map(c=>({field:c.field,operator:c.op,value:c.op==="between"?c.value.split(",").map(Number):c.value}))})).filter(g=>g.conditions.length)};
    try{
      const r=await fetch("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sources:Object.entries(sourceState).filter(([,v])=>v).map(([k])=>k),limit:50,filters})});
      if(!r.ok) throw new Error();
      const data=await r.json(); setResults(data.listings||[]); setStatus(`Найдено: ${data.total}`);
    }catch{setResults([]);setStatus("Ошибка запроса к API");}
  }

  return <main>
    <header><div className="logo">CAR<span>HUNTER</span></div><div className="status">{status}</div></header>
    <section className="hero"><h1>Найди машину<br/><em>без ограничений.</em></h1><p>Единый поиск по автомобильным площадкам с нормализованными фильтрами.</p></section>
    <section className="panel">
      <div className="sources"><b>Источники</b>{sources.map(x=><label key={x}><input type="checkbox" checked={sourceState[x]} onChange={e=>setSourceState({...sourceState,[x]:e.target.checked})}/>{labels[x]}</label>)}</div>
      {groups.map((g,gi)=><div className="filterGroup" key={g.id}>
        <div className="groupHead"><select value={g.logic} onChange={e=>setGroups(gs=>gs.map(x=>x.id===g.id?{...x,logic:e.target.value as "AND"|"OR"}:x))}><option>AND</option><option>OR</option></select><span>Группа условий {gi+1}</span><button className="ghost" onClick={()=>removeGroup(g.id)}>Удалить группу</button></div>
        {g.conditions.map((c,ci)=>{const m=meta(c.field);const opts=m?.options;return <div className="condition" key={c.id}>
          <select value={c.field} onChange={e=>updateCondition(g.id,c.id,"field",e.target.value)}>{fields.map(f=><option key={f.field} value={f.field}>{f.label}</option>)}</select>
          <select value={c.op} onChange={e=>updateCondition(g.id,c.id,"op",e.target.value)}>{(m?.operators||[]).map(o=><option key={o} value={o}>{opLabels[o]||o}</option>)}</select>
          {c.op!=="exists"&&(opts?<select value={c.value} onChange={e=>updateCondition(g.id,c.id,"value",e.target.value)}><option value="">Выберите…</option>{opts.map(o=><option key={o.value} value={o.value}>{o.label}</option>)}</select>:<input placeholder={c.op==="between"?"например: 4,8":m?.unit?"значение ("+m.unit+")":"значение"} value={c.value} onChange={e=>updateCondition(g.id,c.id,"value",e.target.value)}/>)}
          <button className="ghost danger" onClick={()=>removeCondition(g.id,c.id)}>×</button>{ci<g.conditions.length-1&&<span className="join">{g.logic}</span>}
        </div>})}
        <button className="secondary" onClick={()=>addCondition(g.id)}>+ Условие</button>
      </div>)}
      <div className="actions"><button className="secondary" onClick={addGroup}>+ Группа</button><button onClick={search}>ИСКАТЬ</button></div>
    </section>
    <section className="results"><div className="resultsHead"><h2>Результаты</h2><span>{results.length?results.length+" объявлений":""}</span></div>
      {results.length===0?<p className="muted">Пока пусто. Адаптеры Auto.ru, Avito и Drom подключим следующим этапом.</p>:
      results.map((x,i)=><article className="listingCard" key={x.source+x.source_id+i}>
        <div className="listingImage">{x.images?.[0]?<img src={x.images[0]} alt="" loading="lazy"/>:<span>NO PHOTO</span>}</div>
        <div className="listingBody"><div className="listingTop"><h3>{x.title}</h3><strong>{x.price_rub?fmt(x.price_rub)+" ₽":"Цена не указана"}</strong></div>
          <div className="listingSpecs"><span>{x.year||"—"} г.</span><span>{fmt(x.mileage_km)} км</span><span>{engine(x)}</span></div>
          <div className="listingSpecs"><span>{x.fuel?labels[x.fuel]||x.fuel:"—"}</span><span>{x.transmission?labels[x.transmission]||x.transmission:"—"}</span><span>{x.drivetrain?labels[x.drivetrain]||x.drivetrain:"—"}</span>{x.torque_nm&&<span>{fmt(x.torque_nm)} Н·м</span>}</div>
          <div className="listingMeta"><span>{x.seller_name||x.seller_type||"Продавец не указан"} · {x.region||"Регион не указан"}</span><a href={x.url} target="_blank" rel="noreferrer">{labels[x.source]||x.source} ↗</a></div>
        </div>
      </article>)}
    </section>
  </main>
}