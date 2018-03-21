ifndef __CRD_MAKEFILE__

__CRD_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile

.PHONY: crd/install
crd/install: | common/setup
	kubectl apply -f "$(MARKETPLACE_TOOLS_PATH)/crd/application-resource-definition.yaml"

.PHONY: crd/remove
crd/remove: | common/setup
	kubectl delete "crd/applications.marketplace.cloud.google.com"

.PHONY: crd/delete
crd/delete: crd/remove ;


endif
