# Provides a class of targets that trigger rebuilds when variables change.
#
# Usage:
#
# .build/my_container: .build/var/REGISTRY
#
.PHONY: var-init
var-init:
	@mkdir -p .build/var/

.build/var/%: .build/var/%-phony ;

.build/var/%-phony: var-init
	@var_key=$* ; \
	var_val=${${*}} ; \
	var_val_old=$$(cat ".build/var/$$var_key" 2> /dev/null) ; \
	if [ "$$var_val" != "$$var_val_old" ]; then \
	  echo '======================= UPDATING =======================' ; \
	  echo -n "$$var_val" > .build/var/$$var_key ; \
	fi
