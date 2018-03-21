ifndef __GCLOUD_MAKEFILE__

__GCLOUD_MAKEFILE__ := included

REGISTRY ?= gcr.io/$(shell gcloud config get-value project)
NAMESPACE ?= $(shell kubectl config view -o jsonpath="{.contexts[?(@.name==\"$(kubectl config current-context)\")].context}")
ifeq ($(NAMESPACE),)
  NAMESPACE = default
endif

$(info ---- REGISTRY = $(REGISTRY))
$(info ---- NAMESPACE = $(NAMESPACE))


endif
