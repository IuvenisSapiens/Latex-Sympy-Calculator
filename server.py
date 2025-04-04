from flask import Flask, request, jsonify
from re import findall, split, MULTILINE
from re import match as re_match
from re import search as re_search
from sympy import *
from sympy.abc import *
from latex2sympy2_extended import latex2latex, latex2sympy
from latex2sympy2_extended.latex2sympy2 import _Latex2Sympy, ConversionConfig
app = Flask(__name__)

# 初始化全局变量
converter = _Latex2Sympy(is_real=False, convert_degrees=False)

def solve_equations(latex_str, formatter='sympy'):
    # 查找是否有 cases 或 dcases 环境的方程组
    regex_cases_dcases = r"\\begin{(cases|dcases)}([\s\S]*)\\end{\1}"
    matches_cases_dcases = findall(regex_cases_dcases, latex_str, MULTILINE)
    equations = []
    if matches_cases_dcases:
        matches_cases_dcases = split(r"\\\\(?:\[?.*?\])?", matches_cases_dcases[0][1])
        for match in matches_cases_dcases:
            ins = latex2sympy(match, conversion_config=ConversionConfig(lowercase_symbols=False))
            if isinstance(ins, list):
                equations.extend(ins)
            else:
                equations.append(ins)
    else:
        # 如果没有 cases 或 dcases 环境，则尝试直接解析单行方程
        try:
            # 使用 parse_latex 解析 LaTeX 字符串
            equation = latex2sympy(latex_str, conversion_config=ConversionConfig(lowercase_symbols=False))
            equations = [equation]
        except Exception as e:
            # 如果解析失败，返回 False
            return False
    
    # 求解方程或方程组
    solved = solve(equations)
    
    # 根据 formatter 参数决定返回格式
    if formatter == 'latex':
        return latex(solved)
    else:
        return solved

@app.route('/')
def main():
    return 'Latex Sympy Calculator Server'

@app.route('/solve-equations', methods=['POST'])
def solve_equations_api():
    try:
        latex_str = request.json['data']
        formatter = 'latex'
        solved = solve_equations(latex_str, formatter)
        return jsonify({
            'data': solved,
            'error': '',            
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        }) 

@app.route('/set-var', methods=['POST'])
def set_var():
    try:
        # 假设data的格式是 'key = value' 或 'key == value'
        data = request.json['data']
        print(data)
        # 使用正则表达式来分割key和value
        match = re_match(r'^(.*?)\s*(:=|==|=|\\in)\s*(.*)$', data)
        if match:
            key = match.group(1)
            print(key)
            operator = match.group(2)
            print(operator)
            value = match.group(3)
            print(value)
        else:
            raise ValueError("数据格式不正确，应包含 ':=', '==', '=', '\\in' 符号。")

        key = key.strip()
        value = value.strip()


        if operator == '\\in':
            try:
                # 这里假设value是形如 \mathbb{R}^{m \times n} 或 \mathbb{R}^{n \times m} 的格式，需要进一步解析
                dimensions = re_search(r'\^{(.*?)}', value).group(1)
                dimensions = dimensions.replace('\\times', '*').split('*')
                dimensions = [item.strip() for item in dimensions]
                # 检查维度是否为有效的数字或变量
                if dimensions[0].isdigit() and dimensions[1].isdigit():
                    # 创建矩阵符号
                    X = MatrixSymbol(f'{key}', int(dimensions[0]), int(dimensions[1]))
                elif dimensions[0].isidentifier() and dimensions[1].isidentifier():
                    # 如果是矩阵的变量维度，保持字符串形式
                    X = MatrixSymbol(f'{key}', Symbol(dimensions[0]), Symbol(dimensions[1]))
                else:
                    raise ValueError("应为形如 \\mathbb{R}^{m \\times n} 的格式，且m和n应为数字或变量标识符")
            except Exception as e:
                raise ValueError("数据格式："+str(value)+"不正确，应为形如 \\mathbb{R}^{m \\times n} 或 \\mathbb{R}^{n \\times m} 的格式。\n"+str(e))

        else:
            # 对于其他操作符，直接使用 latex2sympy 进行解析
            X = str(latex2sympy(value, conversion_config=ConversionConfig(lowercase_symbols=False)))

        # 将处理后的键值对添加到converter.var字典中
        converter.var[str(latex2sympy(key, conversion_config=ConversionConfig(lowercase_symbols=False)))] = X

        print(converter.var)
        return jsonify({
            'data': '',
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })


@app.route('/latex', methods=['POST'])
def get_latex():
    try:
        parsed_math = latex2latex(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
        return jsonify({
            'data': parsed_math,
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })

@app.route('/matrix-raw-echelon-form', methods=['POST'])
def get_matrix_raw_echelon_form():
    try:
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
        return jsonify({
            'data': latex(parsed_math.subs(converter.var).rref()[0]).replace(r'\left[\begin{matrix}', r'\begin{pmatrix}', -1).replace(r'\end{matrix}\right]', r'\end{pmatrix}', -1),
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })

@app.route('/numerical', methods=['POST'])
def get_numerical():
    try:
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
        return jsonify({
            'data': latex(simplify(parsed_math.subs(converter.var).doit().doit()).evalf(subs=converter.variances)),
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })

@app.route('/factor', methods=['POST'])
def get_factor():
    try:
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
        return jsonify({
            'data': latex(factor(parsed_math.subs(converter.var))),
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })

@app.route('/expand', methods=['POST'])
def get_expand():
    try:
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
        return jsonify({
            'data': latex(expand(apart(expand_trig(parsed_math.subs(converter.var))))),
            'error': ''
        })
    except Exception as _:
        try:
            parsed_math = latex2sympy(request.json['data'], variable_values=converter.var, conversion_config=ConversionConfig(lowercase_symbols=False))
            return jsonify({
                'data': latex(expand(expand_trig(parsed_math.subs(converter.var)))),
                'error': ''
            })
        except Exception as e:
            return jsonify({
                'data': '',
                'error': str(e)
            })

@app.route('/variances', methods=['GET'])
def get_variances():
    result = {str(key): str(value) for key, value in converter.var.items()}
    print(converter.var)
    return jsonify(result)



@app.route('/reset', methods=['GET'])
def reset():
    converter.var = {}
    return jsonify({
        'success': True
    })

@app.route('/complex', methods=['GET'])
def complex():
    converter.is_real = not converter.is_real
    return jsonify({
        'success': True,
        'value': converter.is_real
    })

@app.route('/python', methods=['POST'])
def run_python():
    try:
        rv = eval(request.json['data'])
        return jsonify({
            'data': str(rv),
            'error': ''
        })
    except Exception as e:
        return jsonify({
            'data': '',
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=7395)
