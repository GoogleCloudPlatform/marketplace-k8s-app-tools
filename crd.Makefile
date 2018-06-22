ifndef __CRD_MAKEFILE__

__CRD_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile

# Installs the application CRD on the cluster.
.PHONY: crd/install
crd/install:
	kubectl apply -f "$(MARKETPLACE_TOOLS_PATH)/crd/app-crd.yaml"

# Uninstalls the application CRD from the cluster.
.PHONY: crd/uninstall
crd/uninstall:
	kubectl delete -f "$(MARKETPLACE_TOOLS_PATH)/crd/app-crd.yaml"


endif
