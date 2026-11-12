from collections import Counter
import math
def average_ranks(values):
 ordered=sorted(enumerate(values),key=lambda x:x[1]);ranks=[0.0]*len(values);tie=0;i=0
 while i<len(ordered):
  j=i+1
  while j<len(ordered) and ordered[j][1]==ordered[i][1]:j+=1
  rank=(i+1+j)/2
  for index,_ in ordered[i:j]:ranks[index]=rank
  size=j-i;tie+=size**3-size;i=j
 return ranks,tie
def kendall_w(matrix,raters):
 n=len(matrix);m=len(raters)
 if n<2:return {"value":None,"reason":"完整任务少于2，协调系数不可估计","n":n,"m":m,"tie_correction":0,"denominator":0,"rank_sums":[],"ranks":[]}
 columns=[];ties=[]
 for j in range(m):
  ranks,t=average_ranks([row[j] for row in matrix]);columns.append(ranks);ties.append(t)
 sums=[math.fsum(column[i] for column in columns) for i in range(n)];center=m*(n+1)/2;s=math.fsum((r-center)**2 for r in sums)
 denominator=m*m*(n**3-n)-m*sum(ties)
 value=12*s/denominator if denominator>0 else None
 return {"value":value,"reason":"全部评委对任务给出常量评分，秩无变异，W不可估计" if value is None else "平均秩并列校正Kendall W","n":n,"m":m,"tie_correction":sum(ties),"ties_by_rater":dict(zip(raters,ties)),"denominator":denominator,"rank_sums":sums,"ranks":[[columns[j][i] for j in range(m)] for i in range(n)]}
