from flask import Flask, request, jsonify
from CoolProp.CoolProp import PropsSI
import os

app = Flask(__name__)

# --- 核心计算逻辑 ---
def analyze_refrigeration_cycle(refrigerant, P1_kPa, T1_C, P2_kPa, T2_C, subcooling_C=5.0):
    # 单位转换 (CoolProp 使用 Pa 和 K)
    P1 = P1_kPa * 1000.0
    P2 = P2_kPa * 1000.0
    T1 = T1_C + 273.15
    T2 = T2_C + 273.15
    results = {}

    try:
        # ── 0. 临界温度校验 ──
        try:
            T_crit = PropsSI('Tcrit', refrigerant)
            if T2 > T_crit:
                return {"error": f"排气温度({T1_C}°C)超过{refrigerant}临界温度({T_crit-273.15:.1f}°C)，无法进行亚临界循环计算"}
        except:
            return {"error": f"不支持的制冷剂: {refrigerant}"}

        # ── 1. 防液击检查 ──
        T1_sat_K = PropsSI('T', 'P', P1, 'Q', 1, refrigerant)
        T1_sat_C = T1_sat_K - 273.15
        # 加 0.1K 容差防止浮点误判
        if T1 < T1_sat_K + 0.1:
            return {"error": f"吸气温度({T1_C}°C) ≈ 饱和温度({round(T1_sat_C,2)}°C)，过热度不足，可能湿压缩！"}

        # ── 2. 压缩机做功与等熵效率 ──
        # CoolProp 焓值单位: J/kg，除以 1000 得到 kJ/kg
        h1 = PropsSI('H', 'P', P1, 'T', T1, refrigerant)
        s1 = PropsSI('S', 'P', P1, 'T', T1, refrigerant)
        h2 = PropsSI('H', 'P', P2, 'T', T2, refrigerant)
        h2s = PropsSI('H', 'P', P2, 'S', s1, refrigerant)

        W_act = h2 - h1     # 实际压缩功 (J/kg)
        W_is = h2s - h1     # 等熵压缩功 (J/kg)

        if W_act <= 0:
            return {"error": f"实际压缩功≤0，排气温度({T2_C}°C)必须高于吸气温度({T1_C}°C)"}

        # 等熵效率 = 等熵耗功 / 实际耗功（压缩机效率的正确定义）
        eta_is_decimal = W_is / W_act
        eta_is_pct = eta_is_decimal * 100.0

        # 工程合理性校验
        if eta_is_pct > 100:
            return {
                "error": f"计算等熵效率 {round(eta_is_pct,1)}% > 100%，"
                         f"说明输入的排气温度 T2({T2_C}°C) 低于等熵排气温度，数据不合理。"
                         f"请核实排气温度测量值。"
            }
        if eta_is_pct < 25:
            # 不阻断，但附加提示（严重偏离正常范围 50-85%）
            results['效率警告'] = f"等熵效率仅 {round(eta_is_pct,1)}%，远低于正常范围(50-85%)，请核实工况"

        # ── 3. COP 计算（含过冷度修正）──
        T_cond_K = PropsSI('T', 'P', P2, 'Q', 0, refrigerant)
        T3_K = T_cond_K - subcooling_C  # 温度差在 K 和 °C 之间是等价的
        h3 = PropsSI('H', 'P', P2, 'T', T3_K, refrigerant)
        h4 = h3  # 绝热节流，等焓过程

        Q_e = h1 - h4              # 单位制冷量 (J/kg)
        COP = Q_e / W_act          # 制冷 COP

        # ── 4. 组装返回 ──
        results['等熵效率(%)'] = round(eta_is_pct, 2)
        results['系统COP'] = round(COP, 2)
        results['冷凝温度(°C)'] = round(T_cond_K - 273.15, 2)
        results['单位制冷量(kJ/kg)'] = round(Q_e / 1000.0, 2)  # J/kg → kJ/kg

        return results

    except Exception as e:
        return {"error": f"CoolProp 计算异常: {str(e)}"}


# --- API 接口路由 ---
@app.route('/api/calculate_cop', methods=['POST'])
def calculate_cop():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "没有收到 JSON 数据"}), 400

        refrigerant = data.get('refrigerant', 'R410A')
        P1_kPa = float(data.get('P1_kPa'))
        T1_C = float(data.get('T1_C'))
        P2_kPa = float(data.get('P2_kPa'))
        T2_C = float(data.get('T2_C'))
        subcooling_C = float(data.get('subcooling_C', 5.0))

        result = analyze_refrigeration_cycle(refrigerant, P1_kPa, T1_C, P2_kPa, T2_C, subcooling_C)

        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400

        return jsonify({"status": "success", "data": result})

    except Exception as e:
        return jsonify({"status": "error", "message": f"参数解析错误: {str(e)}"}), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
