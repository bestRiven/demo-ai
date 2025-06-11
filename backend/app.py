from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
from autogluon.tabular import TabularPredictor
import os
import datetime

# 导入我们自定义的模块
from ml.aqi import get_aqi_category

# --- Flask 应用初始化 ---
# 将前端目录 `../frontend` 设置为静态文件目录，
# 并通过 `static_url_path=''` 让其可从根URL访问。
# 这样浏览器对 `/style.css` 的请求会自动映射到 `frontend/style.css` 文件。
app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app) # 允许跨域请求

# --- 全局变量 ---
MODEL_PATH = os.path.join('models', 'ag-aqi-predictor')
DATA_PATH = os.path.join('data', 'final_data.csv')
predictor = None

def load_model():
    """在服务启动时加载训练好的AutoGluon模型。"""
    global predictor
    if not os.path.exists(MODEL_PATH):
        print(f"错误: 模型目录未找到于 {MODEL_PATH}")
        print("请首先通过运行 `python ml/train.py` 来训练模型。")
        predictor = None
        return
        
    try:
        predictor = TabularPredictor.load(MODEL_PATH)
        print("模型加载成功。")
    except Exception as e:
        print(f"加载模型时出错: {e}")
        predictor = None

def get_prediction_input():
    """
    为预测创建特征输入。
    在真实场景中，这里应该获取实时的天气和空气质量数据。
    在此原型中，我们使用数据集中最新的记录来模拟第二天的输入特征。
    """
    try:
        df = pd.read_csv(DATA_PATH)
        
        last_record = df.tail(1).copy()
        last_date = pd.to_datetime(last_record['date'].iloc[0])
        next_date = last_date + datetime.timedelta(days=1)
        
        input_df = pd.DataFrame({
            'TEMP': last_record['TEMP'],
            'WDSP': last_record['WDSP'],
            'PRCP': last_record['PRCP'],
            'month': [next_date.month],
            'day': [next_date.day],
            'weekday': [next_date.weekday()],
            'pm25': last_record['pm25'],
            'o3': last_record['o3']
        })
        return input_df
    except FileNotFoundError:
        print(f"数据文件未找到于 {DATA_PATH}")
        return None

@app.route('/api/predict/<city>', methods=['GET'])
def predict(city):
    """API端点，用于获取指定城市的AQI预测结果。"""
    if predictor is None:
        return jsonify({"error": "模型尚未加载，请检查服务器日志。"}), 500

    # 注意：在此原型中，我们仅支持 'chicago'。
    # 在生产环境中，这里会有一个系统来处理不同城市的数据。
    if city.lower() != 'chicago':
        return jsonify({"error": "在此原型中尚不支持该城市。"}), 404

    input_features = get_prediction_input()
    if input_features is None:
        return jsonify({"error": "无法为预测生成输入特征。"}), 500

    prediction = predictor.predict(input_features)
    predicted_aqi = int(prediction.iloc[0])

    category, health_info, level_code = get_aqi_category(predicted_aqi)

    # --- GenAI 图片模拟 ---
    # 真实系统会调用 Amazon Bedrock 等服务动态生成图片。
    # 这里我们根据AQI等级选择一张预置图片。
    # URL被构建为根相对路径，例如 '/images/good.png'。
    image_name = f"{level_code}.png"
    image_url = f"/images/{image_name}"

    response = {
        "city": city.capitalize(),
        "predicted_aqi": predicted_aqi,
        "category": category,
        "health_advice": health_info,
        "image_url": image_url # 返回优化后的URL
    }

    return jsonify(response)

@app.route('/')
def index():
    """服务前端主页"""
    return app.send_static_file('index.html')

if __name__ == '__main__':
    load_model() # 服务启动时加载模型
    app.run(debug=True, port=5000) 