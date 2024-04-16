.PHONY: help clean test install all init dev css js cog coverage
.DEFAULT_GOAL := dev
.PRECIOUS: requirements.%.in
.FORCE:

HOOKS=$(.git/hooks/pre-commit)
REQS=$(wildcard requirements.*.txt)

CSS_FILES:=$(shell find assets -name *.css)
COG_FILE:=.cogfiles

TS_FILES:=$(wildcard assets/typescript/**/*.ts)
JS_FILES:=$(patsubst %.ts,%.js,$(TS_FILES))

PYTHON_VERSION:=$(shell python --version | cut -d " " -f 2)
PIP_PATH:=.direnv/python-$(PYTHON_VERSION)/bin/pip
WHEEL_PATH:=.direnv/python-$(PYTHON_VERSION)/bin/wheel
PRE_COMMIT_PATH:=.direnv/python-$(PYTHON_VERSION)/bin/pre-commit
UV_PATH:=.direnv/python-$(PYTHON_VERSION)/bin/uv
COG_PATH:=.direnv/python-$(PYTHON_VERSION)/bin/cog
COGABLE_FILES:=$(shell find assets -maxdepth 4 -type f -exec grep -l "\[\[\[cog" {} \;)
MIGRATION_FILES:=$(shell ls -d -- **/migrations/*.py)
ESBUILD_PATH:=./node_modules/.bin/esbuild

help: ## Display this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.gitignore:
	curl -q "https://www.toptal.com/developers/gitignore/api/visualstudiocode,python,direnv" > $@

.git: .gitignore
	git init

.pre-commit-config.yaml: $(PRE_COMMIT_PATH) .git
	curl https://gist.githubusercontent.com/bengosney/4b1f1ab7012380f7e9b9d1d668626143/raw/.pre-commit-config.yaml > $@
	pre-commit autoupdate
	@touch $@

pyproject.toml:
	curl https://gist.githubusercontent.com/bengosney/f703f25921628136f78449c32d37fcb5/raw/pyproject.toml > $@
	@touch $@

requirements.%.txt: $(UV_PATH) pyproject.toml
	@echo "Builing $@"
	python -m uv pip compile --generate-hashes --extra $* $(filter-out $<,$^) > $@

requirements.txt: $(UV_PATH) pyproject.toml
	@echo "Builing $@"
	python -m uv pip compile --generate-hashes $(filter-out $<,$^) > $@

.direnv: .envrc $(UV_PATH) requirements.txt $(REQS)
	@echo "Installing $(filter-out $<,$^)"
	python -m uv pip sync requirements.txt $(REQS)
	@touch $@

.git/hooks/pre-commit: .git $(PRE_COMMIT_PATH) .pre-commit-config.yaml
	pre-commit install

.envrc:
	@echo "Setting up .envrc then stopping"
	@echo "layout python python3.12" > $@
	@touch -d '+1 minute' $@
	@false

$(PIP_PATH): .envrc
	@python -m ensurepip
	@python -m pip install --upgrade pip

$(WHEEL_PATH): $(PIP_PATH)
	@python -m pip install wheel

$(UV_PATH): $(PIP_PATH) $(WHEEL_PATH)
	@python -m pip install uv

$(PRE_COMMIT_PATH): $(PIP_PATH) $(WHEEL_PATH)
	@python -m pip install pre-commit

init: .envrc $(UV_PATH) requirements.dev.txt .direnv .git/hooks/pre-commit ## Initalise a enviroment
	@python -m pip install --upgrade pip

clean: ## Remove all build files
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	rm -rf .pytest_cache
	rm -f .testmondata
	rm -rf *.egg-info

cerberus_crm/static/css/%.min.css: assets/css/%.css $(CSS_FILES)
	npx lightningcss --minify --bundle --nesting --targets '>= 0.25%' $< -o $@
	@touch $@

css: cerberus_crm/static/css/main.min.css ## Build the css

watch-assets: ## Watch and build the css and js
	@echo "Watching scss"
	$(MAKE) css js
	@while inotifywait -qr -e close_write assets/; do \
		$(MAKE) css js; \
	done

install: $(UV_PATH) requirements.txt requirements.dev.txt ## Install development requirements (default)
	@echo "Installing $(filter-out $<,$^)"
	python -m uv pip sync $(filter-out $<,$^)

cerberus_crm/static/js/htmx.min.js:
	curl -sL https://unpkg.com/htmx.org > $@

$(ESBUILD_PATH): node_modules

cerberus_crm/static/js/%.min.js: assets/typescript/%.ts $(TS_FILES) $(ESBUILD_PATH)
	$(ESBUILD_PATH) $< --bundle --minify --sourcemap --outfile=$@

js: cerberus_crm/static/js/htmx.min.js cerberus_crm/static/js/alpine.min.js cerberus_crm/static/js/main.min.js ## Fetch and build the js

$(COG_PATH): $(UV_PATH) $(WHEEL_PATH)
	python -m uv pip install cogapp

$(COG_FILE): $(COGABLE_FILES)
	@find assets -maxdepth 4 -type f -exec grep -l "\[\[\[cog" {} \; > $@

$(COGABLE_FILES): .FORCE
	@cog -rc $@

cog: $(COG_PATH) $(COG_FILE) $(COGABLE_FILES) ## Run cog

db.sqlite3: .direnv $(MIGRATION_FILES)
	python manage.py migrate
	@touch $@

dev: .direnv db.sqlite3 cog css js ## Setup the project read for development

node_modules: package.json package-lock.json
	npm install
	@touch $@

lcov.info: .direnv cerberus/tests/test_*.py
	pytest --cov --cov-report=lcov:$@

coverage: lcov.info
