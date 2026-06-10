"""HTTP-маршруты приложения."""

from flask import jsonify
from services import CalculatorInterface


def register_routes(app, calculator: CalculatorInterface):
    """Регистрация маршрутов с внедрением зависимости."""

    @app.route('/')
    def index():
        return jsonify({
            'message': 'SOLID Flask app in Docker',
            'endpoints': [
                '/health',
                '/info',
                '/calc/<operation>/<a>/<b>'
            ]
        })

    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200

    @app.route('/info')
    def info():
        return jsonify({
            'app': 'Flask SOLID Demo',
            'version': '1.0.0',
            'principles': ['S', 'O', 'L', 'I', 'D']
        })

    @app.route('/calc/<operation>/<a>/<b>')
    def calc(operation, a, b):
        try:
            a_val = float(a)
            b_val = float(b)
            result = calculator.calculate(a_val, b_val, operation)
            return jsonify({
                'operation': operation,
                'a': a_val,
                'b': b_val,
                'result': result
            }), 200
        except ValueError:
            return jsonify({'error': 'Invalid numbers, please provide numeric values'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 400