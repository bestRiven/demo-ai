# 全球城市空气质量预测原型

本项目是为ABC公司设计和开发的一个解决方案原型，旨在展示如何利用AWS云服务和机器学习技术，构建一个可扩展、高效的全球城市空气质量预测平台。

## 项目目标

- **核心功能**: 预测未来24小时的城市空气质量指数（AQI）。
- **技术栈**:
  - **机器学习**: 使用`AutoGluon`进行自动化模型训练和选择。
  - **后端**: 使用`Flask`构建轻量级API服务。
  - **前端**: 使用原生`HTML/CSS/JS`构建交互式用户界面。
  - **数据源**: 模拟来自`NOAA`（天气数据）和`OpenAQ`（空气质量数据）的数据。
- **解决客户痛点**:
  - **可扩展性**: 提出的AWS架构可以轻松扩展以应对数据量的增长。
  - **集成开发环境 (IDE)**: 推荐使用`Amazon SageMaker Studio`作为云端一体化ML开发环境。
  - **AutoML**: 直接使用`AutoGluon`库，并推荐在`Amazon SageMaker`上进行大规模自动化模型评估。
  - **GenAI图片生成**: 模拟了通过AI生成符合情景的图片的过程，并推荐使用`Amazon Bedrock`实现。

## 项目结构

```
.
├── ARCHITECTURE.md     # AWS 架构设计文档
├── backend             # 后端 Flask 应用
│   └── app.py
├── data                # 存放样本数据
│   ├── noaa_gsod_chicago_sample.csv
│   └── openaq_chicago_sample.csv
├── frontend            # 前端页面
│   ├── images          # 存放基于AQI生成的图片
│   │   ├── good.png
│   │   ├── moderate.png
│   │   └── unhealthy.png
│   ├── index.html
│   ├── script.js
│   └── style.css
├── ml                  # 机器学习相关代码
│   ├── aqi.py          # AQI 计算逻辑
│   ├── prepare_data.py # 数据准备脚本
│   └── train.py        # 模型训练脚本
├── models              # 存放训练好的模型 (由train.py自动生成)
├── README.md           # 项目说明 (本文档)
└── requirements.txt    # Python 依赖
```

## 如何运行

**先决条件**:
- Python 3.8+
- 安装了所有在 `requirements.txt` 中列出的依赖。

**重要提示**: 请确保您在项目的根目录下打开终端，并从根目录执行以下所有命令。

**1. 安装依赖**:

打开终端，进入项目根目录，然后运行：
```bash
pip install -r requirements.txt
```
*注意: `AutoGluon` 是一个较大的库，安装可能需要一些时间。*

**2. 准备数据和训练模型**:

依次运行以下脚本来准备数据和训练模型。模型文件将保存在 `models/` 目录下。

```bash
# 步骤 1: 准备和合并数据
python ml/prepare_data.py

# 步骤 2: 训练模型 (此过程可能需要几分钟)
python ml/train.py
```

**3. 启动后端服务**:

```bash
# 运行 Flask 应用
python backend/app.py
```
服务启动后，你将看到类似 `* Running on http://127.0.0.1:5000` 的输出。

**4. 查看前端页面**:

在你的文件浏览器中，找到 `frontend/` 目录，然后用网页浏览器打开 `index.html` 文件。

点击 "预测空气质量" 按钮，你就可以看到芝加哥未来24小时的AQI预测结果、健康建议和一张由"AI生成"的图片。

## 架构设计

关于如何在AWS上部署此解决方案以实现生产级的可扩展性、可靠性和自动化，请参阅 `ARCHITECTURE.md` 文件。 
