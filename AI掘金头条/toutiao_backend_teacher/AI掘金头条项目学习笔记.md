# 🚀 AI掘金头条后端项目 —— 源码深度解析与学习笔记

> 本项目是一个仿"今日头条"的新闻资讯类 App 后端，使用 **Python 3.12 + FastAPI** 构建，
> 本文从零开始、由浅入深地拆解项目中的每一个知识点、每一个函数，
> 并梳理项目"从 0 到 1"的完整构建思路，最后附可直接写进简历的项目经历。

---

## 目录

1. [项目概览](#一项目概览)
2. [一次请求的完整旅程](#二一次请求的完整旅程)
3. [知识点全解（由易到难，共 7 层）](#三知识点全解由易到难共-7-层)
4. [全函数清单（逐文件、逐函数）](#四全函数清单逐文件逐函数)
5. [项目从零到一的构建思路](#五项目从零到一的构建思路)
6. [技术栈总结](#六技术栈总结)
7. [简历项目经历](#七简历项目经历)
8. [项目亮点与可优化点](#八项目亮点与可优化点)

---

## 一、项目概览

### 1.1 这是什么项目？

一句话：**一个新闻资讯 App 的后端服务**，提供用户注册登录、新闻分类浏览、新闻详情（含浏览量统计、相关新闻推荐）、新闻收藏、浏览历史记录等完整能力。

它"麻雀虽小，五脏俱全"：一个真实生产级后端该有的东西——数据库建模、接口分层、身份认证、密码加密、统一响应、全局异常处理、Redis 缓存、分页——全都覆盖了。

### 1.2 功能清单

| 模块 | 功能 | 说明 |
|------|------|------|
| 用户模块 | 注册 / 登录 / 获取信息 / 更新信息 / 修改密码 | 密码 bcrypt 加密，UUID 令牌登录态 |
| 新闻模块 | 分类列表 / 新闻列表 / 新闻详情 | 分页 + hasMore 判断 + 浏览量 +1 + 相关新闻推荐 |
| 收藏模块 | 检查是否收藏 / 添加 / 删除 / 收藏列表 / 清空 | 同一用户对同一新闻只能收藏一次 |
| 历史模块 | 添加 / 列表 / 删除 / 清空 | 同一新闻只保留一条历史，重复浏览刷新时间 |

### 1.3 接口总览（共 17 个接口）

| 方法 | 路径 | 功能 | 是否需要登录 |
|------|------|------|:---:|
| POST | /api/user/register | 注册 | ❌ |
| POST | /api/user/login | 登录 | ❌ |
| GET | /api/user/info | 获取当前用户信息 | ✅ |
| PUT | /api/user/update | 更新用户信息 | ✅ |
| PUT | /api/user/password | 修改密码 | ✅ |
| GET | /api/news/categories | 获取新闻分类 | ❌ |
| GET | /api/news/list | 获取分类下新闻列表（分页） | ❌ |
| GET | /api/news/detail | 获取新闻详情 + 相关新闻 | ❌ |
| GET | /api/favorite/check | 检查某新闻是否已收藏 | ✅ |
| POST | /api/favorite/add | 添加收藏 | ✅ |
| DELETE | /api/favorite/remove | 取消收藏 | ✅ |
| GET | /api/favorite/list | 收藏列表（分页） | ✅ |
| DELETE | /api/favorite/clear | 清空收藏 | ✅ |
| POST | /api/history/add | 添加浏览历史 | ✅ |
| GET | /api/history/list | 历史列表（分页） | ✅ |
| DELETE | /api/history/delete/{history_id} | 删除一条历史 | ✅ |
| DELETE | /api/history/clear | 清空历史 | ✅ |

> 补充：GET / 返回 Hello World，是 FastAPI 脚手架自带的健康检查接口。

### 1.4 目录结构（分层架构）

```
toutiao_backend_teacher/
├── main.py                  # 应用入口：创建 app、注册中间件/异常、挂载路由
├── requirements.txt         # 第三方依赖清单
├── test_main.http           # IDE 接口测试文件（JetBrains HTTP Client）
├── config/                  # 配置层
│   ├── db_conf.py           # MySQL 异步引擎、会话工厂、get_db 依赖
│   └── cache_conf.py        # Redis 连接 + 缓存读写通用方法
├── models/                  # ORM 模型层（数据库表结构）
│   ├── users.py             # User 用户表、UserToken 令牌表
│   ├── news.py              # Category 分类表、News 新闻表
│   ├── favorite.py          # Favorite 收藏表
│   └── history.py           # History 历史表
├── schemas/                 # Pydantic 数据模型层（接口请求/响应校验）
│   ├── base.py              # NewsItemBase 新闻基础模型（被多处复用）
│   ├── users.py             # 用户相关请求/响应模型
│   ├── news.py              # 新闻详情、相关新闻响应模型
│   ├── favorite.py          # 收藏相关模型
│   └── history.py           # 历史相关模型
├── crud/                    # 数据库操作层（对 ORM 查询的封装）
│   ├── users.py             # 用户增删改查 + Token 逻辑
│   ├── news.py              # 新闻查询（无缓存版）
│   ├── news_cache.py        # 新闻查询（带 Redis 缓存版）
│   ├── favorite.py          # 收藏操作
│   └── history.py           # 历史操作
├── cache/                   # 缓存层（Redis key 设计与数据转换）
│   └── news_cache.py        # 新闻相关缓存的读写封装
├── utils/                   # 工具层
│   ├── security.py          # bcrypt 密码加密/校验
│   ├── auth.py              # Token 鉴权依赖 get_current_user
│   ├── response.py          # 统一响应格式 success_response
│   ├── exception.py         # 各类异常处理器
│   └── exception_handlers.py# 全局异常注册
└── .venv/                   # 虚拟环境（非源码）
```

**架构分层思想**：请求从外到内依次穿过 `routers（接口层）→ schemas（校验层）→ crud（数据操作层）→ models（表结构）→ MySQL`，旁路是 `config / utils / cache` 三个支撑层。每一层只干自己职责内的事，这就是"高内聚、低耦合"。

### 1.5 数据库设计（6 张表）

| 表名 | 作用 | 关键设计 |
|------|------|---------|
| user | 用户表 | username / phone 唯一索引；性别用 Enum；头像/简介有默认值 |
| user_token | 用户令牌表 | token 唯一索引；user_id 外键；expires_at 过期时间 |
| news_category | 新闻分类表 | name 唯一；sort_order 排序 |
| news | 新闻表 | category_id 外键 + 索引（高频查询）；publish_time 索引（排序）；views 浏览量 |
| favorite | 收藏表 | `(user_id, news_id)` 联合唯一约束（防重复收藏） |
| history | 历史表 | user_id / news_id / view_time 三个索引 |

---

## 二、一次请求的完整旅程

以"用户查看新闻列表"为例，看一个请求如何走完全链路：

```
前端 (Vue/小程序)
   │  GET /api/news/list?categoryId=1&page=1&pageSize=10
   ▼
FastAPI 应用 (main.py)
   │  CORS 中间件 → 全局异常处理器（先拦截异常）
   ▼
路由层 routers/news.py
   │  Query 参数校验 (categoryId 必填、pageSize≤100)
   │  Depends(get_db) 依赖注入 → 打开数据库会话
   ▼
缓存层 cache/news_cache.py
   │  查 Redis：命中 → 直接返回（快！）
   │  未命中 → 继续往下查
   ▼
数据操作层 crud/news_cache.py → crud/news.py
   │  SQLAlchemy 异步查询 MySQL → ORM 对象
   │  数据写入 Redis 缓存（下次直接命中）
   ▼
响应：统一格式 {code: 200, message: "...", data: {...}}
```

**关键结论**：读请求优先走 Redis（快），缓存没命中才查 MySQL（慢），查到后回填缓存——这就是经典的 **Cache-Aside（旁路缓存）** 模式。

---

## 三、知识点全解（由易到难，共 7 层）

> 学习建议：**先按顺序过一遍 L1~L3 建立信心，再重点啃 L4（SQLAlchemy）和 L5（Redis），
> L6、L7 是项目"质感"所在，面试常考。**

### 🟢 L1：Python 基础（热身层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 1 | 模块与包导入 | 把别的文件里的代码拿来用，`from x import y` | `main.py` 里 `from routers import news, users` |
| 2 | 函数定义与默认参数 | 函数 = 一段可复用的逻辑；默认参数让调用更灵活 | `def get_news_count(db, category_id)` |
| 3 | 类型注解 | 给参数/返回值标注类型，代码即文档，IDE 能自动提示 | `def get_user_by_username(db: AsyncSession, username: str)` |
| 4 | f-string 格式化 | 在字符串里直接嵌变量，`f"{变量}"` | `f"{NEWS_LIST_PREFIX}{category_part}:{page}:{size}"` |
| 5 | 字典解包 `**` | 把字典的键值对"摊开"作为关键字参数传入 | `User(**item)`、`update(...).values(**data)` |
| 6 | 列表推导式 | 一行代码生成新列表，比 for 循环更简洁 | `[News(**item) for item in cached_list]` |
| 7 | try/except 异常捕获 | 程序出错时不崩溃，而是捕获并做兜底处理 | `config/cache_conf.py` 中缓存读写全部 try/except |
| 8 | isinstance 类型判断 | 判断变量是不是某类型，据此走不同分支 | `if isinstance(value, (dict, list))` → 需 json 序列化 |
| 9 | 隐式命名空间包 | 没有 `__init__.py` 的目录也能当包导入（Python 3.3+） | 本项目所有目录均无 `__init__.py`，Python 3.12 下正常运行 |
| 10 | 异步编程 async/await | "协程"：遇到 IO（查库、连 Redis）不干等，先去干别的 | 所有 crud 函数都是 `async def` + `await db.execute(...)` |

### 🟢 L2：FastAPI 入门（框架层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 11 | FastAPI 应用实例 | `FastAPI()` 创建整个服务的"总开关" | `main.py` `app = FastAPI()` |
| 12 | 路由装饰器 | 把"URL + 方法"绑定到一个函数上 | `@router.get("/list")`、`@app.get("/")` |
| 13 | APIRouter 模块化 | 把同类接口打包成一个"路由模块"，再挂到 app 上 | `router = APIRouter(prefix="/api/user", tags=["users"])` |
| 14 | prefix 前缀 + tags 分组 | 统一接口前缀、在 Swagger 文档里自动分组 | 四个模块前缀 `/api/user`、`/api/news` 等 |
| 15 | include_router 挂载 | 把写好的路由模块注册进应用 | `main.py` 中 4 行 `app.include_router(...)` |
| 16 | 查询参数 Query | 从 URL `?key=value` 取参，可设默认值/必填/校验 | `category_id: int = Query(..., alias="categoryId")` |
| 17 | Query 参数校验 | ge(≥)、le(≤) 等约束，不合法自动返回 422 | `page_size: int = Query(10, le=100)` |
| 18 | 请求体参数 | 把前端传的 JSON 自动解析成 Pydantic 模型 | `async def register(user_data: UserRequest, ...)` |
| 19 | 依赖注入 Depends | 自动创建/注入函数需要的"依赖"（如数据库会话） | `db: AsyncSession = Depends(get_db)` |
| 20 | 依赖注入做鉴权 | 把"校验登录"做成依赖，接口声明一下就自动校验 | `user: User = Depends(get_current_user)` |
| 21 | 状态码常量 | 用语义化常量代替裸数字 | `status.HTTP_401_UNAUTHORIZED` |
| 22 | HTTPException 主动抛错 | 业务不满足时主动抛出带状态码的异常 | `raise HTTPException(status_code=404, detail="新闻不存在")` |
| 23 | CORS 跨域中间件 | 允许浏览器跨域访问后端（前后端分离必备） | `main.py` `app.add_middleware(CORSMiddleware, ...)` |
| 24 | 自动生成 API 文档 | FastAPI 免费附赠 Swagger 文档（/docs），可在线调试 | 无需写代码，框架自带 |

### 🟢 L3：Pydantic 数据模型（校验层）

> Pydantic 是 FastAPI 的"校验心脏"：前端传什么、后端返回什么，都由它把关。

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 25 | BaseModel | 定义一个"数据形状"，自动校验类型 | `class UserRequest(BaseModel): username: str` |
| 26 | Field 字段约束 | 给字段加规则：必填、长度、默认值、描述 | `password: str = Field(..., min_length=6)` |
| 27 | alias 别名 | 字段在 Python 里叫 `publish_time`，对外输出叫 `publishedTime`（前后端命名习惯不同） | `Field(None, alias="publishedTime")` |
| 28 | Optional 可空字段 | 该字段允许为 None | `nickname: Optional[str] = None` |
| 29 | 模型继承 | 子模型继承父模型字段，避免重复定义 | `NewsDetailResponse(NewsItemBase)` |
| 30 | 嵌套模型 | 一个模型的字段是另一个模型/模型列表 | `UserAuthResponse` 里嵌 `user_info: UserInfoResponse` |
| 31 | ConfigDict(from_attributes) | 允许直接从 ORM 对象取值构建模型（数据库对象 → 接口数据） | `UserInfoResponse.model_validate(user)` |
| 32 | ConfigDict(populate_by_name) | 传入数据时既认别名 `userInfo` 也认字段名 `user_info` | `schemas/users.py` |
| 33 | model_validate | 把字典/ORM 对象"验一遍"变成模型 | `NewsItemBase.model_validate(item)` |
| 34 | model_dump | 把模型转回字典，可控制输出格式 | `model_dump(mode="json", by_alias=False, exclude={'related_news'})` |
| 35 | model_dump 高级参数 | `exclude_unset`(只输出被设置的)、`exclude_none`(跳过空值) | `crud/users.py` 更新用户时动态拼字段 |
| 36 | default_factory | 可变默认值（如列表）必须用它，避免多个实例共享同一列表 | `related_news: list = Field(default_factory=list)` |

### 🟡 L4：SQLAlchemy 2.0 + MySQL（核心层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 37 | ORM 思想 | 用 Python 类代替 SQL 语句操作数据库表 | `class User(Base)` 对应 `user` 表 |
| 38 | DeclarativeBase | 2.0 新版声明式基类，所有模型继承它 | `class Base(DeclarativeBase): pass` |
| 39 | Mapped / mapped_column | 2.0 新写法：`Mapped[类型]` 声明字段类型，`mapped_column` 配置列属性 | `id: Mapped[int] = mapped_column(Integer, primary_key=True)` |
| 40 | 列属性 | primary_key 主键、autoincrement 自增、nullable 可空、unique 唯一、default 默认值、comment 注释 | 各 models 文件随处可见 |
| 41 | 字段类型 | String(长度)、Integer、Text(长文本)、DateTime(时间)、Enum(枚举) | `gender: Enum('male','female','unknown')` |
| 42 | ForeignKey 外键 | 表与表之间建立"引用关系"，保证数据一致性 | `user_id: ForeignKey(User.id)` |
| 43 | 模型继承复用公共字段 | 把每个表都有的 created_at/updated_at 放进父类 Base，子类自动拥有 | `models/news.py` 的 `Base` |
| 44 | __table_args__ 表级配置 | 在类里声明索引、唯一约束等"表级别"的东西 | `Index(...)`、`UniqueConstraint(...)` |
| 45 | 索引设计 | 索引 = 书的目录。查询/排序常用的字段加索引，速度飞快 | news 表给 category_id、publish_time 加索引 |
| 46 | 唯一约束 | 保证两列的组合不重复 | favorite 表 `(user_id, news_id)` 联合唯一 → 防重复收藏 |
| 47 | 默认值陷阱 | `default=datetime.now` 是"每次插入取当前时间"；`default=datetime.now()` 是"导入模块时定死时间"（BUG） | `models/users.py` 用了带括号版（小瑕疵），news/history 用无括号版（正确） |
| 48 | 异步引擎 | `create_async_engine` 创建异步连接引擎，不阻塞事件循环 | `config/db_conf.py`，驱动 `mysql+aiomysql://` |
| 49 | 连接池 | `pool_size=10` 保持 10 个常驻连接，`max_overflow=20` 允许最多再借 20 个 | `config/db_conf.py` |
| 50 | 会话工厂 | `async_sessionmaker` 生产数据库会话（相当于"一次事务的载体"） | `AsyncSessionLocal = async_sessionmaker(...)` |
| 51 | 查询 select | 构建查询语句：`select(表).where(条件).offset().limit()` | crud 中所有查询 |
| 52 | 查询结果取值 | `scalar_one_or_none()` 取单条(可空)、`scalars().all()` 取列表、`scalar_one()` 取单条(必须存在) | crud 中反复使用 |
| 53 | 聚合函数 func.count | 统计数量，配合 `scalar_one()` 取总数 | `select(func.count(News.id))` |
| 54 | 排序 order_by | `.desc()` 降序、`.asc()` 升序；可多字段排序 | 相关新闻按"浏览量 + 发布时间"双排序 |
| 55 | 分页 offset/limit | 跳过 N 条取 M 条，经典分页 | `offset=(page-1)*page_size` |
| 56 | 更新 update | `update(表).where(条件).values(字段=值)`，`rowcount` 看影响了几行 | `increase_news_views`、`update_user` |
| 57 | 删除 delete | `delete(表).where(条件)`，`rowcount > 0` 判断是否删到 | `remove_news_favorite` 等 |
| 58 | 联表查询 join | 一张表的数据不够用，把两张表按关联条件"拼"起来查 | 收藏/历史列表：`select(News, ...).join(Favorite, Favorite.news_id == News.id)` |
| 59 | 列别名 label | 联表查询时给重复列改名，避免歧义 | `Favorite.created_at.label("favorite_time")` |
| 60 | 事务提交/回滚 | commit 提交、rollback 回滚、refresh 重新读库刷新对象 | `get_db` 里 try/except/finally 三段式管理 |
| 61 | 依赖中的会话生命周期 | FastAPI 依赖用 `yield` 交出会话，请求结束自动收尾——"谁打开谁关闭" | `config/db_conf.py` 的 `get_db` |

### 🟡 L5：Redis 缓存（性能层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 62 | Redis 异步客户端 | `redis.asyncio` 提供 async 版连接，配合 FastAPI 异步模型 | `config/cache_conf.py` |
| 63 | 连接参数 | host/port/db(0~15 个逻辑库)/decode_responses(自动把字节解码成字符串) | `redis.Redis(host=..., decode_responses=True)` |
| 64 | setex 带过期时间写入 | `SETEX key 秒数 value`，到期自动消失——缓存必备 | `set_cache` 中 `redis_client.setex(key, expire, value)` |
| 65 | 序列化 | Redis 只能存字符串；字典/列表用 `json.dumps` 转字符串存，读时 `json.loads` 还原 | `set_cache` / `get_json_cache` |
| 66 | ensure_ascii=False | json 序列化时保留中文原样，而不是转成 \uXXXX | `json.dumps(value, ensure_ascii=False)` |
| 67 | 缓存 Key 设计 | 用"命名空间:业务:标识"格式，如 `news:detail:5`，可读且不冲突 | `cache/news_cache.py` 常量 |
| 68 | 缓存粒度 | 分类/配置这类"稳定数据"缓存久(7200s)，新闻列表 1800s，详情 300s——**数据越稳定，缓存越久** | `cache/news_cache.py` 各函数默认参数 |
| 69 | 防缓存雪崩 | 所有 key 用不同过期时间，避免同一时刻集体失效打爆数据库 | 同上，TTL 全部错开 |
| 70 | Cache-Aside 旁路缓存模式 | 读：先查缓存→没有查库→回填缓存；写：直接写库（本项目简单场景） | `crud/news_cache.py` 所有函数 |
| 71 | 缓存降级容错 | 缓存读写全部 try/except，Redis 挂了就打印日志返回 None，**业务照常走数据库** | `config/cache_conf.py` |
| 72 | ORM ↔ 字典互转 | 存缓存前：ORM → Pydantic → 字典(json)；取缓存后：字典 → `News(**item)` 还原 ORM | `crud/news_cache.py` |

### 🟠 L6：安全与认证（防护层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 73 | 密码不能明文存 | 数据库泄露时明文密码直接暴露，必须哈希加密 | 全项目密码字段 `password` 全部加密存储 |
| 74 | bcrypt 哈希算法 | 专门为密码设计的慢哈希，自带盐值，抗彩虹表攻击 | `utils/security.py` |
| 75 | passlib CryptContext | 统一管理哈希方案，`deprecated="auto"` 自动升级旧算法 | `pwd_context = CryptContext(schemes=["bcrypt"])` |
| 76 | hash / verify 方法 | `hash` 加密、`verify` 校验（返回布尔），两者配对使用 | `get_hash_password` / `verify_password` |
| 77 | Token 登录态 | 登录成功发一个随机令牌，客户端每次请求带上它证明"我是谁" | `create_token` 用 `uuid.uuid4()` 生成 |
| 78 | 令牌过期 | 令牌带过期时间 `expires_at`，过期即失效，需要重新登录 | `timedelta(days=7)`，`get_user_by_token` 校验 |
| 79 | Bearer Token 规范 | 请求头标准写法：`Authorization: Bearer <token>` | `utils/auth.py` 用 `.replace("Bearer ", "")` 取出 token |
| 80 | Header 依赖取请求头 | FastAPI 依赖里声明 `authorization: str = Header(...)` 就能拿到请求头 | `utils/auth.py` |
| 81 | 鉴权依赖复用 | 把"验 token→查用户"封装成 `get_current_user`，哪个接口要登录就 `Depends` 一下 | 收藏/历史/用户信息接口全部复用 |

### 🟠 L7：架构与工程化（进阶层）

| # | 知识点 | 通俗解释 | 代码位置/示例 |
|---|--------|---------|--------------|
| 82 | 分层架构 | 接口/校验/数据操作/表结构 分层隔离，各司其职，好维护好扩展 | 目录结构见 1.4 |
| 83 | 统一响应格式 | 所有接口返回 `{code, message, data}` 三件套，前端解析逻辑统一 | `utils/response.py` |
| 84 | jsonable_encoder | 把 Pydantic/ORM/datetime 等"非 JSON 原生"对象安全转成可序列化结构 | `success_response` 里兜底转换 |
| 85 | 全局异常处理器 | 用 `app.add_exception_handler` 注册各类异常的"收尾人"，避免错误裸奔 | `utils/exception_handlers.py` |
| 86 | 异常处理注册顺序 | **子类在前、父类在后**：具体异常先匹配（如 IntegrityError），兜底的 Exception 最后 | `register_exception_handlers` |
| 87 | 业务异常 HTTPException | 主动抛出、状态码精确（400 参数错、401 未登录、404 不存在） | 各 router |
| 88 | 数据库完整性错误翻译 | 把"Duplicate entry"这种底层报错翻译成"用户名已存在"给用户 | `integrity_error_handler` |
| 89 | 兜底异常 Exception | 任何没被捕获的异常统一返回 500，绝不把堆栈泄露给用户 | `general_exception_handler` |
| 90 | DEBUG_MODE 开关 | 开发环境返回详细错误(类型/详情/堆栈)，生产只返回友好提示 | `utils/exception.py` 顶部常量 |
| 91 | 接口参数风格统一 | 对外 camelCase（`categoryId`），对内 snake_case（`category_id`），靠 alias 转换 | 全部 schemas |
| 92 | 依赖注入的"钩子"用法 | `get_db` 用 `yield` 交出资源，try 成功 commit、异常 rollback、finally close——一套标准事务模板 | `config/db_conf.py` |
| 93 | 接口测试文件 | 用 JetBrains HTTP Client 的 `.http` 文件直接测接口，无需 Postman | `test_main.http` |
| 94 | 虚拟环境 | `.venv` 隔离项目依赖，`requirements.txt` 记录版本，保证环境可复现 | 项目根目录 |

---

## 四、全函数清单（逐文件、逐函数）

> 按"依赖方向"排列：配置 → 模型 → 缓存 → 数据操作 → 接口 → 工具。
> 每个函数都给出：函数签名、作用（通俗解释）、调用它的地方。

### 4.1 config/db_conf.py —— 数据库配置

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_db()` | **数据库会话依赖**：打开会话交给接口使用，接口跑完自动 commit（成功）/ rollback（异常）/ close（收尾）。是"一次请求一个事务"的标准模板 | 所有 router 接口 `Depends(get_db)` |

### 4.2 config/cache_conf.py —— Redis 配置与通用缓存

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_cache(key)` | 读 Redis 字符串；失败打印日志返回 None（缓存挂了不影响业务） | get_json_cache |
| `get_json_cache(key)` | 读缓存并 `json.loads` 还原成列表/字典；无数据或失败返回 None | cache/news_cache.py 全部读取函数 |
| `set_cache(key, value, expire=3600)` | 写缓存：字典/列表先转 JSON 字符串，再 `setex` 带过期时间；默认 1 小时 | cache/news_cache.py 全部写入函数 |

### 4.3 cache/news_cache.py —— 新闻缓存封装（Key 设计师）

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_cached_categories()` | 读分类缓存，Key = `news:categories` | crud/news_cache.get_categories |
| `set_cache_categories(data, expire=7200)` | 写分类缓存，缓存 2 小时（分类最稳定） | 同上 |
| `get_cache_news_list(category_id, page, size)` | 读某分类某页的新闻列表缓存，Key = `news_list:分类:页码:每页条数` | crud/news_cache.get_news_list |
| `set_cache_news_list(category_id, page, size, news_list, expire=1800)` | 写新闻列表缓存，30 分钟 | 同上 |
| `get_cached_news_detail(news_id)` | 读新闻详情缓存，Key = `news:detail:新闻id` | crud/news_cache.get_news_detail |
| `cache_news_detail(news_id, news_data, expire=300)` | 写新闻详情缓存，5 分钟（浏览量常变，缓存短） | 同上 |
| `get_cached_related_news(news_id, category_id)` | 读相关新闻缓存，Key = `news:related:新闻id:分类id` | crud/news_cache.get_related_news |
| `cache_related_news(news_id, category_id, related_list, expire=1800)` | 写相关新闻缓存，30 分钟 | 同上 |

### 4.4 models/ —— ORM 模型（表结构定义）

| 函数/类 | 作用 |
|---------|------|
| `User.__repr__` | 打印调试信息（如 `<User(id=1, username='tom')>`），方便日志排查 |
| `UserToken.__repr__` | 同上，打印令牌对象 |
| `Category.__repr__` | 同上，打印分类对象 |
| `News.__repr__` | 同上，打印新闻对象 |
| `Favorite.__repr__` | 同上，打印收藏对象 |
| `History.__repr__` | 同上，打印历史对象 |

> `__repr__` 是 Python 内置"对象的字符串表示"方法，重写它以后 `print(对象)` 不再显示 `<models.news.News object at 0x...>` 这种天书。

### 4.5 crud/users.py —— 用户数据操作（含 Token 逻辑）

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_user_by_username(db, username)` | 按用户名查用户，查到返回 User 对象，查不到返回 None | 注册查重、登录、更新 |
| `create_user(db, user_data)` | 创建用户：先 bcrypt 加密密码 → 入库 → commit → refresh 取回带 id 的完整对象 | 注册接口 |
| `create_token(db, user_id)` | 生成登录令牌：`uuid4()` 随机串 + 7 天过期；该用户已有令牌则**更新**，没有则**新增**（一套"有则改、无则加"的 upsert 逻辑） | 注册、登录接口 |
| `authenticate_user(db, username, password)` | 登录校验：用户存在 + 密码 verify 通过 → 返回用户；任一失败返回 None | 登录接口 |
| `get_user_by_token(db, token)` | 令牌换用户：查令牌 → 校验未过期 → 查用户返回；令牌无效/过期返回 None | utils/auth.py |
| `update_user(db, username, user_data)` | 更新用户信息：只更新"前端传了的值"（exclude_unset+exclude_none），用 rowcount 判断用户是否存在 | 更新信息接口 |
| `change_password(db, user, old_password, new_password)` | 修改密码：先验旧密码 → 新密码加密 → 重新入库 | 改密接口 |

### 4.6 crud/news.py —— 新闻数据操作（无缓存版）

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_categories(db, skip, limit)` | 查分类列表（分页） | 分类接口（未用到，缓存版优先） |
| `get_news_list(db, category_id, skip, limit)` | 查指定分类下的新闻列表（分页） | 列表接口（未用到，缓存版优先） |
| `get_news_count(db, category_id)` | 统计该分类下新闻总数（`func.count` + `scalar_one`） | 列表接口（计算 hasMore 用） |
| `get_news_detail(db, news_id)` | 按 id 查新闻详情，查不到返回 None | 详情接口（缓存版优先） |
| `increase_news_views(db, news_id)` | 浏览量 +1：`update` 原子自增，`rowcount > 0` 判断新闻是否存在 | 详情接口 |
| `get_related_news(db, news_id, category_id, limit=5)` | 相关新闻推荐：同分类、排除自己、按"浏览量高 + 发布时间新"排序取 5 条 | 详情接口（缓存版优先） |

### 4.7 crud/news_cache.py —— 新闻数据操作（缓存增强版）

> 与 4.6 函数同名同职责，区别是**先查缓存，未命中才查库，并回填缓存**。这是本项目"无缓存版 → 加缓存版"的演进痕迹，非常值得学习。

| 函数 | 作用 | 与无缓存版的差异 |
|------|------|-----------------|
| `get_categories(db, skip, limit)` | 分类列表（缓存优先） | 命中直接返回；未命中查库后用 `jsonable_encoder` 转 JSON 写缓存 |
| `get_news_list(db, category_id, skip, limit)` | 新闻列表（缓存优先） | 缓存 Key 按"页码"算（`skip//limit+1`）；命中时用 `News(**item)` 还原 ORM；写缓存前 ORM→Pydantic→字典 |
| `get_news_count(db, category_id)` | 总数统计（不缓存，因实时性要求高） | 无差异 |
| `get_news_detail(db, news_id)` | 新闻详情（缓存优先） | 写缓存时排除 `related_news` 字段（News 模型没有该字段，防止还原报错） |
| `increase_news_views(db, news_id)` | 浏览量 +1（不缓存，直写库保证准确） | 无差异 |
| `get_related_news(db, news_id, category_id, limit=5)` | 相关新闻（缓存优先） | 命中直接返回字典列表；未命中查库转字典写缓存 |

### 4.8 crud/favorite.py —— 收藏数据操作

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `is_news_favorite(db, user_id, news_id)` | 检查当前用户是否收藏了某新闻，返回布尔 | 检查收藏接口 |
| `add_news_favorite(db, user_id, news_id)` | 添加收藏：insert → commit → refresh | 添加收藏接口 |
| `remove_news_favorite(db, user_id, news_id)` | 取消收藏：delete，`rowcount > 0` 判断是否真删掉了 | 删除收藏接口 |
| `get_favorite_list(db, user_id, page, page_size)` | 收藏列表（分页）：`func.count` 算总数 + **join 联表**查"新闻 + 收藏时间 + 收藏id"，按收藏时间倒序；返回 `(rows, total)` 二元组 | 收藏列表接口 |
| `remove_all_favorites(db, user_id)` | 清空某用户全部收藏，返回删除条数（`rowcount or 0` 防止 None） | 清空收藏接口 |

### 4.9 crud/history.py —— 历史数据操作

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `add_history(db, user_id, news_id)` | 添加历史：**去重逻辑**——已看过该新闻则只刷新 `view_time`，没看过才新增 | 添加历史接口 |
| `get_history_list(db, user_id, page, page_size)` | 历史列表（分页）：总数 + join 联表 + 按浏览时间倒序，返回 `(rows, total)` | 历史列表接口 |
| `delete_history(db, user_id, news_id)` | 删除一条历史（按用户+新闻定位），`rowcount > 0` 判断结果 | 删除历史接口 |
| `clear_history(db, user_id)` | 清空某用户全部历史，返回删除条数 | 清空历史接口 |

### 4.10 routers/users.py —— 用户接口层

| 接口函数 | 路由 | 逻辑流程 | 作用 |
|---------|------|---------|------|
| `register(user_data, db)` | POST /api/user/register | 查重 → 不存在则创建用户 → 生成 Token → 统一响应 | 注册：用户名重复返回 400"用户已存在" |
| `login(user_data, db)` | POST /api/user/login | 校验账号密码 → 生成 Token → 统一响应 | 登录：失败返回 401 |
| `get_user_info(user)` | GET /api/user/info | 依赖注入直接拿当前用户 → 转 UserInfoResponse | 获取登录用户信息 |
| `update_user_info(user_data, user, db)` | PUT /api/user/update | 调用 crud.update_user → 返回更新后用户 | 修改昵称/头像/简介等 |
| `update_password(password_data, user, db)` | PUT /api/user/password | 验旧密码 → 加密新密码 → 入库 | 修改密码，失败返回 500 |

### 4.11 routers/news.py —— 新闻接口层

| 接口函数 | 路由 | 逻辑流程 | 作用 |
|---------|------|---------|------|
| `get_categories(skip, limit, db)` | GET /api/news/categories | 缓存优先查分类 → 统一响应 | 分类列表 |
| `get_news_list(category_id, page, page_size, db)` | GET /api/news/list | 算 offset → 查列表(缓存优先) → 查总数 → 算 `has_more = (offset + 本次条数) < total` | 分页新闻列表，`hasMore` 告诉前端是否还有下一页 |
| `get_news_detail(news_id, db)` | GET /api/news/detail | 查详情(缓存优先) → 不存在 404 → **浏览量 +1** → 查相关新闻 → 组装响应 | 详情页三合一：内容 + 热度 + 推荐 |

### 4.12 routers/favorite.py —— 收藏接口层

| 接口函数 | 路由 | 逻辑流程 | 作用 |
|---------|------|---------|------|
| `check_favorite(news_id, user, db)` | GET /api/favorite/check | 调 crud 查收藏状态 → 返回 `{isFavorite: bool}` | 前端进入详情页时点亮/熄灭收藏按钮 |
| `add_favorite(data, user, db)` | POST /api/favorite/add | 直接插入收藏记录 | 收藏新闻（重复收藏由数据库唯一约束兜底） |
| `remove_favorite(news_id, user, db)` | DELETE /api/favorite/remove | 删除记录，没删到返回 404 | 取消收藏 |
| `get_favorite_list(page, page_size, user, db)` | GET /api/favorite/list | 调 crud 拿 `(rows, total)` → `**news.__dict__` 展开 ORM 字段并合并收藏时间/id → 封装 FavoriteListResponse | 分页收藏列表 |
| `clear_favorite(user, db)` | DELETE /api/favorite/clear | 清空并提示删了几条 | 一键清空收藏 |

### 4.13 routers/history.py —— 历史接口层

| 接口函数 | 路由 | 逻辑流程 | 作用 |
|---------|------|---------|------|
| `add_history(data, user, db)` | POST /api/history/add | 调 crud（自动去重刷新时间） | 记录浏览行为 |
| `get_history_list(page, page_size, user, db)` | GET /api/history/list | 同收藏列表模式：rows + total + hasMore | 分页历史列表 |
| `delete_history(history_id, user, db)` | DELETE /api/history/delete/{history_id} | 调 crud 按"用户+新闻"删除，删不到 404 | 删除单条历史 |
| `clear_history(user, db)` | DELETE /api/history/clear | 清空并返回成功 | 一键清空历史 |

### 4.14 utils/ —— 工具层

| 函数 | 作用 | 被谁调用 |
|------|------|---------|
| `get_hash_password(password)` | 密码加密（bcrypt） | 注册、改密 |
| `verify_password(plain, hashed)` | 密码校验，返回布尔 | 登录、改密 |
| `get_current_user(authorization, db)` | **鉴权依赖**：从请求头取 `Bearer token` → 查用户 → 无效/过期抛 401 → 返回 User 对象 | 所有需登录接口 |
| `success_response(message, data)` | 统一成功响应：包成 `{code:200, message, data}`，内部用 `jsonable_encoder` 兜底转换任意对象 | 几乎所有接口 |
| `http_exception_handler(request, exc)` | 处理业务异常 HTTPException：按原状态码返回 `{code, message, data:None}` | 全局注册 |
| `integrity_error_handler(request, exc)` | 处理数据库完整性错误：把"Duplicate entry"翻译成"用户名已存在"，外键错误翻译成"关联数据不存在" | 全局注册 |
| `sqlalchemy_error_handler(request, exc)` | 处理 SQLAlchemy 数据库错误：返回 500 友好提示，开发模式附详细堆栈 | 全局注册 |
| `general_exception_handler(request, exc)` | 兜底：捕获所有漏网异常，返回 500 | 全局注册 |
| `register_exception_handlers(app)` | 把上面 4 个处理器注册到 app，顺序"具体在前、兜底在后" | main.py 启动时调用 |
| `root()` | GET / 健康检查，返回 Hello World | 直接访问根路径 |

---

## 五、项目从零到一的构建思路

> 这节回答："如果让我重新做一遍，我会按什么顺序、什么思路搭出这个项目？"
> 以下是结合代码注释（如 routers/news.py 顶部的步骤注释）还原出的真实开发路径。

### 第 1 步：需求分析 —— 先想清楚"做给谁用、有哪些功能"

仿"今日头条"的新闻 App，后端要回答 4 个问题：

1. **用户**：怎么注册、登录、证明身份？（用户 + 认证）
2. **新闻**：看什么内容？怎么分类、怎么翻页？（新闻 + 分类 + 分页）
3. **互动**：喜欢的内容怎么存起来？（收藏）
4. **个性化**：看过什么、下次推荐什么？（浏览历史）

> 一句话方法论：**先把功能列成"名词表"，每个名词对应一张表；把操作列成"动词表"，每个动词对应一个接口。**

### 第 2 步：技术选型 —— 为什么是 FastAPI + MySQL + Redis？

| 选型 | 理由 |
|------|------|
| FastAPI | 原生 async 高性能；类型注解自动校验；免费 Swagger 文档；适合前后端分离 |
| SQLAlchemy 2.0 (async) | 用 Python 类管理表结构，异步不阻塞；aiomysql 驱动连 MySQL |
| MySQL | 关系型数据（用户/新闻/收藏）天然适合表结构 + 事务 |
| Redis | 新闻列表/详情是"读多写少"热点数据，缓存到内存，QPS 翻倍 |
| bcrypt/passlib | 密码安全存储的业界标准做法 |

### 第 3 步：数据库设计 —— 建表是地基，索引是道路

先画 ER 关系，再落成 6 张表：

```
user 1 ──── n user_token      （一个用户可有多个令牌，但代码里只保留一条）
news_category 1 ──── n news   （一个分类下多条新闻）
user 1 ──── n favorite n ──── 1 news   （多对多，用收藏表记录）
user 1 ──── n history  n ──── 1 news   （多对多，用历史表记录）
```

建表时的三个"专业动作"（面试亮点）：

- **索引**：`category_id`（高频 where）、`publish_time`（高频排序）、`view_time`（历史按时间倒序）——索引建在查询和排序用到的字段上；
- **唯一约束**：favorite 的 `(user_id, news_id)` 联合唯一，数据库层面保证"同一用户不能重复收藏同一新闻"，比代码里 if 判断更可靠；
- **外键**：`ForeignKey` 保证引用完整性，删不掉"还有收藏记录的新闻"。

### 第 4 步：搭骨架 —— 先让服务"跑起来"

1. 创建虚拟环境 + `requirements.txt` 锁版本；
2. `main.py` 创建 FastAPI 实例；
3. 挂 CORS 中间件（前后端分离必须）；
4. 注册全局异常处理器；
5. 写一个 `/` 健康检查接口，`uvicorn main:app --reload` 启动验证。

> 经验：**先把壳子跑起来，再往里填肉**，避免"写了一堆代码最后跑不起来"。

### 第 5 步：自底向上开发一个模块 —— 以"用户模块"为例

每个模块固定 4 步，顺序是"底层 → 上层"：

```
① models/users.py      定义表结构（User、UserToken 两个类）
② schemas/users.py     定义接口数据形状（请求 UserRequest、响应 UserAuthResponse）
③ crud/users.py        封装数据库操作（查重、建用户、发令牌、验密码…）
④ routers/users.py     暴露 HTTP 接口（register/login/info/update/password）
⑤ main.py              挂载路由 app.include_router(users.router)
```

**为什么自底向上？** 上层依赖下层：写接口前必须先有 crud 方法；写 crud 前必须先有模型。每一层写完都能单独验证，最后一层只是"把积木拼起来"。

### 第 6 步：解决"登录态"问题 —— Token 认证

1. 注册/登录成功 → `uuid4()` 生成随机 Token，存 `user_token` 表（带 7 天过期时间）；
2. 客户端把 Token 放在请求头 `Authorization: Bearer <token>`；
3. 后端写一个 `get_current_user` 依赖：取请求头 → 查 Token → 验过期 → 查用户；
4. 哪个接口要登录，加一个 `Depends(get_current_user)` 参数即可——**一个依赖，处处复用**。

### 第 7 步：做"新闻模块"，顺手学会分页与联表

- **分页**：`offset = (page-1) * page_size`，SQL 用 `offset/limit`，响应里带 `total` 和 `has_more = (offset + 本次数量) < total`，前端据此显示"加载更多"；
- **相关新闻**：同分类 + 排除自己 + `order_by(浏览量 desc, 发布时间 desc)` 双排序，这是最朴素的"推荐算法"；
- **浏览量 +1**：`update ... values(views = views + 1)`，在数据库原子自增，避免"读-改-写"并发丢更新。

### 第 8 步：收藏 & 历史模块 —— 复制成熟套路

收藏和历史结构几乎一样（都是"用户 × 新闻"的关系表），套路完全复用：

- 列表 = **join 联表**：`select(News, 时间别名).join(关系表).where(用户).order_by(时间desc).offset().limit()`
- 添加 = 查重 → insert（历史是"有则刷新时间"）
- 删除/清空 = delete + `rowcount`

> 这就是分层架构的价值：**第二次做同样的事，只需要复制粘贴 + 改表名**。favorite.py 和 history.py 的相似度肉眼可见。

### 第 9 步：统一响应 + 全局异常 —— 让接口"有教养"

- **统一响应**：所有接口返回 `{code, message, data}`，前端写一个拦截器就能统一处理成功/失败；
- **全局异常**：4 层处理器——业务异常(HTTPException) 保持原状态码；数据库唯一约束错误翻译成"用户名已存在"；SQLAlchemy 错误返回 500；Exception 兜底。注册顺序"子类在前，父类在后"；
- **DEBUG_MODE 开关**：开发时把错误堆栈、请求路径返回给前端方便调试；生产环境只给友好提示，不泄露内部信息。

### 第 10 步：性能优化 —— 加 Redis 缓存

对"读多写少"的新闻数据做 **Cache-Aside** 优化：

1. 新增 `cache/news_cache.py`：设计缓存 Key（`news:detail:5` 这种命名空间风格）+ 不同 TTL（分类 2h / 列表 30min / 详情 5min，**错开过期时间防雪崩**）；
2. 新建 `crud/news_cache.py`：与 `crud/news.py` 同名的"缓存优先"版本——先查缓存，命中直接返回；未命中查库并回填缓存（同时保留无缓存版作对照，这是很聪明的教学写法）；
3. 缓存读写全部 try/except：**Redis 挂了业务照常走数据库**（降级容错）；
4. 序列化细节：ORM 对象不能直接存 Redis，要走 `ORM → Pydantic → 字典 → JSON` 的转换链，读出来再 `News(**dict)` 还原。

### 第 11 步：联调与文档

- FastAPI 自带 `/docs` Swagger 页面，在线调试每个接口；
- `test_main.http` 文件用 IDE 直接发请求测试；
- 用 Postman/前端联调，核对每个接口的字段名（camelCase 别名）、分页参数、鉴权头。

---

## 六、技术栈总结

| 类别 | 技术 | 在本项目中的作用 |
|------|------|-----------------|
| 语言 | Python 3.12 | 全项目开发语言，全程 async 异步编程 |
| Web 框架 | FastAPI 0.125 | 路由、依赖注入、参数校验、自动文档 |
| 服务网关 | Uvicorn | ASGI 服务器，运行 FastAPI 应用 |
| 数据库 | MySQL 8 | 6 张表持久化存储业务数据 |
| ORM | SQLAlchemy 2.0 + aiomysql | 异步 ORM：建表、查询、事务、联表 |
| 缓存 | Redis (redis-py async) | 新闻分类/列表/详情缓存，Cache-Aside 模式 |
| 数据校验 | Pydantic v2 | 请求/响应模型、Field 校验、别名映射 |
| 安全 | passlib + bcrypt | 密码哈希加密与校验 |
| 认证 | Token + uuid4 | 无状态登录态 + 过期时间 + Bearer 头 |
| 跨域 | CORSMiddleware | 前后端分离跨域支持 |
| 异常处理 | Starlette 异常体系 | 4 层全局异常处理器 + 统一响应格式 |
| 工程化 | 虚拟环境 / requirements.txt / 分层目录 | 环境隔离、依赖锁定、代码组织 |

---

## 七、简历项目经历

### 7.1 完整版（推荐直接使用）

---

**项目名称：AI掘金头条 —— 新闻资讯类 App 后端服务**

**项目简介**：仿"今日头条"的新闻资讯 App 后端，提供用户注册登录、新闻分类浏览、新闻详情（浏览量统计与相关推荐）、新闻收藏、浏览历史等完整功能，采用前后端分离架构。

**技术栈**：Python 3.12 · FastAPI · SQLAlchemy 2.0（异步）· MySQL · Redis · Pydantic v2 · passlib/bcrypt · Uvicorn

**核心工作**：

1. **架构设计**：采用分层架构（routers 接口层 / schemas 校验层 / crud 数据操作层 / models 模型层），模块间低耦合，职责单一；设计 6 张数据库表（用户、令牌、分类、新闻、收藏、历史），通过外键、联合唯一约束与合理索引（高频查询字段、排序字段）保证数据一致性与查询性能；
2. **接口开发**：独立开发 17 个 RESTful 接口，覆盖用户认证、新闻浏览、收藏、历史四大模块；实现基于 offset/limit 的分页与 hasMore 判断、浏览量原子自增（`views = views + 1`）、相关新闻多字段排序推荐等业务逻辑；
3. **认证与安全**：基于 bcrypt 的密码哈希存储与校验；自研 UUID Token 登录态机制（含 7 天过期校验），封装 `get_current_user` 鉴权依赖，通过 FastAPI 依赖注入在 10+ 个接口中复用；
4. **性能优化**：引入 Redis 实现 Cache-Aside 旁路缓存，对新闻分类（2h）、列表（30min）、详情（5min）分级设置 TTL 防缓存雪崩；缓存读写异常降级兜底，Redis 故障不影响主流程；通过 ORM↔Pydantic↔JSON 序列化链解决复杂对象缓存问题；
5. **工程规范**：统一 `{code, message, data}` 响应格式；设计 4 层全局异常处理（业务异常/数据库完整性约束/ORM 错误/兜底异常），将底层报错翻译为友好提示；DEBUG 开关区分开发/生产错误信息；Pydantic alias 机制统一前后端命名规范（camelCase ↔ snake_case）。

**项目成果**：完整交付可运行的新闻 App 后端，接口全部通过 Swagger 联调验证；Redis 缓存命中时新闻列表/详情接口直接返回内存数据，显著降低数据库压力；代码结构清晰规范，作为教学范例被用于 FastAPI 全栈课程讲解。

---

### 7.2 精简版（简历空间紧张时使用）

---

**AI掘金头条（新闻资讯 App 后端）** | Python · FastAPI · SQLAlchemy · MySQL · Redis

- 分层架构设计 6 张表、17 个 RESTful 接口，覆盖用户/新闻/收藏/历史四大模块；
- bcrypt 密码加密 + UUID Token 鉴权依赖，登录态校验复用 10+ 接口；
- Redis Cache-Aside 缓存新闻热点数据，分级 TTL 防雪崩，故障自动降级；
- 统一响应格式 + 4 层全局异常处理，数据库错误友好化，前后端命名规范统一。

---

## 八、项目亮点与可优化点

### 🌟 值得学习的亮点

1. **教学级的代码演进痕迹**：`crud/news.py`（无缓存）与 `crud/news_cache.py`（有缓存）并存，一眼看懂"如何给已有模块加缓存"；
2. **依赖注入用得漂亮**：`get_db` 管事务生命周期（成功 commit / 失败 rollback / 结束 close），`get_current_user` 管鉴权，接口函数体非常干净；
3. **缓存工程细节到位**：key 命名空间规范、TTL 分级防雪崩、读写异常降级、ORM 序列化链完整；
4. **异常处理是加分项**：把数据库底层错误翻译成用户能看懂的话，这是很多初级项目没有的；
5. **索引设计有意识**：每个表都按"查询条件 + 排序字段"设计索引，favorite 用联合唯一约束做防重。

### 🔧 可继续优化的点（面试可主动提）

1. `models/users.py` 中 `default=datetime.now()` 带括号，是"导入时定死时间"的经典小坑（news/history 的写法才对），可改为 `datetime.now`；
2. Redis 缓存与数据库存在"缓存更新滞后"问题（浏览量 +1 后详情缓存 5 分钟内仍显示旧值），可引入"先更库再删缓存"或延迟双删策略；
3. `create_token` 的 upsert 逻辑中，更新分支依赖 `get_db` 的末尾 commit 兜底，显式 commit 更稳妥；
4. 数据库连接串硬编码在代码里，可用 `python-dotenv` 读取 `.env`（依赖已装，未使用）；
5. 密码 Token 是数据库存储型，可升级为 JWT 无状态方案（免查库、可跨服务）；
6. 分页可升级为"游标分页"，大数据量下比 offset 分页更快；
7. 可补充单元测试（pytest + httpx）与接口自动化测试。

---

*本文档由逐文件阅读项目源码生成，仅供学习交流使用。*
