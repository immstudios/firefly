Firefly
=======

Firefly is a desktop client application for **Nebula** broadcast automation system.

Configuration
-------------

Edit **settings.json** file to set your server address and site name.

```json
{
    "sites"  : [{
        "site_name" : "demo",
        "hub" : "https://demo.nebulabroadcast.com"
    }]
}
```


Installation
------------

For Linux, install python3 and python3-pip packages and then install requiered libraries using
following command

```
sudo pip install requests PyQT5 websockets-client
```

For video playback, you will also need **libmpv1** package.

