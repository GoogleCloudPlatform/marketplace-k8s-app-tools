ifndef __APP_MAKEFILE__

__APP_MAKEFILE__ := included


makefile_dir := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
include $(makefile_dir)/common.Makefile
include $(makefile_dir)/marketplace.Makefile
include $(makefile_dir)/var.Makefile


# Extracts the name property from APP_PARAMETERS.
define name_parameter
$(shell echo '$(APP_PARAMETERS)' \
    | docker run -i --entrypoint=/bin/print_config.py --rm $(APP_DEPLOYER_IMAGE) --values_mode stdin --xtype NAME)
endef


# Extracts the namespace property from APP_PARAMETERS.
define namespace_parameter
$(shell echo '$(APP_PARAMETERS)' \
    | docker run -i --entrypoint=/bin/print_config.py --rm $(APP_DEPLOYER_IMAGE) --values_mode stdin --xtype NAMESPACE)
endef


# Combines APP_PARAMETERS and APP_TEST_PARAMETERS.
define combined_parameters
$(shell echo '$(APP_PARAMETERS)' '$(APP_TEST_PARAMETERS)' \
    | docker run -i --entrypoint=/usr/bin/jq --rm $(APP_DEPLOYER_IMAGE) -s '.[0] * .[1]')
endef


##### Tools development targets #####


.build/app: | .build
	mkdir -p "$@"


.build/app/base_deployer: | .build/app
	mkdir -p "$@"


##### Tools development targets #####


# Your deployer target should depend on the appropriate
# .build/app/base_deployer/* if you're modifying the
# tools (i.e. base deployer) code. Your deployer's Dockerfile
# should also use a FROM base image with the right tag.
# Easiest to have this FROM line:
#
# ARG MARKETPLACE_TOOLS_TAG
# FROM gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$MARKETPLACE_TOOLS_TAG
#
# Then your deployer make target looks like this:
#
# .build/deployer: .build/var/MARKETPLACE_TOOLS_TAG \
#                  .build/app/base_deployer/helm
#     docker build \
#         --build-arg MARKETPLACE_TOOLS_TAG=$(MARKETPLACE_TOOLS_TAG) \
#         ...


.build/app/base_deployer/envsubst: .build/var/MARKETPLACE_TOOLS_TAG \
                                   | .build/app/base_deployer
	$(call print_target)
	@ if [[ -z "$$(docker image ls -q "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)")" ]]; then \
	  if ! docker pull "gcr.io/cloud-marketplace-tools/k8s/deployer_envsubst:$(MARKETPLACE_TOOLS_TAG)" 2> /dev/null; then \
	    make .build/marketplace/deployer/envsubst; \
	  fi; \
	fi
	@touch "$@"


.build/app/base_deployer/helm: .build/var/MARKETPLACE_TOOLS_TAG \
                               | .build/app/base_deployer
	$(call print_target)
	@ if [[ -z "$$(docker image ls -q "gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)")" ]]; then \
	  if ! docker pull "gcr.io/cloud-marketplace-tools/k8s/deployer_helm:$(MARKETPLACE_TOOLS_TAG)" 2> /dev/null; then \
	    make .build/marketplace/deployer/helm; \
	  fi; \
	fi
	@touch "$@"


.build/app/base_deployer/helm_onbuild: .build/var/MARKETPLACE_TOOLS_TAG \
                                       | .build/app/base_deployer
	$(call print_target)
	@ if [[ -z "$$(docker image ls -q "gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild:$(MARKETPLACE_TOOLS_TAG)")" ]]; then \
	  if ! docker pull "gcr.io/cloud-marketplace-tools/k8s/deployer_helm/onbuild:$(MARKETPLACE_TOOLS_TAG)" 2> /dev/null; then \
	    make .build/marketplace/deployer/helm; \
	  fi; \
	fi
	@touch "$@"


#####################################


.build/app/dev: .build/var/MARKETPLACE_TOOLS_TAG \
              | .build/app
	$(call print_target)
	@ if [[ -z "$$(docker image ls -q "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)")" ]]; then \
	  if ! docker pull "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" 2> /dev/null; then \
	    make .build/marketplace/dev; \
	  fi; \
	fi
	docker run \
	    "gcr.io/cloud-marketplace-tools/k8s/dev:$(MARKETPLACE_TOOLS_TAG)" \
	    cat /scripts/dev > "$@"
	chmod a+x "$@"


.PHONY: app/phony
app/phony: ;


########### Main  targets ###########


# Builds the application containers and push them to the registry.
# Including Makefile can extend this target. This target is
# a prerequisite for install.
.PHONY: app/build
app/build:: ;


# Installs the application into target namespace on the cluster.
.PHONY: app/install
app/install:: app/build \
              .build/var/APP_DEPLOYER_IMAGE \
              .build/var/APP_PARAMETERS \
              .build/var/HOME \
              .build/var/MARKETPLACE_TOOLS_TAG \
              | .build/app/dev
	$(call print_target)
	.build/app/dev \
	    /scripts/install \
	        --deployer='$(APP_DEPLOYER_IMAGE)' \
	        --parameters='$(APP_PARAMETERS)' \
	        --entrypoint="/bin/deploy.sh"


# Installs the application into target namespace on the cluster.
.PHONY: app/install-test
app/install-test:: app/build \
                   .build/var/APP_DEPLOYER_IMAGE \
                   .build/var/APP_PARAMETERS \
                   .build/var/APP_TEST_PARAMETERS \
                   .build/var/HOME \
                   .build/var/MARKETPLACE_TOOLS_TAG \
	           | .build/app/dev
	$(call print_target)
	.build/app/dev \
	    /scripts/install \
	        --deployer='$(APP_DEPLOYER_IMAGE)' \
	        --parameters='$(call combined_parameters)' \
	        --entrypoint="/bin/deploy_with_tests.sh"


# Uninstalls the application from the target namespace on the cluster.
.PHONY: app/uninstall
app/uninstall: .build/var/APP_DEPLOYER_IMAGE \
               .build/var/APP_PARAMETERS
	$(call print_target)
	kubectl delete 'application/$(call name_parameter)' \
	    --namespace='$(call namespace_parameter)' \
	    --ignore-not-found


# Runs the verification pipeline.
.PHONY: app/verify
app/verify: app/build \
            .build/var/APP_DEPLOYER_IMAGE \
            .build/var/APP_PARAMETERS \
            .build/var/APP_TEST_PARAMETERS \
            .build/var/HOME \
            .build/var/MARKETPLACE_TOOLS_TAG \
            | .build/app/dev
	$(call print_target)
	.build/app/dev \
	    /scripts/verify \
	          --deployer='$(APP_DEPLOYER_IMAGE)' \
	          --parameters='$(call combined_parameters)'


endif
