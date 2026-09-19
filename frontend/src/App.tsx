import { useEffect, useState } from "react";

type FieldMeta={field:string;label:string;type:string;unit?:string;operators:string[];options?:{value:string;label:string}[]};
type Condition={id:number;field:string;op:string;value:string};
type Group={id:number;logic:"AND"|"OR";conditions:Condition[]};
type Listing={source:string;source_id:string;url:string;title:string;price_rub?:number;year?:number;mileage_km?:number;brand?:string;model?:string;trim?:string;body_type?:string;engine_layout?:string;displacement_l?:number;power_hp?:number;torque_nm?:number;fuel?:string;transmission?:string;drivetrain?:string;seller_name?:string;seller_type?:string;region?:string;images?:string[]};
type CatalogNode={id:string;name:string;level:string;offers_count:number;mark_id?:string;mark_name?:string;model_id?:string;model_name?:string;generation_id?:string;generation_name?:string;generation_year_from?:number;generation_year_to?:number;generation_restyle?:boolean;configuration_id?:string;configuration_name?:string;body_type?:string;doors_count?:number;photo_url?:string;tech_params?:{engine_type?:string;displacement?:number;gear_type?:string;transmission?:string;power?:number;year_start?:number;year_stop?:number;human_name?:string}};
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
  const [catalog,setCatalog]=useState<CatalogNode[]>([]);
  const [selected,setSelected]=useState({mark:"",model:"",generation:"",configuration:"",tech:""});
  const [selectedNames,setSelectedNames]=useState({mark:"",model:"",generation:"",configuration:""});
  const [catalogLoading,setCatalogLoading]=useState(false);
  const [sourceCaps,setSourceCaps]=useState<Record<string,{listing_search:boolean;catalog:boolean}>>({});
  const [dromUrl,setDromUrl]=useState("");
  const [dromNative,setDromNative]=useState<Record<string,number>>({});

  useEffect(()=>{
    fetch("/api/filter-fields").then(r=>r.json()).then(setFields).catch(()=>setStatus("Не удалось загрузить каталог фильтров"));
    fetch("/api/source-capabilities").then(r=>r.json()).then(setSourceCaps).catch(()=>{});
    loadCatalog([]);
  },[]);

  async function loadCatalog(lookup:string[]){
    setCatalogLoading(true);
    try{
      const qs=lookup.length?"?bc_lookup="+encodeURIComponent(lookup.join("#")):"";
      const r=await fetch("/api/catalog/autoru"+qs);
      if(!r.ok) throw new Error();
      const data=await r.json(); setCatalog(data.nodes||[]);
    }catch{setCatalog([]);setStatus("Auto.ru каталог недоступен: нужен AUTORU_API_TOKEN");}
    finally{setCatalogLoading(false);}
  }
  const level=(l:string)=>catalog.filter(x=>x.level===l);
  const choose=(key:keyof typeof selected,value:string)=>{
    const next={...selected,[key]:value};
    if(key==="mark") Object.assign(next,{model:"",generation:"",configuration:"",tech:""});
    if(key==="model") Object.assign(next,{generation:"",configuration:"",tech:""});
    if(key==="generation") Object.assign(next,{configuration:"",tech:""});
    if(key==="configuration") Object.assign(next,{tech:""});
    setSelected(next);
    const picked=catalog.find(x=>x.id===value);
    const names={...selectedNames,[key]:picked?.name||""};
    if(key==="mark") Object.assign(names,{model:"",generation:"",configuration:""});
    if(key==="model") Object.assign(names,{generation:"",configuration:""});
    if(key==="generation") Object.assign(names,{configuration:""});
    setSelectedNames(names);
    const lookup=[next.mark,next.model,next.generation,next.configuration].filter(Boolean);
    loadCatalog(lookup);
  };
  const selectedTech=catalog.find(x=>x.id===selected.tech);
  const meta=(field:string)=>fields.find(x=>x.field===field);
  const addCondition=(gid:number)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:[...g.conditions,{id:Date.now(),field:fields[0]?.field||"brand",op:"eq",value:""}]}:g));
  const removeCondition=(gid:number,cid:number)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.filter(c=>c.id!==cid)}:g).filter(g=>g.conditions.length||gs.length===1));
  const updateCondition=(gid:number,cid:number,key:keyof Condition,value:string)=>setGroups(gs=>gs.map(g=>g.id===gid?{...g,conditions:g.conditions.map(c=>c.id===cid?{...c,[key]:value,...(key==="field"?{op:"eq",value:""}:{})}:c)}:g));
  const addGroup=()=>setGroups(gs=>[...gs,{id:Date.now(),logic:"AND",conditions:[{id:Date.now()+1,field:fields[0]?.field||"brand",op:"eq",value:""}]}]);
  const removeGroup=(gid:number)=>setGroups(gs=>gs.length>1?gs.filter(g=>g.id!==gid):gs);

  async function search(){
    setStatus("Ищу по источникам…");
    const conditions=groups.flatMap(g=>g.conditions.filter(c=>c.value||c.op==="exists").map(c=>({field:c.field,operator:c.op,value:c.op==="between"?c.value.split(",").map(Number):c.value})));
    if(selectedNames.mark) conditions.push({field:"brand",operator:"eq",value:selectedNames.mark});
    if(selectedNames.model) conditions.push({field:"model",operator:"eq",value:selectedNames.model});
    if(selectedNames.generation) conditions.push({field:"generation",operator:"eq",value:selectedNames.generation});
    try{
      const r=await fetch("/api/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({sources:Object.entries(sourceState).filter(([,v])=>v).map(([k])=>k),limit:50,source_params:{drom:dromNative},filters:{logic:"and",conditions}})});
      if(!r.ok) throw new Error();
      const data=await r.json(); setResults(data.listings||[]); setStatus(`Найдено: ${data.total}`);
    }catch{setResults([]);setStatus("Ошибка запроса к API");}
  }

  return <main>
    <header><div className="logo">CAR<span>HUNTER</span></div><div className="status">{status}</div></header>
    <section className="hero"><h1>Найди машину<br/><em>без ограничений.</em></h1><p>Единый поиск по автомобильным площадкам с нормализованными фильтрами.</p></section>
    <section className="panel">
      <div className="sources"><b>Источники</b>{sources.map(x=><label key={x}><input type="checkbox" checked={sourceState[x]} disabled={sourceCaps[x]&&!sourceCaps[x].listing_search} onChange={e=>setSourceState({...sourceState,[x]:e.target.checked})}/>{labels[x]}{sourceCaps[x]&&!sourceCaps[x].listing_search?" · каталог":""}</label>)}</div>

      <div className="catalogPicker">
        <div className="groupHead"><span>Каталог Drom</span><small>вставь публичную ссылку Drom для извлечения native ID</small></div>
        <div className="condition"><input placeholder="https://auto.drom.ru/bmw/5-series/" value={dromUrl} onChange={e=>setDromUrl(e.target.value)}/><button className="secondary" onClick={async()=>{try{const r=await fetch("/api/catalog/drom?url="+encodeURIComponent(dromUrl));if(!r.ok)throw new Error();const n=(await r.json()).nodes?.[0];const raw=n?.raw||{};setDromNative(Object.fromEntries(Object.entries(raw).filter(([k])=>["firmId","modelId","generationNumber","restylingNumber"].includes(k)&&typeof raw[k]==="number")));setStatus("Drom ID получены");}catch{setStatus("Не удалось разобрать Drom-ссылку")}}}>Разобрать</button></div>
        {Object.keys(dromNative).length>0&&<div className="listingSpecs">{Object.entries(dromNative).map(([k,v])=><span key={k}>{k}: {v}</span>)}</div>}
        <div className="groupHead"><span>Каталог Auto.ru</span><small>{catalogLoading?"Загрузка…":catalog.length?`${catalog.length} вариантов`:""}</small></div>
        <div className="condition">
          <select value={selected.mark} onChange={e=>choose("mark",e.target.value)}><option value="">Марка</option>{level("mark").map(x=><option key={x.id} value={x.id}>{x.name} · {fmt(x.offers_count)}</option>)}</select>
          <select value={selected.model} disabled={!selected.mark} onChange={e=>choose("model",e.target.value)}><option value="">Модель</option>{level("model").filter(x=>!selected.mark||x.mark_id===selected.mark).map(x=><option key={x.id} value={x.id}>{x.name} · {fmt(x.offers_count)}</option>)}</select>
          <select value={selected.generation} disabled={!selected.model} onChange={e=>choose("generation",e.target.value)}><option value="">Поколение</option>{level("generation").filter(x=>!selected.model||x.model_id===selected.model).map(x=><option key={x.id} value={x.id}>{x.name}{x.generation_year_from?` · ${x.generation_year_from}–${x.generation_year_to||"н.в."}`:""} · {fmt(x.offers_count)}</option>)}</select>
          <select value={selected.configuration} disabled={!selected.generation} onChange={e=>choose("configuration",e.target.value)}><option value="">Кузов / конфигурация</option>{level("configuration").filter(x=>!selected.generation||x.generation_id===selected.generation).map(x=><option key={x.id} value={x.id}>{x.configuration_name||x.name} · {fmt(x.offers_count)}</option>)}</select>
          <select value={selected.tech} disabled={!selected.configuration} onChange={e=>setSelected({...selected,tech:e.target.value})}><option value="">Двигатель / КПП</option>{level("tech_param").filter(x=>!selected.configuration||x.configuration_id===selected.configuration).map(x=><option key={x.id} value={x.id}>{x.tech_params?.human_name||x.name} · {fmt(x.offers_count)}</option>)}</select>
        </div>
        {selectedTech&&<div className="listingSpecs"><span>{selectedTech.tech_params?.engine_type||"—"}</span><span>{selectedTech.tech_params?.displacement?(`${selectedTech.tech_params.displacement/1000} л`):"—"}</span><span>{selectedTech.tech_params?.power?`${selectedTech.tech_params.power} л.с.`:"—"}</span><span>{selectedTech.tech_params?.transmission||"—"}</span><span>{selectedTech.offers_count} объявлений</span></div>}
      </div>

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
      {results.length===0?<p className="muted">Выбери машину в каталоге или добавь фильтры. Реальные объявления подключаются отдельным адаптером источника.</p>:
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
