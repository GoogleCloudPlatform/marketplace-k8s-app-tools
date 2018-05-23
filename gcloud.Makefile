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
gcloud/registry_prefix: .build/registry_prefix
.build/registry_prefix: .build/registry_prefix_phony
.PHONY: .build/registry_prefix_phony
.build/registry_prefix_phony: | .build
ifneq ($(shell [ -e ".build/registry_prefix" ] && cat ".build/registry_prefix" || echo ""),$(REGISTRY))
	$(info REGISTRY changed to $(REGISTRY))
	@echo "$(REGISTRY)" > ".build/registry_prefix"
endif

# Using this target to trigger rebuilding when TAG changes.
gcloud/tag_prefix: .build/tag_prefix
.build/tag_prefix: .build/tag_prefix_phony
.PHONY: .build/tag_prefix_phony
.build/tag_prefix_phony: | .build
ifneq ($(shell [ -e ".build/tag_prefix" ] && cat ".build/tag_prefix" || echo ""),$(TAG))
	$(info TAG changed to $(TAG))
	@echo "$(TAG)" > ".build/tag_prefix"
endif


endif
