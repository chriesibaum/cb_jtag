
BUILD_DIR := ./dist

COV_RESULT:= ./reports/junit/junit.xml
COV_REPORT:= ./reports/coverage_html/index.html ./reports/coverage/coverage.xml
DOC_BADGES:= ./doc/tests-badge.svg ./doc/coverage-badge.svg

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

doc: badges

.PHONY: test
test: $(COV_RESULT)
$(COV_RESULT):
	@$(E) "running tests..."
	coverage run    -m pytest -v -rP ./test/test_0_cb_bit.py			 --junit-xml=./reports/junit/junit.xml
	coverage run -a -m pytest -v -rP ./test/test_cb_jtag_probe.py		 --junit-xml=./reports/junit/junit.xml
	coverage run -a -m pytest -v -rP ./test/test_0_nucleo_G474RE.py		 --junit-xml=./reports/junit/junit.xml

cov_report: $(COV_REPORT)
$(COV_REPORT): $(COV_RESULT)
	coverage report -m
	coverage html -d ./reports/coverage_html
	coverage xml -o ./reports/coverage/coverage.xml

badges: $(DOC_BADGES)
$(DOC_BADGES): $(COV_RESULT) $(COV_REPORT)
	@echo "Generating coverage badge..."
	@genbadge tests --output-file ./doc/tests-badge.svg
	@genbadge coverage --output-file ./doc/coverage-badge.svg

build:
	$(HATCH) build


install: build
	@uv pip install dist/cb_jtag*.whl --force-reinstall


deploy: build
	$(E) Uploading package to PyPI...
	twine upload dist/*


clean:
	@$(E) "cleaning up..."
	@rm -rf ./__pycache__
	@rm -rf ./*/__pycache__
	@rm -rf ./htmlcov
	@rm -rf ./reports/
	@rm -f ./.coverage

mr_proper: clean
	@$(E) "cleaning up using Mr. Proper..."
	@rm -rf ./$(BUILD_DIR)

venv_clean:
	@$(E) "cleaning up virtual environment..."
	@rm -rf .venv