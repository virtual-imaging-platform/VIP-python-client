# VIP-python-client

This module is used to communicate with the VIP api using the Python
language.
This a synchronous implementation.

## How to use it

This module works like a state-machine : first, set the apikey with
setApiKey(str). All the functions will refer to this apikey later.

You can also set the certificate for vip with setCertifPath(str). By default,
the script will look at its location for a '[...]/certif.crt' file.
You should already have a certificate when cloning this project from git. If
it's not the case you can get it with your browser [on VIP](http://vip.creatis.insa-lyon.fr/). Get the chained one.

You can now use all of the functions :)

## Raised errors

If there's any VIP issues, functions will raise *RuntimeError* errors. See
'detect\_errors' and 'manage\_errors' functions if you want to change this.

## Improvement

- an asynchronous version
- missing a few optional parameters for some function (not important)
