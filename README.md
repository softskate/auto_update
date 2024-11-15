## Getting started

* Clone from source (requires git):

```
git clone https://github.com/softskate/auto_update.git
```

* After cloning, move into the new directory with"

```
cd auto_update
```
* Set your projects folder in \__main__.py to `PROJECTS_DIR` variable
* Create `keys.py` and genrate token into `secret_token` variable
* Run `main.py` in background.

## Make ready your repository for auto update

### Add webhook

Open your repository and go to Settings > Webhooks > Add webhook.
Insert this into Payload URL 

```
http://{your_server_ip}:5000/webhook/pull/{your_project_folder_name}
```

Insert you `secret_token` into Secret field.
Set SSL verification as Disabled.
