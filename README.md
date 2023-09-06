[vip-portal]: https://vip.creatis.insa-lyon.fr/ "https://vip.creatis.insa-lyon.fr/"

<img src="https://vip.creatis.insa-lyon.fr/images/core/vip-logo.png" alt="VIP-logo" height="100" title="Virtual Imaging Platform"/> 

Python client for the [Virtual Imaging Platform][vip-portal] (**VIP**), a free online platform for medical image simulation and analysis. 

Now available on [Pypi](https://pypi.org/project/vip-client/):
```bash
pip install vip-client
```
If you encounter any issues, please contact us at: <vip-support@creatis.insa-lyon.fr>

- [Prerequisites](#prerequisites)
- [Content](#content)
- [VipSession](#vipsession)
- [Examples](#examples)
- [Release Notes](#release-notes)

---

# Prerequisites

1. This client has been made compatible with **Python 3.7+** and should work on Posix OS (*e.g.* **Linux**, **Mac**) and **Windows**. It relies on the [`requests`](https://pypi.org/project/requests/) (third-party) Python library.

2. To use this client, you need a free **VIP account** with a valid **API key**. Getting a VIP account takes a few minutes following this [procedure](doc/account.md).

# Content

- The `VipSession` class (see [below](#vipsession)) can be used to launch VIP executions on local datasets. 

- Other classes (`vip_client.classes`) and methods (`vip_client.utils`) are mostly used by the VIP team and may also fulfill specific user needs. See the doc [here](doc/source.md) or contact [vip-support](<vip-support@creatis.insa-lyon.fr>) for more information.

# VipSession

```python
from vip_client import VipSession
```

The `VipSession` class launches executions on [VIP][vip-portal] from any machine where the dataset is stored (*e.g.*, one's server or PC). 

[See the dedicated documentation page](doc/vipsession.md).

The basic steps can also be learnt through a dedicated [tutorial](examples/tutorials/demo-vipsession.ipynb) available on Binder:

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/virtual-imaging-platform/VIP-python-client/HEAD?labpath=examples%2Ftutorials%2Fdemo-vipsession.ipynb)

# Examples

Application examples can be found [in this repository](examples), including tutorials and workshop materials.

# Release Notes

The release history is available [here](doc/history.md).

---