import {useState} from 'react';
export function useAsync(){const [busy,setBusy]=useState(false);const [error,setError]=useState('');async function execute(fn:()=>Promise<unknown>){setBusy(true);setError('');try{await fn()}catch(e){setError((e as Error).message)}finally{setBusy(false)}}return {busy,error,execute}}
