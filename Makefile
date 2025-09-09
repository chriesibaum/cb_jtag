
BUILD_DIR := ./dist

# tools
E := @echo
PYCODESTYLE := pycodestyle
PYCODESTYLE_FLAGS := --show-source --show-pep8 #--ignore=E501,E228,E722

AUTOPEP8 := autopep8
AUTOPEP8_FLAGS := --in-place

FLAKE8 := flake8
FLAKE8_FLAGS := --show-source  --ignore=E501,E228,E722

BANDIT := bandit
BANDIT_FLAGS := --format custom --msg-template \
    "{abspath}:{line}: {test_id}[bandit]: {severity}: {msg}"


HATCH := hatch



all:



test:
	pytest -v -rP


build:
	$(HATCH) build


install: build
	@pip install dist/cb_jtag*.whl --force-reinstall


clean:
	@rm -rf __pycache__
	@rm -rf */__pycache__

mr_proper: clean
	@rm -rf ./$(BUILD_DIR)