
<img src="https://vip.creatis.insa-lyon.fr/images/core/vip-logo.png" alt="VIP-logo" height="150" title="Virtual Imaging Platform"/> 

Python client for the [Virtual Imaging Platform]("https://vip.creatis.insa-lyon.fr/") (**VIP**), a free online platform for medical image simulation and analysis.

See the full documentation on [GitHub](https://github.com/virtual-imaging-platform/VIP-python-client) for detailed information.
If you encounter any issues, please contact us at: <vip-support@creatis.insa-lyon.fr>

# Package Content

[vipsession-tutorial]: #examples/tutorials/demo-vipsession.ipynb "VipSession Tutorial"

Several modules can be used to interact with VIP. 
- Most useful methods are implemented in the Python class `VipSession`.
- Classes `VipLauncher` and `VipCI` are mostly used by the VIP team for current projects.
- Module `utils.vip` can be used for advanced requests.

The `VipSession` class ([doc](https://github.com/virtual-imaging-platform/VIP-python-client#vipsession)) is recommended to run simulations or massive analyses on local datasets.
```python
from vip_client import VipSession
```
It also comes with a tutorial [Notebook][vipsession-tutorial] that can be used in this Binder instance:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/virtual-imaging-platform/VIP-python-client/HEAD?labpath=examples%2Ftutorials%2Fdemo-vipsession.ipynb)

# Prerequisites

This client has been made compatible with **Python 3.7+** and should work on both Posix (**Linux**, **Mac**) and **Windows** OS. It requires minimal preparation from the user:

1. A **VIP account** with a valid *API key*. This takes a few minutes by following this [procedure](https://github.com/virtual-imaging-platform/VIP-python-client#manage-your-vip-account).

2. The [`requests`](https://pypi.org/project/requests/) Python library.
```bash
pip install requests
```