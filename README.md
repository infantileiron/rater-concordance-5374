# 松庭评测 · 评委评分一致性

为松庭15人任务评测组制作的盲评校准工作台。锁定五级有序标尺，选择评委，以同一组完整任务计算并列校正Kendall W与成对二次加权Cohen kappa；保留混淆矩阵、分歧任务、隔离任务和人工归档。不用于人员录用或自动评价评委优劣。

## 场景与日常流程

团队原来用Excel比较评委均分，忽视同分并列、评分方向差异与偶然一致；缺评分时各评委对的分母也经常不一致。上游为匿名任务盲评记录和统一评分指南；本系统替代标尺锁定、完整性核查、两类一致性计算与人工复核；下游是评测组标尺讨论和站内CSV归档。

09:00分析员登录；09:03核对 songting_blind_ratings_202611.json 的120任务×4评委；09:08锁定L1—L5五级标尺；09:12选择四名匿名评委并保存研究；09:15提交Redis后台计算；09:18核查4项整任务隔离和116项共同分母；09:22比较W、六对kappa与评分混淆矩阵；09:27查看分歧任务和平均秩；09:32记录标尺、缺评分处理与解释边界；09:36管理员确认最新复核接受后归档；09:40只读账号下载六行评委对CSV。

|角色|主要页面|权限和典型动作|
|---|---|---|
|admin|全部|导入、配置、运行、复核及批准归档|
|analyst|盲评任务/有序标尺/评委组合/一致性证据/分歧复核|创建并运行研究，提交人工意见；批准归档后端403|
|viewer|全部只读和报告下载|核对混淆计数及分母；写入后端403|

## 启动与账号

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
```

前端 http://localhost:18222 ，后端文档 http://localhost:19222/docs ，数据库映射17722。演示账号：admin@songting.demo、analyst@songting.demo、viewer@songting.demo；密码均为 `Panel2026!`。JWT开发密钥应在部署前替换。

恰好五服务frontend/backend/worker/db/redis，全部healthcheck。backend等待PG/Redis健康，worker额外等待backend种子完成，frontend等待backend健康；所有HTTP健康检查使用127.0.0.1。PG、Redis AOF与worker心跳各用命名卷。结束演示执行 `docker compose down -v --remove-orphans`，会清除本项目演示数据。

SEED_DEMO=true自动建表并填充固定ID/自然键种子，不重复插入、不覆盖用户修改。固定seed2303生成120任务、4评委、5有序类别的模拟盲评，包含并列、刻意偏严的评委丁，以及ST-011/ST-037/ST-088/ST-109四项缺丁评分任务。选中全部4评委时4项整行隔离，全部指标共用116项任务；另选评委组合会重新计算完整任务集合。演示有完成研究、人工复核和报告。全部匿名模拟资料，不是真实人员资料。

## 六实体与页面

RatingDataset保存任务ID、任务组、评委代码和离散评分代码；RatingScale保存五级类别代码/名称/固定顺序；AgreementStudy锁定数据、标尺和评委列表；AgreementRun由Redis独立worker计算并持久化状态与结果；PanelReview记录分歧讨论和解释边界；Report仅在最新复核accepted后由管理员归档，一个run只归档一次。

六业务页：评测总览、盲评任务、有序标尺、评委组合、一致性证据、分歧复核（含操作留痕）。排序标尺、成对指标、混淆矩阵、任务平均秩与分歧表均使用后端真实计算结果，前端只绘图。盲评页预览40任务，计算使用全量完整集合；分歧表按平均二次距离降序预览20任务。标尺创建后不可原位修改，研究关联固定版本。

## 两种算法

### 带并列校正Kendall W

对每一评委的全部完整任务按五级标尺顺序排序；同类并列取所占秩的平均值。n为完整任务数，m为选定评委数，R_i为任务i在m位评委的秩和，中心为m(n+1)/2。每评委并列修正T_j=Σ(t³−t)，其中t为每一并列组大小。

`W = 12 × Σ(R_i − m(n+1)/2)² / [m²(n³−n) − mΣT_j]`。

少于2个完整任务，或全部评委对任务均给常量导致秩无变异、分母0时，W返回null并给出原因，不记为0或1。W只看任务排序协调，不要求给出的绝对等级相同。

### 二次加权Cohen kappa

五级标尺按保存列表映射到序号0—4；二次分歧权重 `d(i,j)=(i−j)²/16`。对每一评委对生成5×5真实混淆计数，观测分歧Do=Σd(i,j)O_ij/n，期望分歧De=Σd(i,j)(A_i/n)(B_j/n)，`kappa=1−Do/De`。少于2个完整任务或De=0返回null与原因；kappa可能为负，不裁为0。两个相同常量类别导致De=0；不同常量类别的De>0，数学值为0，应结合低变异情况解释。

类别代码/文字是标签。即使代码写为1、3、10、50、100，仍按列表的五个位置计算权重，不能按数字标签的差值或排序替代固定标尺。

### 分母、失败态与复现

选定评委任一缺评分（null或未提供）就整任务隔离，公开task_id和缺评分评委；W与所有成对kappa共用完整任务，不对每对使用不同分母。未知类别不是缺评分，保存研究时返回422，不静默转换或剔除。可估计kappa均值只是评委对的描述均值，明确可估计对数；不是推断检验或自动判定标准。

相同任务JSON、评委顺序、标尺顺序校验码给出确定性结果，无随机计算。支持2—8评委、2—2000任务、恰好5级标尺；任务ID和标尺代码唯一。非法评委、标尺、未知类别、重复任务和输入结构都由服务端验证。全部缺评分会输出0完整任务、null指标和完整隔离清单。队列或计算异常保留失败状态，可重新创建运行。

## 技术与开发

|部分|技术|
|---|---|
|前端|React18.3、TypeScript5.7、Vite6、Nginx1.28|
|后端|Python3.11、FastAPI、SQLAlchemy、PyJWT|
|持久化|PostgreSQL16|
|队列|Redis7.4 AOF、独立Python worker与心跳|

frontend/src含api/stores/types/components/common/hooks/pages/router/utils/constants；backend/src含routes/controllers/services/models/schemas/middlewares/utils/constants/config；backend/scripts为seed，backend/migrations说明初次模型建表。测试、截图、日志、TESTING与verification均在批次test-artifacts/gb-2303，源码不混入产物。

后端本地：安装requirements.txt，配置DATABASE_URL/REDIS_URL/JWT_SECRET，在backend执行`uvicorn src.main:app --reload`，另开`python -m src.worker`。前端`npm ci && npm run dev`；开发时给/api配置指向19222的同源代理，Docker Nginx已去除/api前缀转发。已验证React锁文件只改根包名，依赖节点未做领域字符串替换；Docker使用npm ci。

环境：COMPOSE_PROJECT_NAME=rater-concordance；FRONTEND_PORT=18222；BACKEND_PORT=19222；DB_PORT=17722；JWT_SECRET；SEED_DEMO。DATABASE_URL/REDIS_URL在Compose服务传入。`.env`忽略，`.env.example`供复制。

共享枚举Role、RunStatus、Decision定义在backend/src/constants/enums.py与frontend/src/constants/enums.ts；角色校验在controllers/auth.py、App.tsx；运行状态由services/runs.py和worker.py更新、Status组件消费；复核decision由schemas/review.py验证，Reviews页展示。标尺级别由schemas/scale.py约束，services/cohort.py映射位置，前端Scales与ConfusionMatrix消费。

## 已知边界

W与kappa回答不同问题，不能互相替代；高排序一致也可能有等级系统偏移。缺评分按选定评委整任务隔离可能改变任务构成，必须公开分母和隔离清单。未提供置信区间、显著性检验或评分偏差因果分析。没有真实人员录用服务。JSON表单导入，没有CSV文件解析器。单worker启动时恢复queued/running，未实现分布式租约；初次SQLAlchemy建表，没有生产迁移回滚。Google Fonts加载Noto Sans SC/Noto Serif SC，网络不可用则字体回退。开发密钥和演示账号只用于本地模拟。

MIT License。

并列修正和整行缺失处理的口径可对照 [CRAN irr官方Kendall W说明](https://search.r-project.org/CRAN/refmans/irr/html/kendall.html)；kappa定义及quadratic权重可对照 [scikit-learn官方API](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)。本项目固定传入全部五级的顺序，并明确选择少于两完整任务时不估计。
