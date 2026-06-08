from flask import Flask, request, jsonify
from CoolProp.CoolProp import PropsSI
import os

app = Flask(__name__)

# --- 核心计算逻辑 ---
def analyze_refrigeration_cycle(refrigerant, P1_kPa, T1_C, P2_kPa, T2_C, subcooling_C=5.0):
    # 单位转换 (CoolProp 底层必须使用 Pa 和 K)
    P1 = P1_kPa * 1000.0
    P2 = P2_kPa * 1000.0
    T1 = T1_C + 273.15
    T2 = T2_C + 273.15
    results = {}
    
    try:
        # 防液击检查：判断吸气温度是否低于饱和温度
        T1_sat_K = PropsSI('T', 'P', P1, 'Q', 1, refrigerant)
        T1_sat_C = T1_sat_K - 273.15
        if T1 <= T1_sat_K:
            return {"error": f"吸气温度({T1_C}°C) ≤ 饱和温度({round(T1_sat_C,2)}°C)。系统可能发生湿压缩，无法计算！"}
            
        # 压缩机做功与等熵效率
        h1 = PropsSI('H', 'P', P1, 'T', T1, refrigerant)
        s1 = PropsSI('S', 'P', P1, 'T', T1, refrigerant)
        h2 = PropsSI('H', 'P', P2, 'T', T2, refrigerant)
        h2s = PropsSI('H', 'P', P2, 'S', s1, refrigerant)
        
        W_act = h2 - h1
        W_is = h2s - h1
        eta_is = (W_is / W_act) * 100
        
        # COP 计算
        T_cond_K = PropsSI('T', 'P', P2, 'Q', 0, refrigerant)
        T3_K = T_cond_K - subcooling_C
        h3 = PropsSI('H', 'P', P2, 'T', T3_K, refrigerant)
        h4 = h3 
        
        Q_e = h1 - h4
        COP = Q_e / W_act
        
        # 组装返回数据
        results['等熵效率(%)'] = round(eta_is, 2)
        results['系统COP'] = round(COP, 2)
        results['冷凝温度(°C)'] = round(T_cond_K - 273.15, 2)
        results['单位制冷量(kJ/kg)'] = round(Q_e / 1000, 2)
        
        return results

    except Exception as e:
        return {"error": f"CoolProp 计算报错: {str(e)}"}

# --- API 接口路由 ---
@app.route('/api/calculate_cop', methods=['POST'])
def calculate_cop():
    try:
        # 接收小程序或前端发来的 JSON 数据
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "没有收到 JSON 数据"}), 400
            
        # 提取参数，设置默认值
        refrigerant = data.get('refrigerant', 'R410A')
        P1_kPa = float(data.get('P1_kPa'))
        T1_C = float(data.get('T1_C'))
        P2_kPa = float(data.get('P2_kPa'))
        T2_C = float(data.get('T2_C'))
        subcooling_C = float(data.get('subcooling_C', 5.0))
        
        # 调用核心计算函数
        result = analyze_refrigeration_cycle(refrigerant, P1_kPa, T1_C, P2_kPa, T2_C, subcooling_C)
        
        # 如果计算逻辑中抛出了自定义错误
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
            
        # 成功返回
        return jsonify({"status": "success", "data": result})
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"参数解析错误或缺少必要参数: {str(e)}"}), 400

if __name__ == '__main__':
    # 微信云托管会自动注入 PORT 环境变量，通常是 80 端口
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
