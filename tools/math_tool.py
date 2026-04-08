def execute_math(expression: str):
    try:
        return eval(expression)
    except Exception as e:
        return str(e)