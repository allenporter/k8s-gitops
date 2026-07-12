# Execution Checklist: In-Cluster Devcontainer Builder and Caching Verification (Complete)

- `[x]` Define a new workspace for `home-assistant-journal-assistant`
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/journal-assistant/pvc.yaml`
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/journal-assistant/service.yaml`
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/journal-assistant/pod.yaml` using prebuilt image
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/journal-assistant/kustomization.yaml`
  - `[x]` Register the new workspace in `kubernetes/devcontainers/prod/kustomization.yaml`

- `[x]` Create build Job manifests in workspace folders using inline caching:
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/ring-keypad/builder-job.yaml`
  - `[x]` Create `kubernetes/devcontainers/prod/workspaces/journal-assistant/builder-job.yaml`

- `[x]` Update existing `ring-keypad` workspace:
  - `[x]` Modify `kubernetes/devcontainers/prod/workspaces/ring-keypad/pod.yaml` to use the prebuilt image and remove complex dependencies installations

- `[x]` Execute the validation steps in the cluster:
  - `[x]` Run the `ring-keypad` builder Job (warm up shared registry cache)
  - `[x]` Run the `journal-assistant` builder Job (verify cache hits)
  - `[x]` Verify both workspace pods deploy successfully using the compiled images
