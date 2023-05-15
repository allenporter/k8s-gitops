"""Ansible action plugin for fetchign gcp secrets."""

from google.cloud import secretmanager
from ansible.plugins.action import ActionBase

ARG_SPEC = {
    'project': {'type': 'raw'},
    'secret': {'type': 'raw'},
    'version': {'type': 'raw'}
}

class ActionModule(ActionBase):
    """An ansible module for reading GCP Secret Manager secrets."""

    def run(self, tmp=None, task_vars=None):
        """Run the action plugin."""
        task_vars = task_vars or {}
        validation_result, new_module_args = self.validate_argument_spec(
            argument_spec=ARG_SPEC,
        )
        result = super(ActionModule, self).run(tmp, task_vars)

        project_id = new_module_args['project']
        secret_id = new_module_args['secret']
        version_id = new_module_args['version']
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

        client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(request={"name": name})

        result['secret'] = response.payload.data.decode("UTF-8")
        result['failed'] = False

        return result