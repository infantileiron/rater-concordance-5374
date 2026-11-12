import {useCallback,useEffect,useState} from 'react';
import {loadWorkspace,Workspace} from '../stores/workspace';
export function useWorkspace(){const [data,setData]=useState<Workspace>({datasets:[],scales:[],studies:[],runs:[],reviews:[],reports:[],audit:[]});const [error,setError]=useState('');const [loading,setLoading]=useState(true);
const refresh=useCallback(async()=>{try{setData(await loadWorkspace());setError('')}catch(e){setError((e as Error).message)}finally{setLoading(false)}},[]);
useEffect(()=>{refresh();const timer=setInterval(refresh,2500);return()=>clearInterval(timer)},[refresh]);return {data,error,loading,refresh,setError};}
