export const ROLES:Record<string,string>={admin:'管理员',analyst:'评测分析员',viewer:'只读复核员'};
export const RUN_STATUS:Record<string,string>={queued:'排队中',running:'计算中',completed:'已完成',failed:'失败'};
export const DECISIONS:Record<string,string>={accepted:'接受并记录边界',needs_attention:'需要继续核查'};
