class MathTool:

    name = "math"

    def execute(self, input_data):
        try:
            return eval(input_data)
        except Exception as e:
            return str(e)