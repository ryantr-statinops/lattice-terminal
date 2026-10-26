import {useState,type FormEvent} from 'react';
import {send} from './api';
import {Button} from './ui/buttons';
import {Field,TextInput} from './ui/fields';
import {InlineNotice} from './ui/feedback';

type CredentialField={name:string;value:string};

export function ProviderCredentialEditor({providerId,onCancel,onSaved}:{providerId:string;onCancel:()=>void;onSaved:()=>void}){
  const [service,setService]=useState('market-data');
  const [fields,setFields]=useState<CredentialField[]>([{name:'',value:''}]);
  const [pending,setPending]=useState(false);
  const [error,setError]=useState('');

  const updateField=(index:number,patch:Partial<CredentialField>)=>setFields(current=>current.map((field,i)=>i===index?{...field,...patch}:field));
  const submit=async(event:FormEvent<HTMLFormElement>)=>{
    event.preventDefault();
    const credential:Record<string,string>=Object.create(null) as Record<string,string>;
    for(const field of fields){
      const name=field.name.trim();
      if(!name||!field.value){setError('Enter a field name and value for every credential row.');return;}
      if(Object.hasOwn(credential,name)){setError('Credential field names must be unique.');return;}
      credential[name]=field.value;
    }
    setPending(true);setError('');
    try{
      await send(`/providers/${encodeURIComponent(providerId)}/credentials`,{service:service.trim(),credential},'PUT');
      setFields(current=>current.map(field=>({...field,value:''})));
      onSaved();
    }catch(reason){setError(reason instanceof Error?reason.message:String(reason));}
    finally{setPending(false);}
  };

  return <form className="provider-credential-editor" onSubmit={event=>void submit(event)}>
    <p className="muted">Saved in the local encrypted vault. Saving an existing provider/service replaces its credential. Values are never prefilled or returned, and saving does not verify provider access.</p>
    <Field label="Provider service key" hint="Use a short key such as market-data or account-read.">
      <TextInput autoComplete="off" maxLength={64} pattern="[a-z0-9][a-z0-9._-]{0,63}" required value={service} onChange={event=>setService(event.target.value)}/>
    </Field>
    {fields.map((field,index)=><div className="provider-credential-row" key={index}>
      <Field label={`Credential field ${index+1}`}>
        <TextInput autoComplete="off" maxLength={64} placeholder="Field name" required value={field.name} onChange={event=>updateField(index,{name:event.target.value})}/>
      </Field>
      <Field label={`Credential value ${index+1}`}>
        <TextInput type="password" autoComplete="new-password" required value={field.value} onChange={event=>updateField(index,{value:event.target.value})}/>
      </Field>
      {fields.length>1&&<Button type="button" aria-label={`Remove credential field ${index+1}`} onClick={()=>setFields(current=>current.filter((_,i)=>i!==index))}>Remove</Button>}
    </div>)}
    <div className="provider-credential-actions">
      <Button type="button" onClick={()=>setFields(current=>[...current,{name:'',value:''}])}>Add field</Button>
      <Button type="button" onClick={onCancel}>Cancel</Button>
      <Button type="submit" variant="primary" pending={pending}>Save credentials</Button>
    </div>
    {error&&<InlineNotice tone="negative">{error}</InlineNotice>}
  </form>;
}
