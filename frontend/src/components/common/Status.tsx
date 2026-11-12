import {RUN_STATUS} from '../../constants/enums';export function Status({value}:{value:string}){return <span className={'status '+value}>{RUN_STATUS[value as keyof typeof RUN_STATUS]||value}</span>}
