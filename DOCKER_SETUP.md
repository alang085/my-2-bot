# Docker 安装和设置指南

## 🔍 检查 Docker 是否已安装

如果命令 `docker --version` 不工作，需要先安装 Docker。

---

## 🐳 Windows 安装 Docker

### 方法1：Docker Desktop（推荐）

#### 步骤1：下载 Docker Desktop

1. 访问：https://www.docker.com/products/docker-desktop/
2. 点击 "Download for Windows"
3. 下载 Docker Desktop 安装程序

#### 步骤2：安装 Docker Desktop

1. 运行安装程序
2. 按照向导完成安装
3. 安装完成后重启电脑

#### 步骤3：启动 Docker Desktop

1. 从开始菜单启动 "Docker Desktop"
2. 等待 Docker 启动完成（系统托盘图标不再动画）
3. 验证安装：在 PowerShell 中运行：
   ```powershell
   docker --version
   docker run hello-world
   ```

---

## 🚀 如果不想安装 Docker Desktop

### 方案A：使用 GitLab CI/CD 自动构建

GitLab 可以自动构建 Docker 镜像，无需本地安装 Docker。

#### 创建 .gitlab-ci.yml

在项目根目录创建 `.gitlab-ci.yml` 文件：

```yaml
stages:
  - build

build-image:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:latest .
    - docker push $CI_REGISTRY_IMAGE:latest
  only:
    - main
```

这样每次推送代码到 main 分支时，GitLab 会自动构建并推送镜像到 Container Registry。

---

### 方案B：使用在线构建服务

可以使用在线 Docker 构建服务，无需本地安装：

1. **GitHub Actions**（如果 GitHub 可用）
2. **GitLab CI/CD**（推荐，你的代码已在 GitLab）
3. **Docker Hub Automated Build**（连接 GitHub/GitLab）

---

## 🎯 推荐方案：使用 GitLab CI/CD

由于你的代码已在 GitLab，最简单的方法是使用 GitLab CI/CD 自动构建。

### 步骤1：创建 .gitlab-ci.yml

我帮你创建这个文件，GitLab 会自动构建镜像。

### 步骤2：推送代码

推送后，GitLab 会自动：
1. 检测到 .gitlab-ci.yml
2. 构建 Docker 镜像
3. 推送到 GitLab Container Registry

### 步骤3：使用镜像

镜像地址：`registry.gitlab.com/alang085-group/my-bot1:latest`

---

## 📝 你希望使用哪种方案？

1. **安装 Docker Desktop**（本地构建，更灵活）
2. **使用 GitLab CI/CD**（自动构建，无需本地安装）⭐ 推荐
3. **其他方案**

告诉我你的选择，我会帮你配置！

