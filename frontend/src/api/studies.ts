import {request,post} from './client';import type {Study} from '../types/domain';
export const list=()=>request<Study[]>('/studies');
export const create=(data:unknown)=>post<Study>('/studies',data);
