import type {User} from '../types/domain';
export function readUser():User|null{try{return JSON.parse(localStorage.getItem('panel-user')||'null')}catch{return null}}
export function saveSession(token:string,user:User){localStorage.setItem('panel-token',token);localStorage.setItem('panel-user',JSON.stringify(user))}
export function clearSession(){localStorage.removeItem('panel-token');localStorage.removeItem('panel-user')}
