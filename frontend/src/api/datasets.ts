import {request,post} from './client';import type {Dataset} from '../types/domain';
export const list=()=>request<Dataset[]>('/datasets');
export const create=(data:unknown)=>post<Dataset>('/datasets',data);
