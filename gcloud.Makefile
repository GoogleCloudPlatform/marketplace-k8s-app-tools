ifndef __GCLOUD_MAKEFILE__

__GCLOUD_MAKEFILE__ := included

# Include this Makefile to automatically derive registry
# and target namespace from the current gcloud and kubectl
# configurations.
# This is for convenience over having to specifying the
# environment variables manually.


ifndef REGISTRY
  # We replace ':' with '/' characters to support a now-deprecated
  # projects format "google.com:my-project".
  REGISTRY := gcr.io/$(shell gcloud config get-value project | tr ':' '/')
endif

ifndef NAMESPACE
  NAMESPACE := $(shell kubectl config view -o jsonpath="{.contexts[?(@.name==\"$$(kubectl config current-context)\")].context.namespace}")
  ifeq ($(NAMESPACE),)
    NAMESPACE = default
  endif
endif

$(info ---- REGISTRY = $(REGISTRY))
$(info ---- NAMESPACE = $(NAMESPACE))


# Using this target to trigger rebuilding when REGISTRY changes.
.PHONY: gcloud/REGISTRY .build/REGISTRY_phony
gcloud/REGISTRY: .build/REGISTRY
.build/REGISTRY: .build/REGISTRY_phony
.build/REGISTRY_phony: | .build
ifneq ($(shell [ -e ".build/REGISTRY" ] && cat ".build/REGISTRY" || echo ""),$(REGISTRY))
	$(info REGISTRY changed to $(REGISTRY))
	@echo "$(REGISTRY)" > ".build/REGISTRY"
endif

# Using this target to trigger rebuilding when TAG changes.
.PHONY: gcloud/TAG .build/TAG_phony
gcloud/TAG: .build/TAG
.build/TAG: .build/TAG_phony
.build/TAG_phony: | .build
ifneq ($(shell [ -e ".build/TAG" ] && cat ".build/TAG" || echo ""),$(TAG))
	$(info TAG changed to $(TAG))
	@echo "$(TAG)" > ".build/TAG"
endif


endif
