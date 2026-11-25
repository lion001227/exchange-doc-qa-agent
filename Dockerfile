FROM python:3.11-slim
WORKDIR /app
#安装Python依赖
COPY requirements.txt .
RUN  pip install --no-cache-dir -r requirements.txt
#复制项目代码
COPY . .
#streamlit和fastapi端口
EXPOSE 8501 8000
#默认启动前端
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
