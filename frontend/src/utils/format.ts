export const number=(v:number|null|undefined,d=3)=>v==null?'不可估计':v.toFixed(d);
export const percent=(v:number|null)=>v==null?'不可估计':(v*100).toFixed(1)+'%';
export const date=(v:string)=>new Date(v).toLocaleString('zh-CN',{hour12:false});
