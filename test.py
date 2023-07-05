import textwrap
import os
from src.VipLauncher import VipLauncher

wrapper = textwrap.TextWrapper(
    width = 70,
    initial_indent = '    ',
    subsequent_indent = '    ',
    max_lines = 10,
    drop_whitespace=False,
    replace_whitespace = False,
    break_on_hyphens = False,
    break_long_words = False
)

text = """
    Parses the input settings, i.e.:
        - Converts all input paths (local or VIP) to PathLib objects 
            and write them relatively to their input directory. For example:
            '/vip/Home/API/INPUTS/my_signals/signal001' becomes: 'my_signals/signal001'
        - Leaves the other parameters untouched.\n
"""
# Setup
f1, f2 = "test_1.txt", "test_2.txt"
# Write
with open(f1, "w") as t1, open(f2, "w") as t2:
    print(wrapper.fill(text), end="", file=t1) # oracle
    VipLauncher._printc(text, end="", wrapper=wrapper, file=t2) # test 
# Read 
with open(f1, "r") as t1, open(f2, "r") as t2:   
    assert t1.read() == t2.read()
# End
os.remove(f1)
os.remove(f2)

VipLauncher.init()
VipLauncher.show_pipeline("FreeSurfer-Recon-all/v7.3.1")
# VipLauncher.show_pipeline("SimuBloch/0.5")