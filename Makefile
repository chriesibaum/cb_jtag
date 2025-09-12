
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


.PHONY: test
test:
	@$(E) "running tests..."
# 	pytest -v -rP test/test_0.py::Test_Nucleo_G474RE
	coverage run    -m pytest -v -rP ./test/test_0_cb_bit.py
	coverage run -a -m pytest -v -rP ./test/test_cb_jtag_iface.py
	coverage run -a -m pytest -v -rP ./test/test_0_nucleo_G474RE.py

	# 	coverage run -m pytest -v -rP test/test_0_board_LPC1837.py

cov_report: test
	coverage report -m
	coverage html

build:
	$(HATCH) build


install: build
	@pip install dist/cb_jtag*.whl --force-reinstall


deploy: build
	$(E) Uploading package to PyPI...
	twine upload dist/*


clean:
	@$(E) "cleaning up..."
	@rm -rf ./__pycache__
	@rm -rf ./*/__pycache__
	@rm -rf ./htmlcov
	@rm -f ./.coverage


mr_proper: clean
	@rm -rf ./$(BUILD_DIR)