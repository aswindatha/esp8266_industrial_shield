import sys, json
sys.path.insert(0, r"C:\Users\aswin\Music\universal controller\ind_8ch_motor_ctrl\tools")
import mcp
mcp.init()

def call(tool, **kwargs):
    r = mcp.call(tool, kwargs if kwargs else {})
    return r

def show(tool, **kwargs):
    print("### " + tool)
    print(call(tool, **kwargs))
    print()
