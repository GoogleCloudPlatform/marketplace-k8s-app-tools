ifndef __MARKETPLACE_MAKEFILE__

__MARKETPLACE_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile


.build/marketplace: | .build
	mkdir -p "$@"

.build/marketplace/dev: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                        $(MARKETPLACE_TOOLS_PATH)/marketplace/dev/* \
                        $(MARKETPLACE_TOOLS_PATH)/scripts/* \
                        $(MARKETPLACE_TOOLS_PATH)/marketplace.Makefile \
                        .build/var/SERVICE_ACCOUNT_JSON_FILE-optional \
                        | .build/marketplace
	$(call print_target)

	# Note: This approach is ugly and doesn't quite work - docker
	# build seems to be ignoring .build/ files. Probably better
	# to have an init that checks for files mounted in predictable
	# places.
	set -x ; \
	if [[ ! -z "$(SERVICE_ACCOUNT_JSON_FILE)" ]]; then \
	    mkdir -p "$(MARKETPLACE_TOOLS_PATH)/.build/marketplace" ; \
	    cp "$(realpath $(SERVICE_ACCOUNT_JSON_FILE))" "$(MARKETPLACE_TOOLS_PATH)/.build/marketplace/service_account.json" ; \
	    export SERVICE_ACCOUNT_JSON_FILE="$(MARKETPLACE_TOOLS_PATH)/.build/marketplace/service_account.json" ; \
	fi ; \
	cd "$(MARKETPLACE_TOOLS_PATH)" ; \
	if [[ -z "$(SERVICE_ACCOUNT_JSON_FILE)" ]]; then \
	    export SERVICE_ACCOUNT_JSON_FILE=.build/blank ; \
	    touch "$$SERVICE_ACCOUNT_JSON_FILE" ; \
	fi ; \
	find . | grep .build ; \
	docker build \
	    --build-arg SERVICE_ACCOUNT_JSON_FILE="$$SERVICE_ACCOUNT_JSON_FILE" \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/dev" \
	    -f marketplace/dev/Dockerfile \
	    . ; \
	rm "$$SERVICE_ACCOUNT_JSON_FILE"
	@touch "$@"


.build/marketplace/deployer: | .build/marketplace
	mkdir -p "$@"


.build/marketplace/deployer/envsubst: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                                      $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_envsubst_base/* \
                                      .build/marketplace/delete_deprecated \
                                      | .build/marketplace/deployer
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst" \
	    -f marketplace/deployer_envsubst_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/deployer/helm: $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_util/* \
                                  $(MARKETPLACE_TOOLS_PATH)/marketplace/deployer_helm_base/* \
                                  .build/marketplace/delete_deprecated \
                                  | .build/marketplace/deployer
	$(call print_target)
	cd $(MARKETPLACE_TOOLS_PATH) \
	&& docker build \
	    --tag "gcr.io/cloud-marketplace-tools/k8s/deployer_helm" \
	    -f marketplace/deployer_helm_base/Dockerfile \
	    .
	@touch "$@"


.build/marketplace/delete_deprecated: | .build/marketplace
# For BSD compatibility, we can't use xargs -r.
	@ \
	for image in $$(docker images --format '{{.Repository}}' \
	    | sort | uniq \
	    | grep 'gcr.io/google-marketplace-tools/'); do \
	  printf "\n\033[93m\033[1m$${image} is DEPRECATED. Please update your Dockerfile\033[0m\n\n"; \
	done
	@ \
	for image in $$(docker images --format '{{.Repository}}:{{.Tag}}' \
	    | grep 'gcr.io/google-marketplace-tools/' \
	    | grep -v -e '<[Nn]one>'); do \
	  docker rmi "$${image}"; \
	done
	@touch "$@"


endif
