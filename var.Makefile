ifndef __VAR_MAKEFILE__

__VAR_MAKEFILE__ := included

# Provides a class of targets that trigger rebuilds when variables change.
#
# Usage:
#
# .build/my_container: .build/var/REGISTRY
#
.PHONY: var/phony
var/phony: ;

.build/var:
	mkdir -p .build/var

.build/var/%: .build/var/%-phony ;

.build/var/%-phony: var/phony | .build/var .build/var/%-required
	@ \
	var_key="$*" ; \
	var_val="${$*}" ; \
	var_val_old=$$(cat ".build/var/$$var_key" 2> /dev/null) ; \
	if [ "$$var_val" != "$$var_val_old" ]; then \
	  echo -e "\033[93m\033[1m$$var_key has been updated.\033[0m" ; \
	  echo -e "\033[93m\033[1m  old value: $$var_val_old\033[0m" ; \
	  echo -e "\033[93m\033[1m  new value: $$var_val\033[0m" ; \
	  echo -n "$$var_val" > .build/var/$$var_key ; \
	fi

.build/var/%-required: var/phony
	@ \
	var_key="$*" ; \
	var_val="${$*}" ; \
	if [ "$$var_val" = "" ]; then \
	  echo -e "\n\e[91mMake variable '$*' is required.\e[39m\n"; \
	  exit 1; \
	fi

endif
