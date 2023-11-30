# Fabric-PythonHelper
Collection of useful python code for automation in Microsoft Fabric.
Documentation to follow!

## PBI Admin
### PBIAdmin_GetAccessToken

### PBIAdmin_DataflowRefresher

### PBIAdmin_SemanticModelRefresher

## GraphAPI
### GraphAPI_Emails

## Building a Wheel File
In order to build I had to add to create a pip.ini file in `C:\ProgramData\pip\`
<br>
Which contained:
```
[global]
trusted-host = files.pythonhosted.org
```
You can then build with:
- `pip install build`
- `python -m build`