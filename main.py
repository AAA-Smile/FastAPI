from fastapi import FastAPI, Query, Path , HTTPException
from fastapi.params import Depends
from pydantic import BaseModel , Field
from fastapi.responses import HTMLResponse , FileResponse
from sqlalchemy.ext.asyncio import create_async_engine , async_sessionmaker , AsyncSession
from sqlalchemy.orm import DeclarativeBase , Mapped , mapped_column
from sqlalchemy import DateTime, func , Float , String , select

#先创建FastAPI实例
app = FastAPI()

#运行代码使用 uvicorn main:app --reload
#其中关于uvicorn后跟着的参数 main是文件名 app是FastAPI实例名 要根据实际命名情况进行修改 reload用于即时刷新
#定义一个跟路由
@app.get('/')
async def root():
    return {'msg' : 'Hello World'}

#弹出的URL后缀加上 docs 可进入调试文档实时查看、调试个人编写的所有接口


#定义路径参数路由
#book路径后跟着一个id参数，在调试界面可以自定义输入数字显示具体返回内容
@app.get('/books/{id}')
async def get_book(id : int):#约束参数类型，无法输入int以外的类型字符
    return {'id' : id , 'mes' : f'这是第{id}本书'}
#路径参数加入Path进行参数限制
'''
1、...代表是必填项
2、ge/gt 大于等于/大于
3、le/lt 小于等于/小于
4、description 描述
5、min_length,max_length 限制最小长度以及最大长度
6、default 定义默认值
'''
@app.get("/user/{id}")
async def get_user(id : int = Path(... , ge = 1 , le = 100 , description = '用户id 范围1-100')):
    return {'id' : id , 'msg' : f'这是第{id}个用户'}

#定义查询参数路由
#在方法名内定义参数，在docs文档内可对定义参数进行编辑操作，Query同样作为查询参数的类型注解，常用定义和Path一模一样
#查询参数是跟在域名？后的数值，即请求行
@app.get('/news/new_list')
async def get_new_list(
        skip : int = Query(0 , description = '跳过记录数') ,
        limit : int = Query(10 , description = '返回记录数')
):
    return {'skip' : skip , 'limit' : limit}

#定义请求体参数路由
#请求体通常包含许多参数类型以及部分信息需要保密，需要先定义一个Pydantic模型类
'''
Pydantic模型类通常用于：
1、定义请求体的结构，规定前端发来的Json必须包含定义字段
2、数据校验，检查前端发来的字段类型是否符合规定
3、数据转换，将前端传来的Json数据自动转化为Python对象，以便于取值
'''
#定义模型类需要继承基类BaseModel
class User(BaseModel):
    username : str
    password : str
@app.post('/register')#请求体参数路由类型为POST
async def register(user:User):
    return user.username , user.password
#同时呢在请求体参数的Pydantic模型类中也有Field函数可以约束参数，同样和Path约束无二
#这里我们来简单定义一个图书录入接口
class Books(BaseModel):
    book_name : str = Field(... , min_length = 2 , max_length = 20)
    book_author : str = Field(... , min_length = 1)
    book_price : float = Field(... , gt = 0)
@app.post('/book/into')
async def book_into(books : Books):
    return books.book_name , books.book_author , books.book_price


#响应类型
#1、返回网页（HTML）
#这个响应类型不返回Json数据，直接返回一个浏览器能识别的网页代码
#查看方法：运行代码后在域名后输入接口名即可查看
@app.get('/html' , response_class = HTMLResponse)
async def get_html():
    return '<h1>Hello World</h1>'

#2、返回图片/文件（FileResponse）
#访问这个地址会直接弹出一张图片或者下载一个文件
@app.get('/file' , response_class = FileResponse)
async def get_file():
    return FileResponse('1786551117045.jpg')

#3、当然还可以自定义响应数据格式
#下面我们尝试来定义一个新闻接口：其中包含元素有新闻id、标题、内容
class News(BaseModel):
    id : int
    title : str
    content : str
@app.get('/news/{id}' , response_model = News)
async def get_new(id : int):
    return {
        'id' : id ,
        'title' : f'这是第{id}本书' ,
        'content' : f'这是一本好书'
    }


#异常处理
#status_code 定义错误代码 raise用于抛出异常 detail用于定义具体错误信息
@app.get('/news1/{id}')
async def get_news(id : int) :
    if id not in [1,2,3,4,5]:
        raise HTTPException(status_code=404 , detail = '该id值不存在')
    return {'id' : id}

#中间件middleware -- 为每个请求前后添加统一的处理逻辑 -- 控制的是所有接口
#中间件代码运行按照代码顺序自下而上执行
#request - 请求 ， call_next - 传递请求的函数
@app.middleware('http')
async def middleware(request , call_next):
    print('=====中间件1开始运行=====')
    response = await call_next(request)
    print('=====中间件1结束运行=====')
    return response
#当再添加一个中间件时，代码块执行顺序是从下到上 -- 具体结果可看终端显示，刷新域名之后会很清晰的显示出来
#即中间件2开始运行 - 中间件1开始运行 - 中间件1结束运行 - 中间件2结束运行
@app.middleware('http')
async def middleware(request , call_next):
    print('=====中间件2开始运行=====')
    response = await call_next(request)
    print('=====中间件2结束运行=====')
    return response


#数据库相关 -- SQLAlchemy
#1、创建数据库引擎
ASYNC_DATABASE_URL = 'mysql+aiomysql://root:123456@localhost:3306/fastapi_first?charset=utf8'
async_engine = create_async_engine(
    ASYNC_DATABASE_URL ,
    echo = True, #输出SQL日志
    pool_size = 10, #设置连接池中保持连接的永久活跃连接数
    max_overflow = 20 , #设置连接池允许创建的额外连接数
)

#2、定义数据表结构
#通常可以先定义一个通用SQLAlchemy基类，再根据需要的表结构额外定义数据表SQLAlchemy模型类
#表模型类继承基类即可获得基类定义表结构
#定义SQLAlchemy基类需要继承DeclarativeBase
class Base(DeclarativeBase):
    """
    Mapped定义的是Python里的类型提示
    mapped_column是列定义函数，声明的是数据库内列类型以及列初始值
    default是端口内的初始值,ORM层面默认值
    insert_default是数据库端默认值
    onupdate触发更新时的默认值，作用对象是数据库
    """
    create_time : Mapped[DateTime] = mapped_column(DateTime ,
                                                   insert_default = func.now() ,#数据库端默认值，需要添加括号调用
                                                   default= func.now)
    update_time : Mapped[DateTime] = mapped_column(DateTime ,
                                                   insert_default= func.now() ,
                                                   default= func.now ,
                                                   onupdate= func.now())
#我们再来定义一个SQLAlchemy表模型类，继承基类 -- 定义一个图书表吧
class Book(Base):
    __tablename__ = 'book'

    id : Mapped[int] = mapped_column(primary_key=True , comment = '书籍id')
    book_name : Mapped[str] = mapped_column(String(255) , comment = '书籍名称')
    author : Mapped[str] = mapped_column(String(255) , comment = '书籍作者')
    publisher : Mapped[str] = mapped_column(String(255) , comment = '书籍出版社')
    price : Mapped[float] = mapped_column(Float , comment = '书籍价格')

#3、建表，定义函数建表，在启动fastapi时调用建表函数
async def create_table():
    #获取异步引擎 -- 创建事务、建表
    """
    .begin()：开启一个数据库事务
    async with：保证在代码块执行完毕后，如果没报错就自动 COMMIT（提交），如果报错了就自动 ROLLBACK（回滚）。
    conn：代表当前数据库连接（异步版）
    """
    async with async_engine.begin() as conn:
        #metadata--是Base的容器，所有继承基类的SQLAlchemy模型类
        #run_sync用于将一个步骤规划进线程池里
        await conn.run_sync(Base.metadata.create_all) #Base模型类的元数据创建
#启动FastAPI时调用建表函数 await -- 在异步环境中调用可等待函数
@app.on_event('startup')
async def startup_event():
    await create_table()
#这时重启fastapi或者刷新浏览器即可看到终端的建表语句，在数据库中即可查看到新增内容

#路由匹配中使用ORM -- 创建依赖项，使用Depends注入到处理函数
#依赖注入：创建依赖项获取数据库会话 + Depends注入路由处理函数
#首先要创建一个异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    #绑定数据库异步引擎
    bind = async_engine ,
    #指定会话类
    class_ = AsyncSession ,
    #设置提交后会话不过期，不会重新查询数据库
    expire_on_commit = False
)
#定义依赖项函数
async def get_db():
    async with AsyncSessionLocal() as session :
        try :
            #返回数据库会话给路由处理函数
            #依赖注入的暂停和恢复 -- 将数据库连接借给接口用
            yield session
            #commit() 提交事务
            await session.commit()
        except Exception :
            #如果有异常则回滚
            await session.rollback()
            #抛出异常给FastAPI捕获
            raise
        finally :
            #关闭会话
            await session.close()
#让我们尝试使用一下依赖注入：在调用函数时使用依赖项连接数据库
#这时需要确保数据库表中有数据，自行添加几条数据(我这采用在MySQL数据库中输入指令的方式)
"""
INSERT INTO book (book_name, author, publisher, price, create_time, update_time) VALUES 
('三体', '刘慈欣', '重庆出版社', 58.00, NOW(), NOW()),
('活着', '余华', '作家出版社', 25.00, NOW(), NOW()),
('百年孤独', '加西亚·马尔克斯', '南海出版公司', 68.00, NOW(), NOW()),
('人类简史', '尤瓦尔·赫拉利', '中信出版社', 79.00, NOW(), NOW()),
('算法导论', 'Thomas H. Cormen', '机械工业出版社', 168.00, NOW(), NOW()),
('深入理解计算机系统', 'Randal E. Bryant', '机械工业出版社', 139.00, NOW(), NOW()),
('你当像鸟飞往你的山', '塔拉·韦斯特弗', '南海出版公司', 59.80, NOW(), NOW()),
('平凡的世界', '路遥', '北京十月文艺出版社', 79.80, NOW(), NOW()),
('白夜行', '东野圭吾', '南海出版公司', 45.00, NOW(), NOW()),
('经济学原理', '曼昆', '北京大学出版社', 88.00, NOW(), NOW()),
('Python编程从入门到实践', 'Eric Matthes', '人民邮电出版社', 89.00, NOW(), NOW()),
('数据结构与算法分析', 'Mark Allen Weiss', '机械工业出版社', 79.00, NOW(), NOW()),
('月亮与六便士', '毛姆', '上海译文出版社', 48.00, NOW(), NOW()),
('未来简史', '尤瓦尔·赫拉利', '中信出版社', 82.00, NOW(), NOW()),
('围城', '钱钟书', '人民文学出版社', 36.00, NOW(), NOW()),
('黑客与画家', 'Paul Graham', '人民邮电出版社', 69.00, NOW(), NOW()),
('明朝那些事儿', '当年明月', '浙江人民出版社', 99.00, NOW(), NOW()),
('边城', '沈从文', '江苏文艺出版社', 29.80, NOW(), NOW()),
('时间的秩序', '卡洛·罗韦利', '湖南科学技术出版社', 56.00, NOW(), NOW()),
('流畅的Python', 'Luciano Ramalho', '人民邮电出版社', 119.00, NOW(), NOW());
"""
#使用Depends进行依赖注入
@app.get('/books1/book')
async def get_book_list(db : AsyncSession = Depends(get_db)):
    #execute返回的是OMR对象，执行数据库语句
    result = await db.execute(select(Book))
    #scalars是为了将对象转换为具体的Python对象，all()是获取全部数据
    book = result.scalars().all()
    return book

#CRUD操作 -- 进行真正的增删改查操作
"""
其实在上面的Depends依赖注入处就简单演示了一次查询函数的编写
接下来我们详细的来编写几个查询函数
包括：
1、普通查询函数
2、条件查询函数
3、模糊查询函数
4、分页查询函数
"""
@app.get('/books2/book')
async def get_book_list(db : AsyncSession = Depends(get_db)):
    #单条查询语句，返回的是数据表中的第一个数据 -- first()
    book1 = await db.execute(select(Book))
    result1 = book1.scalars().first()
    #获取指定数据表主键数值的数据 -- get() 其中参数第一个为数据表名称，第二个为想要主键值
    book2 = await db.get(Book , 2)
    return result1 , book2
#条件查询
#我们来模拟一下这个场景：需要判断用户输入的书本ID在数据库中是否存在
#存在就输出数据库中ID值对应信息，不存在返回null
@app.get('/books3/{id}')
async def select_id(id : int , db : AsyncSession = Depends(get_db)):
    book = await db.execute(select(Book).where(Book.id == id))
    # scalar_one_or_none()意思是如果有结果就返回对应的单个结果，没有就返回null
    result = book.scalar_one_or_none()
    return result
#现在我们需要查询数据表中书籍价格大于100的书本
@app.get('/books4/search_book')
async def select_book_by_price(db : AsyncSession = Depends(get_db)):
    book = await db.execute(select(Book).where(Book.price > 100))
    result = book.scalars().all()
    return result
#模糊查询 -- like() '%'代表零个或多个字符 , '_'表示单个字符 , '&'表示和 , '|'表示或 , 'in_'表示在对应内容内
#我们现在查询一下数据表中作者由T开头的
@app.get('/books5/name')
async def search_name(db : AsyncSession = Depends(get_db)):
    name = await db.execute(select(Book).where(Book.author.like('T%')))
    result = name.scalars().all()
    return result
#接下来演示一下关于和与或的使用，我这就以&为例,查询一下作者为T开头且价格大于100的
@app.get('/books6/search_book')
async def search_book(db : AsyncSession = Depends(get_db)):
    book = await db.execute(select(Book).where((Book.author.like('T%')) & (Book.price > 100)))
    result = book.scalars().all()
    return result
#聚合查询 -- 使用方法func.聚类方法名称
#count 计数 , avg 平均 , min 最小值 , max 最大值 , sum 求和
#scalar() 提取标量值，返回的是数值，配合聚合查询使用
@app.get('/book8/statistics')
async def get_book_statistics(db: AsyncSession = Depends(get_db)):
    # 1. 构建一次查询，获取所有聚合值（不再分开查 5 次！）
    #其中的label是给查询结果列起别名
    stmt = select(
        func.count(Book.id).label("total_count"),
        func.round(func.avg(Book.price), 2).label("avg_price"),
        func.min(Book.price).label("min_price"),
        func.max(Book.price).label("max_price"),
        func.round(func.sum(Book.price), 2).label("sum_price")
    )

    # 2. 执行查询（只发一次网络请求给数据库）
    result = await db.execute(stmt)
    row = result.one()  # 聚合查询永远只返回一行

    # 3. 返回一个结构清晰的 JSON 对象（不再是乱糟糟的元组）
    return {
        "total_count": row.total_count or 0,  # 处理空表情况
        "avg_price": float(row.avg_price) if row.avg_price is not None else 0.0,
        "min_price": float(row.min_price) if row.min_price is not None else 0.0,
        "max_price": float(row.max_price) if row.max_price is not None else 0.0,
        "sum_price": float(row.sum_price) if row.sum_price is not None else 0.0,
    }
#分页查询
#offset() 跳过的记录数, limit() 展示的记录数
@app.get('/books9/list')
async def get_book_list(
        page : int = 1 ,
        page_size : int = 10 ,
        db : AsyncSession = Depends(get_db)
):
    #跳过数目 = （当前页数 - 1） * 当页展示数目
    skip = (page - 1) * page_size
    book_list = await db.execute(select(Book).offset(skip).limit(page_size))
    result = book_list.scalars().all()
    return result

#新增数据
#我们来简单定义一个新增图书的接口
"""
用户输入书本相关信息 -- 新增 -- 书名、作者、出版社、价格
用户输入 -- 参数 -- 请求体
"""
#新增信息不可能直接在域名之后显示出来，所以要先定义一个请求体参数路由
class BookBase(BaseModel):
    book_name : str
    author : str
    publisher : str
    price : float
@app.post('/books10/add')
async def add_book(book : BookBase , db : AsyncSession = Depends(get_db)):
    #对输入的Json数据格式进行解包填入数据表中
    new_book = Book(**book.__dict__)
    db.add(new_book)
    await db.commit()
    return book
#这个时候去数据库中就能查询到刚刚添加的新数据

#修改数据 -- 使用PUT接口
#操作步骤一般为 get查找数据表中是否存在这本书 -- 进行重新赋值 -- commit提交到数据库
#因为修改的数据类型和BookBase类中定义的数据一样，所以我们在这里继续复用
@app.put('/books11/update/{id}')
async def update_book(id : int , date : BookBase , db : AsyncSession = Depends(get_db)):
    #数据表中查询该id书本
    db_book = await db.get(Book , id)
    if db_book is None :
        raise HTTPException(status_code= 404 , detail= '该书不存在')
    """
    这里重新赋值可以采用每个重新赋值的方式
        db_book.book_name = data.book_name
        db_book.author = data.author
        db_book.publisher = data.publisher
        db_book.price = data.price
    但这种写法未免太臃肿，在生产中也很少会这样编写
    我们在这就使用setattr这个函数来重新赋值
    """
    #先将date数据转换为字典，并只取前端传入的数据
    update_date = date.model_dump(exclude_unset=True)
    for field , value in update_date.items():
        setattr(db_book , field , value)
    #别忘了提交
    await db.commit()
    return db_book

#删除数据 -- DELETE接口
#操作步骤和上面相同，一般需要修改数据库信息时都需要先查询数据库中国是否有这个项，再进行修改
@app.delete('/books/delete/{id}')
async def delete_book(id : int , db : AsyncSession = Depends(get_db)):
    db_book = await db.get(Book , id)
    if db_book is None :
        raise HTTPException(status_code= 404 , detail= '该书本不存在')
    await db.delete(db_book)
    await db.commit()
    return {'msg' : '已删除'}
#这时候再去查询数据表就会发现你输入的ID书已经删除了

"""
新手最容易犯的 3 个错（避坑指南）
忘记写 await：
错误：db.execute(select(Book))
正确：await db.execute(...)
原因：因为是异步（边干活边等），必须加 await 告诉程序“你等一下，我去拿数据”。

用错了提取数据的方法：
查多条用：.scalars().all()（返回列表）。
查单条用：.scalar_one_or_none()（返回一个对象或 None）。
灾难：如果你查多条用了 scalar_one_or_none()，数据库里只要有 2 本书，程序立刻崩溃报错（这就是你之前遇到的 Internal Server Error）。

更新或删除后忘记 commit：
如果你只写了 db.add() 或 db.delete()，没写 await db.commit()，关掉程序后数据根本没变。commit 是“保存”按钮，不按等于白干！
"""