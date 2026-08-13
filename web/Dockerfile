FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY package.json ./

# 安装所有依赖（包括 devDependencies）
RUN npm install

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
