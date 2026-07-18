# ISDP 智能供需决策中心

一个面向 AI 产品经理 Demo 展示的智能供需决策系统（ISDP）原型，包含数据模拟引擎、场景化调度策略、A/B 实验闭环和 Streamlit 交互式驾驶舱。

## 核心能力

- 3 种业务场景切换：
  - 日常正常状态
  - 异常天气状态
  - 传统节假日
- 10 个时空网格，24 小时供需模拟
- 供需缺口、相对准时率、补贴金额、核心 ROI 等指标联动
- AI Agent 推理流程展示
- 一键下发策略与执行复盘
- A/B 实验结果对比

## 项目文件

- `app.py`：Streamlit 前端仪表盘入口
- `isdp_data_simulator_validation.py`：底层数据模拟与指标引擎
- `requirements.txt`：Python 依赖

## 本地启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
streamlit run app.py
```

### 3. 打开页面

启动后，终端会输出本地地址，通常是：

```bash
http://localhost:8501
```

用浏览器打开即可。

## 部署到 Streamlit Community Cloud

这是最适合当前 Demo 的部署方式，适合展示和持续迭代。

### 部署步骤

1. 将项目推送到 GitHub 仓库
2. 确保仓库包含以下文件：
   - `app.py`
   - `isdp_data_simulator_validation.py`
   - `requirements.txt`
3. 打开 [Streamlit Community Cloud](https://streamlit.io/cloud)
4. 使用 GitHub 登录并授权
5. 选择你的仓库
6. 将入口文件设置为 `app.py`
7. 点击部署

### 后续迭代

以后只要你在本地修改代码，然后执行：

```bash
git add .
git commit -m "update ISDP demo"
git push
```

Streamlit Cloud 会自动拉取最新代码并重新部署，网页地址通常保持不变。

## 运行要求

- Python 3.10+
- Streamlit
- Pandas

## 常见问题

### 1. 页面打不开
检查是否已安装依赖，并确认运行命令是：

```bash
streamlit run app.py
```

### 2. 依赖缺失
重新安装：

```bash
pip install -r requirements.txt
```

### 3. 部署后没更新
确认代码已经推送到 GitHub，并检查 Streamlit Cloud 是否完成自动重建。

## Demo 说明

本项目是一个演示级的智能供需决策系统，强调：

- 场景联动
- 指标闭环
- Agent 可解释性
- 一键式业务处置

适合用于：

- AI 产品经理作品集
- 路演 Demo
- 业务方案演示
- 招聘面试展示
