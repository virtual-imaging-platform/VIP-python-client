import sys
from pathlib import Path
SOURCE_ROOT = str(Path(__file__).parents[1] / "src") # <=> /src/
sys.path.append(SOURCE_ROOT)
import vip_client

from vip_client.classes import VipLoader
from pathlib import *

VipLoader.init()
path = "/vip/EGI tutorial (group)/outputs"
print(f"Under '{path}':")
print("\n".join(VipLoader.list_dir(path)))
print()
VipLoader.download_dir(
    vip_path=path, 
    local_path=Path("Here")
)