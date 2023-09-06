<img src="https://vip.creatis.insa-lyon.fr/images/core/vip-logo.png" alt="VIP-logo" height="100" title="Virtual Imaging Platform"/> 

Python client for the [Virtual Imaging Platform]("https://vip.creatis.insa-lyon.fr/") (**VIP**), a free online platform for medical image simulation and analysis.

Please check the full documentation on [GitHub](https://github.com/virtual-imaging-platform/VIP-python-client).
If you encounter any issues, contact us at: <vip-support@creatis.insa-lyon.fr>

# Prerequisites

- This client has been made compatible with **Python 3.7+** and should work on Posix OS (*e.g.* **Linux**, **Mac**) and **Windows**. It relies on the [`requests`](https://pypi.org/project/requests/) (third-party) library.

- To use this client, you need a free **VIP account** with a valid API key. Getting a VIP account takes a few minutes by following this [procedure](https://github.com/virtual-imaging-platform/VIP-python-client#manage-your-vip-account).

# Package Content

- Most user-centric methods are implemented in the `VipSession` class. 
- Other classes (`vip_client.classes`) and methods (`vip_client.utils`) may be used to fulfill specific user needs.

The `VipSession` class ([doc](https://github.com/virtual-imaging-platform/VIP-python-client#vipsession)) allows to run VIP applications on local datasets.
```python
from vip_client import VipSession
```
It comes with a Notebook [tutorial](https://github.com/virtual-imaging-platform/VIP-python-client/blob/develop/examples/tutorials/demo-vipsession.ipynb) that can be launched on Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/virtual-imaging-platform/VIP-python-client/HEAD?labpath=examples%2Ftutorials%2Fdemo-vipsession.ipynb)

---