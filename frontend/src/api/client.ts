export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const token=localStorage.getItem('panel-token');
 const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',...(token?{'Authorization':'Bearer '+token}:{}),...options.headers}});
 if(!response.ok){let detail='请求失败';try{const data=await response.json();detail=typeof data.detail==='string'?data.detail:JSON.stringify(data.detail)}catch{};throw new Error(detail)}
 return response.json();
}
export const post=<T>(path:string,data:unknown)=>request<T>(path,{method:'POST',body:JSON.stringify(data)});
export async function downloadReport(id:string){const r=await fetch('/api/reports/'+id+'/csv',{headers:{Authorization:'Bearer '+localStorage.getItem('panel-token')}});if(!r.ok)throw new Error('下载失败');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download='songting-agreement.csv';a.click();URL.revokeObjectURL(url)}
