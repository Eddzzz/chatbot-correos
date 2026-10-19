import type {CSSProperties, ReactNode} from 'react';

export function Brand() {
  return <div className="brand"><img src="/correos-bolivia-transparent.png" alt="Correos de Bolivia" width="2170" height="725"/><span>ASISTENTE POSTAL</span></div>;
}

export function Icon({name, size=20}: {name:string;size?:number}) {
  const paths:Record<string,ReactNode> = {
    search:<><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
    plus:<path d="M12 5v14M5 12h14"/>,
    chat:<path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0Z"/>,
    arrow:<path d="M7 17 17 7M7 7h10v10"/>,
    send:<path d="m6 11 6-6 6 6M12 5v15"/>,
    box:<><path d="m12 3 9 5-9 5-9-5 9-5ZM3 8v9l9 5 9-5V8M12 13v9M7.5 5.5l9 5"/></>,
    pin:<><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/><circle cx="12" cy="10" r="2.5"/></>,
    chart:<><path d="M4 4v16h16M9 15v-4M14 15V7M19 15v-6"/></>,
    shield:<><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Z"/><path d="m8 12 3 3 5-6"/></>,
    moon:<path d="M20.5 13A8.5 8.5 0 0 1 11 3.5 8.5 8.5 0 1 0 20.5 13Z"/>,
    sun:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/></>,
    menu:<path d="M4 6h16M4 12h16M4 18h16"/>,
    close:<path d="m6 6 12 12M6 18 18 6"/>,
    exit:<><path d="M9 4H4v16h5M10 12h11m-4-4 4 4-4 4"/></>,
    key:<><circle cx="8" cy="9" r="4"/><path d="m11 12 9 9m-5-5 3-3m-6 0 3-3"/></>,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name] || paths.chat}</svg>;
}

export function ThemeToggle({theme,onToggle}: {theme:'light'|'dark';onToggle:()=>void}) {
  return <button type="button" className="theme-toggle" onClick={onToggle} aria-label={theme==='dark' ? 'Activar modo claro' : 'Activar modo oscuro'} title={theme==='dark' ? 'Modo claro' : 'Modo oscuro'}><Icon name={theme==='dark' ? 'sun' : 'moon'}/></button>;
}

export function PostalMotion({large=false}: {large?:boolean}) {
  return <div className={`postal-motion ${large ? 'large' : ''}`} aria-hidden="true">
    <div className="orbit orbit-one"/><div className="orbit orbit-two"/>
    <span className="orbit-point point-one"/><span className="orbit-point point-two"/>
    <div className="glass-envelope"><svg viewBox="0 0 120 90" fill="none"><rect x="10" y="16" width="100" height="63" rx="13"/><path d="m13 22 39 29a14 14 0 0 0 16 0l39-29M14 74l29-26m63 26L77 48"/></svg><span className="envelope-spark">✦</span></div>
    <span className="motion-dash dash-one"/><span className="motion-dash dash-two"/>
  </div>;
}

export function Ambient() {
  return <div className="ambient" aria-hidden="true"><div className="ambient-blue"/><div className="ambient-gold"/><div className="postal-grid"/>{[0,1,2].map(i=><span key={i} className="route-line" style={{'--route':i} as CSSProperties}/>)}</div>;
}
