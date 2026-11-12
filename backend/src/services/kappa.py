def weighted_kappa(a,b,k=5):
 if len(a)!=len(b):raise ValueError("配对评分长度不一致")
 if k!=5 or any(not isinstance(x,int) or x<0 or x>=k for x in a+b):raise ValueError("评分必须映射到固定五级标尺序号0至4")
 n=len(a);matrix=[[0]*k for _ in range(k)]
 for x,y in zip(a,b):matrix[x][y]+=1
 marg_a=[sum(row) for row in matrix];marg_b=[sum(matrix[i][j] for i in range(k)) for j in range(k)]
 if n<2:return {"kappa":None,"reason":"完整配对任务少于2，不可估计","n":n,"matrix":matrix,"marginal_a":marg_a,"marginal_b":marg_b,"observed_disagreement":None,"expected_disagreement":None,"exact_agreement":None}
 weights=[[(i-j)**2/(k-1)**2 for j in range(k)] for i in range(k)]
 observed=sum(weights[i][j]*matrix[i][j]/n for i in range(k) for j in range(k))
 expected=sum(weights[i][j]*marg_a[i]*marg_b[j]/(n*n) for i in range(k) for j in range(k))
 value=1-observed/expected if expected>0 else None
 return {"kappa":value,"reason":"期望分歧为0，kappa不可估计" if value is None else "五级标尺序号二次权重Cohen kappa","n":n,"matrix":matrix,"marginal_a":marg_a,"marginal_b":marg_b,"observed_disagreement":observed,"expected_disagreement":expected,"exact_agreement":sum(matrix[i][i] for i in range(k))/n}
