from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
from torchvision import models, transforms
from PIL import Image
import requests
from io import BytesIO
import torch

# 根据环境选择数据库URL
if os.getenv("TESTING") == "true":
    DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    DATABASE_URL = "postgresql://postgres:mysecretpassword@localhost:5432/postgres"
    engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class StudentDB(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    student_id = Column(Integer, unique=True, nullable=False)

class Student(BaseModel):
    name: str
    student_id: int

class PredictRequest(BaseModel):
    url: str

# 创建数据库表
def create_tables():
    if os.getenv("TESTING") != "true":
        Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/students/")
async def get_students(db: Session = Depends(get_db)):
    students = db.query(StudentDB).all()
    return [
        {"id": s.id, "name": s.name, "student_id": s.student_id}
        for s in students
    ]

@app.get("/students/{student_id}")
async def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(StudentDB).filter(StudentDB.student_id == student_id).first()
    if student is None:
        return {"error": "学生未找到"}
    return {"id": student.id, "name": student.name, "student_id": student.student_id}

@app.post("/students/")
async def create_student(student: Student, db: Session = Depends(get_db)):
    db_student = StudentDB(name=student.name, student_id=student.student_id)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return {"id": db_student.id, "name": db_student.name, "student_id": db_student.student_id}

@app.put("/students/{student_id}")
async def update_student(student_id: int, student: Student, db: Session = Depends(get_db)):
    db_student = db.query(StudentDB).filter(StudentDB.student_id == student_id).first()
    if db_student is None:
        return {"error": "学生未找到"}
    db_student.name = student.name
    db_student.student_id = student.student_id
    db.commit()
    db.refresh(db_student)
    return {"id": db_student.id, "name": db_student.name, "student_id": db_student.student_id}

@app.delete("/students/{student_id}")
async def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = db.query(StudentDB).filter(StudentDB.student_id == student_id).first()
    if db_student is None:
        return {"error": "学生未找到"}
    db.delete(db_student)
    db.commit()
    return {"message": "学生已删除"}

# 预加载 resnet50 模型和类别标签
resnet_model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
resnet_model.eval()

# 预处理方法
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
])

# 加载 imagenet 类别标签
LABELS_URL = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
response = requests.get(LABELS_URL)
IMAGENET_LABELS = response.text.strip().split("\n")

@app.post("/predict")
async def predict(req: PredictRequest):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        img_response = requests.get(req.url, headers=headers)
        if img_response.status_code != 200:
            return {"error": f"图片下载失败，状态码: {img_response.status_code}"}
        content_type = img_response.headers.get("Content-Type", "")
        if not content_type.startswith("image"):
            return {"error": f"URL内容不是图片，Content-Type: {content_type}"}
        img = Image.open(BytesIO(img_response.content)).convert("RGB")
    except Exception as e:
        return {"error": f"图片下载或打开失败: {str(e)}"}
    input_tensor = preprocess(img)
    input_batch = input_tensor.unsqueeze(0)
    with torch.no_grad():
        output = resnet_model(input_batch)
        probabilities = torch.nn.functional.softmax(output[0], dim=0)
        top5_prob, top5_catid = torch.topk(probabilities, 5)
    results = []
    for i in range(top5_prob.size(0)):
        results.append({
            "label": IMAGENET_LABELS[top5_catid[i]],
            "probability": float(top5_prob[i])
        })
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

