ifndef __GCLOUD_MAKEFILE__

__GCLOUD_MAKEFILE__ := included

# Include this Makefile to set environment context variables to sane
# defaults based on the current working context.

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

ifndef PROJECT
  PROJECT := $(shell kubectl config current-context | sed 's/gke_//' | sed 's/_.*//')
endif

ifndef CLUSTER
  CLUSTER := $(shell kubectl config current-context | sed 's/gke_//' | sed 's/.*_//')
endif

ifndef ZONE
  ZONE := $(shell kubectl config current-context | sed 's/gke_//' | sed 's/[^_]*_//' | sed 's/_.*//')
endif

$(info ---- REGISTRY = $(REGISTRY))
$(info ---- NAMESPACE = $(NAMESPACE))
$(info ---- PROJECT = $(PROJECT))
$(info ---- CLUSTER = $(CLUSTER))
$(info ---- ZONE = $(ZONE))

endif
