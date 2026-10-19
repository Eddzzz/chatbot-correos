import {useEffect, useRef} from 'react';
import './postalMascot.css';

export function PostalMascot() {
  const video = useRef<HTMLVideoElement>(null);
  useEffect(()=>{
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = ()=>{
      if (!video.current) return;
      video.current.autoplay = !preference.matches;
      if (preference.matches) video.current.pause();
      else void video.current.play().catch(()=>{/* The first pose remains as a fallback. */});
    };
    update();
    preference.addEventListener('change',update);
    return ()=>preference.removeEventListener('change',update);
  },[]);
  return <div className="postal-thinking" role="status" aria-live="polite">
    <div className="thinking-frames" aria-hidden="true">
      <video ref={video} src="/cartero-thinking-v2-24fps.webm" autoPlay loop muted playsInline
        onPlaying={event=>{event.currentTarget.dataset.playing='true';}}
        onError={event=>{delete event.currentTarget.dataset.playing;}}/>
    </div>
    <div className="thinking-copy">
      <strong>Construyendo tu respuesta</strong>
      <span>Estoy pensando en tu consulta<span className="thinking-dots" aria-hidden="true"><i/><i/><i/></span></span>
    </div>
  </div>;
}
