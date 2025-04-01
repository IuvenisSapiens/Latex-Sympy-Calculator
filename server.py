from flask import Flask, request, jsonify
from sympy import apart, expand, expand_trig, factor, latex, simplify
from latex2sympy2_extended import latex2latex, latex2sympy
from latex2sympy2_extended.latex2sympy2 import _Latex2Sympy
app = Flask(__name__)

# 初始化全局变量
converter = _Latex2Sympy(is_real=False, convert_degrees=False)

@app.route('/')
def main():
    return 'Latex Sympy Calculator Server'


@app.route('/latex', methods=['POST'])
def get_latex():
    try:
        parsed_math = latex2latex(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
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
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
        return jsonify({
            'data': latex(parsed_math.subs(converter.variances).rref()[0]).replace(r'\left[\begin{matrix}', r'\begin{pmatrix}', -1).replace(r'\end{matrix}\right]', r'\end{pmatrix}', -1),
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
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
        return jsonify({
            'data': latex(simplify(parsed_math.subs(converter.variances).doit().doit()).evalf(subs=converter.variances)),
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
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
        return jsonify({
            'data': latex(factor(parsed_math.subs(converter.variances))),
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
        parsed_math = latex2sympy(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
        return jsonify({
            'data': latex(expand(apart(expand_trig(parsed_math.subs(converter.variances))))),
            'error': ''
        })
    except Exception as _:
        try:
            parsed_math = latex2sympy(request.json['data'], variable_values=converter.variances, is_real=converter.is_real, convert_degrees=converter.convert_degrees)
            return jsonify({
                'data': latex(expand(expand_trig(parsed_math.subs(converter.variances)))),
                'error': ''
            })
        except Exception as e:
            return jsonify({
                'data': '',
                'error': str(e)
            })

@app.route('/variances', methods=['GET'])
def get_variances():
    result = {str(key): str(value) for key, value in converter.variances.items()}
    return jsonify(result)

@app.route('/reset', methods=['GET'])
def reset():
    converter.variances = {}
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
