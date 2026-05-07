from flask import Flask, jsonify
from flask_cors import CORS
import random

app = Flask(__name__)

# 允许所有来源的跨域请求（开发环境推荐；生产环境建议指定具体域名）
CORS(app)

@app.route('/api/vocs/prediction', methods=['GET'])
def vocs_prediction():
    """
    返回未来6小时(每半小时一个点，共12个点)的VOCs浓度预测值
    每个值为20~80之间的随机浮点数，保留2位小数
    """
    predictions = [round(random.uniform(20, 80), 2) for _ in range(12)]
    return jsonify({"predictions": predictions})

if __name__ == '__main__':
    # debug=True 在开发时开启，保存代码后自动重载
    app.run(debug=True, port=5000)