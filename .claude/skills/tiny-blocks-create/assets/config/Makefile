PWD := $(CURDIR)
ARCH := $(shell uname -m)
PLATFORM :=

ifeq ($(ARCH),arm64)
    PLATFORM := --platform=linux/amd64
endif

TTY := $(shell [ -t 0 ] && echo -it)

PHP_VERSION := $(shell sed -n 's/.*"php": *"^\([0-9]*\.[0-9]*\)".*/\1/p' composer.json)
IMAGE_VERSION := 1.0.0
PHP_IMAGE := gustavofreze/php:${PHP_VERSION}-cli-${IMAGE_VERSION}
WORKSPACE := /var/www/html

DOCKER_RUN = docker run ${PLATFORM} --rm ${TTY} --net=host -v ${PWD}:${WORKSPACE} ${PHP_IMAGE}

RESET := \033[0m
GREEN := \033[0;32m
YELLOW := \033[0;33m

.DEFAULT_GOAL := help

.PHONY: configure
configure: ## Configure development environment
	@${DOCKER_RUN} composer configure

.PHONY: configure-and-update
configure-and-update: ## Configure development environment and update dependencies
	@${DOCKER_RUN} composer configure-and-update

.PHONY: tests
tests: ## Run unit and mutation tests with coverage
	@${DOCKER_RUN} composer tests

.PHONY: test-file
test-file: ## Run tests for a specific file (usage: make test-file FILE=ClassNameTest)
	@${DOCKER_RUN} composer test-file ${FILE}

.PHONY: review
review: ## Run lint and static analysis
	@${DOCKER_RUN} composer review

.PHONY: show-reports
show-reports: ## Open coverage and mutation reports in the browser
	@sensible-browser reports/coverage/coverage-html/index.html reports/coverage/mutation-report.html

.PHONY: show-outdated
show-outdated: ## Show outdated direct dependencies
	@${DOCKER_RUN} composer outdated --direct

.PHONY: show-image
show-image: ## Show the pinned PHP tooling image
	@echo ${PHP_IMAGE}

.PHONY: clean
clean: ## Remove dependencies and generated artifacts
	@sudo chown -R ${USER}:${USER} ${PWD}
	@rm -rf reports vendor .phpunit.cache *.lock

.PHONY: help
help: ## Display this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "$$(printf '$(GREEN)')Setup$$(printf '$(RESET)')"
	@grep -E '^(configure|configure-and-update):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*? ## "}; {printf "$(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$$(printf '$(GREEN)')Testing$$(printf '$(RESET)')"
	@grep -E '^(tests|test-file):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$$(printf '$(GREEN)')Quality$$(printf '$(RESET)')"
	@grep -E '^(review):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$$(printf '$(GREEN)')Reports$$(printf '$(RESET)')"
	@grep -E '^(show-reports|show-outdated|show-image):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$$(printf '$(GREEN)')Cleanup$$(printf '$(RESET)')"
	@grep -E '^(clean):.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-25s$(RESET) %s\n", $$1, $$2}'
