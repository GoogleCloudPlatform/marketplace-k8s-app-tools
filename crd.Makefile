ifndef __CRD_MAKEFILE__

__CRD_MAKEFILE__ := included

include common.Makefile

# Installs the application CRD on the cluster.
.PHONY: crd/install
crd/install:
	kubectl apply -f "crd/app-crd.yaml"
	kubectl apply -f "crd/kalm.yaml"

# Uninstalls the application CRD from the cluster.
.PHONY: crd/uninstall
crd/uninstall:
	kubectl delete -f "crd/app-crd.yaml"
	kubectl delete -f "crd/kalm.yaml"


endif
