import io
import sys
import pandas as pd
import matplotlib.pyplot as plt
import traceback

def execute_code(code, df):
    """
    Executes the given code with access to the DataFrame `df` and matplotlib.pyplot as `plt`.
    Returns: (output_text, result_var, chart_generated, error)
    """
    local_vars = {"df": df, "plt": plt}
    stdout = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = stdout
    error = None
    chart_generated = False
    result_var = None

    try:
        exec(code, {}, local_vars)
        if "chart.png" in code:
            chart_generated = True
        if "result" in local_vars:
            result_var = local_vars["result"]
    except Exception as e:
        error = traceback.format_exc()
    finally:
        sys.stdout = sys_stdout

    output_text = stdout.getvalue()
    return output_text, result_var, chart_generated, error 