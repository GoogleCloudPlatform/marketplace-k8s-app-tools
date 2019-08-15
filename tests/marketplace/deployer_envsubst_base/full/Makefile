TAG ?= latest

# Convenience makefiles.
include gcloud.Makefile
include var.Makefile

# app.Makefile provides the main targets for installing the
# application.
# It requires several APP_* variables defined as followed.
include app.Makefile

APP_DEPLOYER_IMAGE ?= $(REGISTRY)/example/wordpress/deployer:$(TAG)
NAME ?= wordpress-1
APP_PARAMETERS ?= { \
  "name": "$(NAME)", \
  "namespace": "$(NAMESPACE)", \
  "imageWordpress": "$(REGISTRY)/example/wordpress:$(TAG)", \
  "imageInit": "$(REGISTRY)/example/wordpress/init:$(TAG)", \
  "imageMysql": "$(REGISTRY)/example/wordpress/mysql:$(TAG)", \
  "imageUbbagent": "$(REGISTRY)/example/wordpress/ubbagent:$(TAG)", \
  "reportingSecret": "gs://cloud-marketplace-ops-test-kokoro/reporting_secrets/wordpress.yaml" \
}
TESTER_IMAGE ?= $(REGISTRY)/example/wordpress/tester:$(TAG)

# Extend the target as defined in app.Makefile to
# include real dependencies.
app/build:: .build/wordpress/deployer \
            .build/wordpress/init \
            .build/wordpress/mysql \
            .build/wordpress/tester \
            .build/wordpress/ubbagent \
            .build/wordpress/wordpress


.build/wordpress: | .build
	mkdir -p "$@"

.build/wordpress/deployer: .build/var/APP_DEPLOYER_IMAGE \
                           .build/var/MARKETPLACE_TOOLS_TAG \
                           .build/var/REGISTRY \
                           .build/var/TAG \
                           apptest/deployer/* \
                           apptest/deployer/manifest/* \
                           deployer/* \
                           manifest/* \
                           schema.yaml \
                           | .build/wordpress
	$(call print_target, $@)
	docker build \
	    --build-arg REGISTRY="$(REGISTRY)/example/wordpress" \
	    --build-arg TAG="$(TAG)" \
	    --build-arg MARKETPLACE_TOOLS_TAG="$(MARKETPLACE_TOOLS_TAG)" \
	    --tag "$(APP_DEPLOYER_IMAGE)" \
	    -f deployer/Dockerfile \
	    .
	docker push "$(APP_DEPLOYER_IMAGE)"
	@touch "$@"


.build/wordpress/tester: .build/var/TESTER_IMAGE
	$(call print_target, $@)
	docker pull cosmintitei/bash-curl
	docker tag cosmintitei/bash-curl "$(TESTER_IMAGE)"
	docker push "$(TESTER_IMAGE)"
	@touch "$@"

# Simulate building of primary app image. Actually just copying public image to
# local registry.
.build/wordpress/wordpress: .build/var/REGISTRY \
                            .build/var/TAG \
                            | .build/wordpress
	$(call print_target, $@)
	docker pull launcher.gcr.io/google/wordpress4-php5-apache
	docker tag launcher.gcr.io/google/wordpress4-php5-apache "$(REGISTRY)/example/wordpress:$(TAG)"
	docker push "$(REGISTRY)/example/wordpress:$(TAG)"
	@touch "$@"

# Build secondary app image.
.build/wordpress/init: init/* \
                       .build/var/REGISTRY \
                       .build/var/TAG \
                       | .build/wordpress
	$(call print_target, $@)
	cd init \
	&& docker build --tag "$(REGISTRY)/example/wordpress/init:$(TAG)" .
	docker push "$(REGISTRY)/example/wordpress/init:$(TAG)"
	@touch "$@"

# Relocate public mysql image to $REGISTRY.
.build/wordpress/mysql: .build/var/REGISTRY \
                        .build/var/TAG \
                        | .build/wordpress
	$(call print_target, $@)
	docker pull launcher.gcr.io/google/mysql5
	docker tag launcher.gcr.io/google/mysql5 "$(REGISTRY)/example/wordpress/mysql:$(TAG)"
	docker push "$(REGISTRY)/example/wordpress/mysql:$(TAG)"
	@touch "$@"

# Relocate ubbagent image to $REGISTRY.
.build/wordpress/ubbagent: .build/var/REGISTRY \
                           .build/var/TAG \
                           | .build/wordpress
	$(call print_target, $@)
	docker pull "gcr.io/cloud-marketplace-tools/metering/ubbagent:sha_dfb8b727bd23a7e48b6b4904f4fa2aad43634607"
	docker tag "gcr.io/cloud-marketplace-tools/metering/ubbagent:sha_dfb8b727bd23a7e48b6b4904f4fa2aad43634607" "$(REGISTRY)/example/wordpress/ubbagent:$(TAG)"
	docker push "$(REGISTRY)/example/wordpress/ubbagent:$(TAG)"
	@touch "$@"
