# 学生管理系统

一个简单的学生管理系统，使用FastAPI和SQLAlchemy构建。

## 功能特性

- 创建学生记录
- 根据学号查询学生信息
- 自动测试覆盖

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
python main.py
```

应用将在 http://localhost:9000 启动

## API接口

### 获取根路径
```
GET /
```

### 创建学生
```
POST /students/
Content-Type: application/json

{
    "name": "张三",
    "student_id": 1001
}
```

### 查询学生
```
GET /students/{student_id}
```

## 运行测试

### 方法1：使用测试脚本
```bash
python run_tests.py
```

### 方法2：直接使用pytest
```bash
pytest test_main.py -v
```

### 方法3：使用pytest配置文件
```bash
pytest
```

## 测试覆盖

测试包括以下功能：

- ✅ 根路径访问
- ✅ 创建学生记录
- ✅ 查询存在的学生
- ✅ 查询不存在的学生
- ✅ 创建多个学生
- ✅ 重复学号处理
- ✅ 无效数据验证

## 环境配置

- 开发环境：使用PostgreSQL数据库
- 测试环境：使用SQLite内存数据库（自动切换）

## 项目结构

```
.
├── main.py              # 主应用文件
├── test_main.py         # 测试文件
├── requirements.txt     # 依赖列表
├── pytest.ini          # pytest配置
├── run_tests.py        # 测试运行脚本
└── README.md           # 项目说明
``` 