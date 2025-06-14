from flask import Flask, jsonify, request
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
# *** 修复 #1: 更新模型路径以匹配新的表格模型训练脚本 ***
MODEL_PATH = os.path.join('models', 'ag-aqi-predictor-tabular')
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
    *** 修复 #2: 重写此函数以在推理时正确生成所需的特征工程 ***

    为预测创建特征输入。此函数现在会:
    1. 读取最近的历史数据。
    2. 计算与训练时完全相同的滑动平均和其他特征。
    3. 返回一个与模型期望的输入格式完全匹配的DataFrame。
    """
    try:
        df = pd.read_csv(DATA_PATH, parse_dates=['date'])
        
        # 使用最新的数据来模拟第二天的输入
        last_known_record = df.tail(1).iloc[0]
        next_day = last_known_record['date'] + datetime.timedelta(days=1)
        
        # 准备一个包含足够历史数据的临时df来计算滑动平均
        # 我们需要至少6天的历史数据来为新的一天计算7日滑动平均
        history_df = df.tail(6).copy()
        # 将最新的真实数据添加到这个历史记录的末尾
        new_row = pd.DataFrame([last_known_record])
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        history_df.set_index('date', inplace=True)

        # 为新的一天计算滑动平均特征
        rolling_features = ['pm25', 'o3', 'TEMP', 'WDSP']
        new_features = {}
        for feature in rolling_features:
            # 计算7天滑动平均值 (包括今天)
            rolling_mean = history_df[feature].rolling(window=7, min_periods=1).mean().iloc[-1]
            new_features[f'{feature}_7d_mean'] = rolling_mean
            
        # 准备最终的输入DataFrame
        input_df = pd.DataFrame({
            # 原始特征 (使用最后一天的值作为预估)
            'pm25': [last_known_record['pm25']],
            'o3': [last_known_record['o3']],
            'TEMP': [last_known_record['TEMP']],
            'WDSP': [last_known_record['WDSP']],
            'PRCP': [last_known_record['PRCP']],
            # 时间特征
            'month': [next_day.month],
            'day_of_year': [next_day.dayofyear],
            'weekday': [next_day.weekday()],
            # 新的滑动平均特征
            'pm25_7d_mean': [new_features['pm25_7d_mean']],
            'o3_7d_mean': [new_features['o3_7d_mean']],
            'TEMP_7d_mean': [new_features['TEMP_7d_mean']],
            'WDSP_7d_mean': [new_features['WDSP_7d_mean']],
        })

        # 确保列的顺序和模型训练时一致
        if predictor:
            input_df = input_df[predictor.features()]

        return input_df

    except FileNotFoundError:
        print(f"数据文件未找到于 {DATA_PATH}")
        return None
    except Exception as e:
        print(f"为预测准备输入数据时出错: {e}")
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