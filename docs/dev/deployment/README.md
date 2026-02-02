# Deployment docs

This repo is the **App repo**: it owns source code, Dockerfile, migrations schema, and environment variable schema. Deployment (k8s manifests, ConfigMap/Secret values, runbooks) lives in a separate **Deploy repo**. The only interface between them is the GHCR image tag.

See [k8s_architecture.md](k8s_architecture.md), [k8s_app_architecture.md](k8s_app_architecture.md), and [k8s_sub_architecture.md](k8s_sub_architecture.md) for details.
