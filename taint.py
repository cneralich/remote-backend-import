import os
from terrasnek.api import TFC
import urllib.request
import hashlib
import base64
import json
import subprocess

TFE_TOKEN = os.getenv("TFE_TOKEN", None)
TFE_URL = os.getenv("TFE_URL", None)
TFE_ORG = os.getenv("TFE_ORG", None)

api_new = TFC(TFE_TOKEN, url=TFE_URL)
api_new.set_org(TFE_ORG)


# Method for tainting resources when workspace_id is passed
def taint_state_ws_id(workspace_id, taint_list):
    current_version = api_new.state_versions.get_current(workspace_id)[
        'data']
    
    state_url = current_version['attributes']['hosted-state-download-url']
    pull_state = urllib.request.urlretrieve(state_url, 'terraform.tfstate')

    for resource in taint_list:
        subprocess.call(["terraform", "taint", "%s" % (resource)]) 

    state_file = open("terraform.tfstate", "r")
    state_data = state_file.read()
    state_encoded = state_data.encode("utf8")
    state_serial = json.loads(state_data)['serial']
    state_lineage = json.loads(state_data)['lineage']

    state_hash = hashlib.md5()
    state_hash.update(state_encoded)
    state_md5 = state_hash.hexdigest()
    state_b64 = base64.b64encode(state_encoded).decode("utf-8")

    # Build the new state payload
    create_state_version_payload = {
        "data": {
            "type": "state-versions",
            "attributes": {
                "serial": state_serial,
                "lineage": state_lineage,
                "md5": state_md5,
                "state": state_b64
            }
        }
    }

    # Migrate state to the new Workspace
    api_new.workspaces.lock(workspace_id, {
                            "reason": "taint script"})
    api_new.state_versions.create(
        workspace_id, create_state_version_payload)
    api_new.workspaces.unlock(workspace_id)

    os.remove('terraform.tfstate')
    os.remove('terraform.tfstate.backup')

    return


# Method for tainting resources when workspace_name is passed
def taint_state_ws_name(workspace_name, taint_list):
    workspace_id = api_new.workspaces.show(workspace_name=workspace_name)['data']['id']
    
    current_version = api_new.state_versions.get_current(workspace_id)[
        'data']
    
    state_url = current_version['attributes']['hosted-state-download-url']
    pull_state = urllib.request.urlretrieve(state_url, 'terraform.tfstate')

    for resource in taint_list:
        subprocess.call(["terraform", "taint", "%s" % (resource)]) 

    state_file = open("terraform.tfstate", "r")
    state_data = state_file.read()
    state_encoded = state_data.encode("utf8")
    state_serial = json.loads(state_data)['serial']
    state_lineage = json.loads(state_data)['lineage']

    state_hash = hashlib.md5()
    state_hash.update(state_encoded)
    state_md5 = state_hash.hexdigest()
    state_b64 = base64.b64encode(state_encoded).decode("utf-8")

    # Build the new state payload
    create_state_version_payload = {
        "data": {
            "type": "state-versions",
            "attributes": {
                "serial": state_serial,
                "lineage": state_lineage,
                "md5": state_md5,
                "state": state_b64
            }
        }
    }

    # Migrate state to the new Workspace
    api_new.workspaces.lock(workspace_id, {
                            "reason": "taint script"})
    api_new.state_versions.create(
        workspace_id, create_state_version_payload)
    api_new.workspaces.unlock(workspace_id)

    os.remove('terraform.tfstate')
    os.remove('terraform.tfstate.backup')

    return