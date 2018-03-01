APP_REPO ?= ../marketplace-k8s-app-example
APP_NAME ?= wordpress

AGENT_REPO ?= ../ubbagent

APP_INSTANCE_NAME ?= $(APP_NAME)-1
NAMESPACE ?= default

$(shell mkdir -p .build/)

install-crd:
	$(MAKE) -C "crd/" "$@"

remove-crd:
	$(MAKE) -C "crd/" "$@"

build/kubectl:
	curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.9.0/bin/linux/amd64/kubectl
	chmod 755 kubectl
	mkdir -p build/
	mv kubectl build/

.build/marketplace-deployer_kubectl_base: build/kubectl marketplace/deployer_kubectl_base/*
	docker build \
	    --tag "$(REGISTRY)/marketplace/deployer_kubectl_base" \
	    -f marketplace/deployer_kubectl_base/Dockerfile \
	    .
	gcloud docker -- push "$(REGISTRY)/marketplace/deployer_kubectl_base"
	touch "$@"

.build/marketplace-controller: build/kubectl marketplace/controller/*
	docker build \
	    --tag "$(REGISTRY)/marketplace/controller" \
	    -f marketplace/controller/Dockerfile \
	    .
	gcloud docker -- push "$(REGISTRY)/marketplace/controller"
	touch "$@"

.build/marketplace-ubbagent:
	cd "$(AGENT_REPO)"; \
	docker build \
	    --tag "$(REGISTRY)/marketplace/ubbagent" \
	    .
	gcloud docker -- push "$(REGISTRY)/marketplace/ubbagent"
	touch "$@"

build/app: .build/marketplace-deployer_kubectl_base .build/marketplace-controller .build/marketplace-ubbagent
	$(MAKE) -C "$(APP_REPO)" "build/$(APP_NAME)"

up: build/app .build/marketplace-deployer_kubectl_base .build/marketplace-controller check-env
	scripts/start.sh \
	    --app-name=$(APP_NAME) \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE) \
	    --registry=$(REGISTRY)

down: check-env
	scripts/stop.sh \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE)

down-delete-events: check-env
	# Note: We don't do this in down because we intend for Kubernetes
	# has its own garbage collection mechanism. We clean them up
	# here to only to improve the development experience.
	kubectl delete events \
	    --namespace="$(NAMESPACE)" \
	    --selector="app=$(APP_INSTANCE_NAME)"

reload: down down-delete-events up

watch: check-env
	scripts/watch.sh \
	    --name=$(APP_INSTANCE_NAME) \
	    --namespace=$(NAMESPACE)

clean:
	rm -rf .build/ build/
	$(MAKE) -C "$(APP_REPO)" "clean/$(APP_NAME)"

check-env:
ifndef REGISTRY
  $(error REGISTRY is undefined. See README.md)
endif
ifndef APP_REPO
  $(error APP_REPO is undefined. See README.md)
endif
ifndef APP_NAME
  $(error APP_NAME is undefined. See README.md)
endif
ifndef APP_INSTANCE_NAME
  $(error APP_INSTANCE_NAME is undefined. See README.md)
endif
ifndef NAMESPACE
  $(error NAMESPACE is undefined. See README.md)
endif
