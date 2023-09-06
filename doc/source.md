# Classes and Methods of the Python client

`vip_client` currently contains 5 classes in `vip_client.classes` and 1 module in `vip_client.utils`.

## Classes

### [vip_client.classes.**VipSession**](../src/vip_client/classes/VipSession.py)

The most user-friendly class to interact with VIP. See the documentation [here](VipSession.md).

### [vip_client.classes.**VipLauncher**](../src/vip_client/classes/VipLauncher.py)

A parent class of `VipSession` that implements everything needed to launch VIP applications on remote data sets. *More information to come*.

### [vip_client.classes.**VipCI**](../src/vip_client/classes/VipCI.py)

[Prototype] A `VipLauncher` implementation to launch VIP application on [Girder](https://girder.readthedocs.io/en/latest/) datasets. Currently used for continuous integration (CI) tests on the VIP platform.

### [vip_client.classes.**VipLoader**](../src/vip_client/classes/VipLoader.py)

[Work in progress] A class that implements everything needed to upload/download data to/from VIP servers. *More information to come*.

### [vip_client.classes.**VipClient**](../src/vip_client/classes/VipClient.py)

[Work in progress] Base class to communicate with VIP. *More information to come*.

## Modules

### [vip_client.utils.**vip**](../src/vip_client/utils/vip.py)

This package implements synchronous requests to the [VIP (RESTful) API](https://github.com/virtual-imaging-platform/VIP-portal/tree/master/vip-api) (through the [`requests`](https://pypi.org/project/requests/) Python library).

- *How to use it*: This module works like a state machine: first, set the `apikey` with
`setApiKey(str)`. All the functions will refer to this `apikey` later.
- *Raised errors*: If there are any VIP issues, functions will raise *RuntimeError* errors. See
`detect_errors` and `manage_errors` functions if you want to change this.
- *Future Work*: An asynchronous version
