def prepare(tasks,raters,levels):
 codes=[l["code"] for l in levels]
 if len(codes)!=5 or len(set(codes))!=5:raise ValueError("需要恰好五级唯一有序标尺")
 if len(raters)<2 or len(set(raters))!=len(raters):raise ValueError("至少选择两名不同评委")
 positions={code:i for i,code in enumerate(codes)};complete=[];isolated=[]
 for task in tasks:
  values=task["ratings"]
  unknown=[r for r in raters if values.get(r) is not None and values[r] not in positions]
  if unknown:raise ValueError("任务"+task["task_id"]+"含不在所选标尺内的类别代码")
  missing=[r for r in raters if values.get(r) is None]
  if missing:isolated.append({"task_id":task["task_id"],"missing_raters":missing,"reason":"所选评委缺评分，整任务隔离"})
  else:complete.append({"task_id":task["task_id"],"group":task.get("group",""),"positions":[positions[values[r]] for r in raters],"codes":[values[r] for r in raters]})
 return complete,isolated
