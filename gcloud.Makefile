ifndef __GCLOUD_MAKEFILE__

__GCLOUD_MAKEFILE__ := included


ifndef REGISTRY
  REGISTRY := gcr.io/$(shell gcloud config get-value project)
endif

ifndef NAMESPACE
  NAMESPACE := $(shell kubectl config view -o jsonpath="{.contexts[?(@.name==\"$$(kubectl config current-context)\")].context.namespace}")
  ifeq ($(NAMESPACE),)
    NAMESPACE = default
  endif
endif

$(info ---- REGISTRY = $(REGISTRY))
$(info ---- NAMESPACE = $(NAMESPACE))


endif
