import {useEffect,useRef} from 'react';
import {Icon} from '../../PostalUI';

export function DeleteChatDialog({title,busy,error,onCancel,onConfirm}: {
  title:string;busy:boolean;error:string;onCancel:()=>void;onConfirm:()=>void;
}) {
  const dialog=useRef<HTMLDialogElement>(null);
  const cancel=useRef<HTMLButtonElement>(null);
  useEffect(()=>{
    const opener=document.activeElement;
    const element=dialog.current!;
    element.showModal();
    cancel.current?.focus();
    return ()=>{
      element.close();
      if(opener instanceof HTMLElement && opener.isConnected) opener.focus();
      else document.querySelector<HTMLTextAreaElement>('#message')?.focus();
    };
  },[]);
  return <dialog ref={dialog} className="delete-chat-dialog" aria-labelledby="delete-chat-title" aria-describedby="delete-chat-description" aria-busy={busy} onCancel={event=>{event.preventDefault();if(!busy)onCancel();}}>
    <div className="delete-chat-heading">
      <div className="delete-chat-icon"><Icon name="trash" size={18}/></div>
      <h2 id="delete-chat-title">¿Eliminar este chat?</h2>
    </div>
    <p className="delete-chat-name">{title}</p>
    <p id="delete-chat-description">Se eliminarán todos los mensajes de esta conversación. Esta acción no se puede deshacer.</p>
    {error && <p className="delete-chat-error" role="alert">{error} Inténtalo de nuevo.</p>}
    <div className="delete-chat-actions">
      <button ref={cancel} type="button" className="delete-chat-cancel" disabled={busy} onClick={onCancel}>Cancelar</button>
      <button type="button" className="delete-chat-confirm" disabled={busy} onClick={onConfirm}>{busy ? 'Eliminando…' : 'Eliminar chat'}</button>
    </div>
  </dialog>;
}
