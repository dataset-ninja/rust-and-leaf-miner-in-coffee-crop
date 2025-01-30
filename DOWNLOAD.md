Dataset **Rust and Leaf Miner in Coffee Crop** can be downloaded in [Supervisely format](https://developer.supervisely.com/api-references/supervisely-annotation-json-format):

 [Download](https://assets.supervisely.com/remote/eyJsaW5rIjogImZzOi8vYXNzZXRzLzIyNzFfUnVzdCBhbmQgTGVhZiBNaW5lciBpbiBDb2ZmZWUgQ3JvcC9ydXN0LWFuZC1sZWFmLW1pbmVyLWluLWNvZmZlZS1jcm9wLURhdGFzZXROaW5qYS50YXIiLCAic2lnIjogIldZWnR6Y3ZiY3NCeEZESkFXSXdUclRzZ045b0U1elRsb1A2LzA2ZnhRN1U9In0=)

As an alternative, it can be downloaded with *dataset-tools* package:
``` bash
pip install --upgrade dataset-tools
```

... using following python code:
``` python
import dataset_tools as dtools

dtools.download(dataset='Rust and Leaf Miner in Coffee Crop', dst_dir='~/dataset-ninja/')
```
Make sure not to overlook the [python code example](https://developer.supervisely.com/getting-started/python-sdk-tutorials/iterate-over-a-local-project) available on the Supervisely Developer Portal. It will give you a clear idea of how to effortlessly work with the downloaded dataset.

The data in original format can be [downloaded here](https://prod-dcd-datasets-cache-zipfiles.s3.eu-west-1.amazonaws.com/vfxf4trtcg-5.zip).