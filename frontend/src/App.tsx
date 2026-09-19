import { useState } from "react";

const fields = [
  ["brand","Марка"],["model","Модель"],["generation","Поколение"],["body_type","Кузов"],
  ["price_min","Цена от"],["price_max","Цена до"],["year_min","Год от"],["year_max","Год до"],
  ["mileage_max","Пробег до"],["displacement_min_l","Объём от"],["displacement_max_l","Объём до"],
  ["power_min_hp","Мощность от"],["power_max_hp","Мощность до"],["region","Регион"]
];

export default function App() {
  const [values,setValues] = useState<Record<string,string>>({});
  const [status,setStatus] = useState("Готов к поиску");
  const update=(k:string,v:string)=>setValues({...values,[k]:v});
  async function search(){
    setStatus("Ищу по источникам…");
    const params=new URLSearchParams();
    Object.entries(values).filter(([,v])=>v).forEach(([k,v])=>params.set(k,v));
    params.set("limit","50");
    try {
      const r=await fetch("/api/search?"+params.toString());
      if(!r.ok) throw new Error();
      const data=await r.json();
      setStatus(`Найдено: ${data.total}`);
    } catch { setStatus("Backend пока не подключён к реальным объявлениям"); }
  }
  return <main>
    <header><div className="logo">CAR<span>HUNTER</span></div><div className="status">{status}</div></header>
    <section className="hero"><h1>Найди машину<br/><em>без ограничений.</em></h1><p>Единый поиск по автомобильным площадкам.</p></section>
    <section className="panel">
      <div className="sources"><b>Источники</b>{["autoru","avito","drom"].map(x=><label key={x}><input type="checkbox" defaultChecked/>{x}</label>)}</div>
      <div className="grid">{fields.map(([k,label])=><label key={k}>{label}<input value={values[k]||""} onChange={e=>update(k,e.target.value)} /></label>)}</div>
      <div className="row"><label>Топливо<select><option>Любое</option><option>Бензин</option><option>Дизель</option><option>Гибрид</option><option>Электро</option></select></label>
      <label>Привод<select><option>Любой</option><option>FWD</option><option>RWD</option><option>AWD</option></select></label>
      <label>Коробка<select><option>Любая</option><option>Автомат</option><option>Механика</option><option>Робот</option></select></label>
      <button onClick={search}>ИСКАТЬ</button></div>
    </section>
  </main>
}
