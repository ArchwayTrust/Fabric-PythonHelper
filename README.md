# Fabric-PythonHelper
Collection of useful python code for automation in Microsoft Fabric.
Documentation to follow!

## PBI Admin
In Fabric notebook run:
```
from fabric_python_helper import pbi_admin as pbi
```


### Access Tokens
Can be initiated directly:
```
access_token = pbi.AccessTokens().get_token_as_fabric_notebook_owner()
```

### Dataflows

```
access_token = pbi.AccessTokens().get_token_as_fabric_notebook_owner()
workspace_id = "7509f..."
dataflow_id = "46aed9..."

dataflow = pbi.Dataflows(workspace_id, dataflow_id, access_token)
dataflow.refresh_dataflow(expected_duration=60, loop_interval=20, wait_for_completion=True)
```


### Semantic Models
```
access_token = pbi.AccessTokens().get_token_as_fabric_notebook_owner()
semantic_model_id = "d0c24..."

semantic_model = pbi.SemanticModels(semantic_model_id, access_token)
semantic_model.refresh_semantic_model(expected_duration=60, loop_interval=20, wait_for_completion=True)
```


## GraphAPI
Requires an app registration with delegated User.Read, Mail.ReadWrite, offline_access and public client flow enabled.
Requires an azure key vault with an pre initiated secret (correct value will be written in).

In Fabric notebook run:
```
from fabric_python_helper import graph_api as gr
```
### Emails

```
tennant_id = "23...."
client_id = "00df..."
akv_url = "https://name.vault.azure.net/"
refresh_secret_name = "Secret Name"

email_account = gr.Emails(tennant_id, client_id, akv_url, refresh_secret_name)

```
#### Initial Authentication

On first run you will need to authenticate, this is using device flow authentication:

```
email_account.get_initial_tokens()
```

It will give you a link and device code which you need to follow and authenticate with.

#### Find the message id (currently returns first email only)
```
message_id = email_account.search_message_by_subject_and_sender("Attachment Test", "email@address.com")
```

#### Get list of attachment ids:
```
attachments = email_account.get_attachment_ids_and_names(message_id)
```

#### Get attachments:
(You can loop through the list of attachments if required)
```
attachment = email_account.download_attachment(message_id = message_id, attachment_id = attachments[0][0], is_binary=True, encoding="utf-8")
```

#### Save to onelake:
Assuming it's a text file eg you're here because you're grabbing a csv from an email you can just use 

```
mssparkutils.fs.put(file_path, attachment, overwrite=True)
```
If you returned a binary other methods would be required.

#### Delete the email:

```
email_account.delete_email(message_id)
```

#### Send an email

```
email_addresses = ["email1@address.co.uk", "email2@address.co.uk"]

subject = "Test Email"

content = """
Hi,
I'm the content of the email.
I'm on my own line.

    From Ben               
"""

email_account.send_email(subject, content, email_addresses)
```

## Building a Wheel File
In order to build I had to add to create a pip.ini file in `C:\ProgramData\pip\`
<br>
Which contained:
```
[global]
trusted-host = files.pythonhosted.org
               pypi.org
```
You can then build with:
- `pip install build`
- `python -m build`