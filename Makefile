#!/usr/bin/make
PY_COV=python3-coverage
PYTEST=pytest-3
REFDIR=tests/reference/6/
GOOD=tests/kicad6/good-project/good-project.kicad_pcb
REFILL=tests/kicad6/zone-refill/zone-refill.kicad_pcb
GOOD_SCH=tests/kicad6/good-project/good-project.kicad_sch
CWD := $(abspath $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST))))))
USER_ID=$(shell id -u)
GROUP_ID=$(shell id -g)

deb:
	fakeroot dpkg-buildpackage -uc -b

deb_sig:
	fakeroot dpkg-buildpackage -b

deb_clean:
	fakeroot debian/rules clean
	-@rm -rf kiauto.egg-info

lint:
	# flake8 --filename is broken
	ln -sf src/eeschema_do eeschema_do.py
	ln -sf src/pcbnew_do pcbnew_do.py
	# stop the build if there are Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --statistics
	rm eeschema_do.py pcbnew_do.py

test_server_ki5:
	python3-coverage erase
	pytest-3 --test_dir output
	python3-coverage report

test_server_ki6:
	python3-coverage erase
	pytest-3 --test_dir output
	python3-coverage report

test_server_ki7:
	python3-coverage erase
	pytest-3 --test_dir output
	python3-coverage report

test_server_ki8:
	python3-coverage erase
	pytest-3 --test_dir output
	python3-coverage report

test_server_nightly:
	python3-coverage erase
	KIAUS_USE_NIGHTLY=7.0 pytest-3 --test_dir output
	python3-coverage report

test: lint
	rm -rf output
	$(PY_COV) erase
#	KIAUTO_INTERPOSER_DISABLE=1 KIAUS_USE_NIGHTLY=7.0 $(PYTEST) --test_dir output
	$(PYTEST) --test_dir output
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html
	-@rm -rf tests/kicad6/kicad4-project/kicad4-project-rescue.lib tests/kicad6/kicad4-project/kicad4-project.kicad_prl \
		tests/kicad6/kicad4-project/kicad4-project.kicad_pro tests/kicad6/kicad4-project/kicad4-project.kicad_sch \
		tests/kicad6/kicad4-project/kicad4-project.pro-bak tests/kicad6/kicad4-project/rescue-backup/ \
		tests/kicad6/kicad4-project/sym-lib-table

test_docker_local:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:latest \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad5/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

t1k5: test_docker_local_1

t1k5ni: test_docker_local_1_ni

test_docker_local_1:
	rm -rf output
	#$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	# KIAUTO_INTERPOSER_DISABLE=1
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki5 \
		/bin/bash -c "$(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad5/ .coverage"
	#$(PY_COV) report
	#$(PY_COV) html
	#rm .coverage

test_docker_local_1_ni:
	rm -rf output
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki5 \
		/bin/bash -c "export KIAUTO_INTERPOSER_DISABLE=1; $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad5/ .coverage"

test_docker_local_k6:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki6 \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad6/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html

test_docker_local_k6_1:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki6 \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad6/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	rm .coverage

test_docker_local_k6_1_ni:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki6 \
		/bin/bash -c "export KIAUTO_INTERPOSER_DISABLE=1; $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad6/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	rm .coverage

t1k6: test_docker_local_k6_1

t1k6ni: test_docker_local_k6_1_ni

test_docker_local_k7:
	rm -rf output
	$(PY_COV) erase
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki7 \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad6/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	rm .coverage

test_docker_local_k8:
	rm -rf output
	$(PY_COV) erase
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki8 \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad*/ .coverage.*"
	$(PY_COV) report
	$(PY_COV) html
	rm .coverage.*

test_docker_local_k7_1:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki7 \
		/bin/bash -c "flake8 . --count --statistics ; $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad7/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	rm .coverage

t1k7: test_docker_local_k7_1

test_docker_local_k8_1:
	rm -rf output
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki8 \
		/bin/bash -c "$(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad8/ .coverage.*"
	rm .coverage.*

# t1k8: test_docker_local_k8_1

test_docker_local_k8_1_ni:
	rm -rf output
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" ghcr.io/inti-cmnb/kicad_auto_test:ki8 \
		/bin/bash -c "export KIAUTO_INTERPOSER_DISABLE=1; $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/kicad8/ .coverage.*"
	rm .coverage.*

t1k8ni: test_docker_local_k8_1_ni

test_docker_local_ng:
	rm -rf output
	$(PY_COV) erase
	# Run in the same directory to make the __pycache__ valid
	# Also change the owner of the files to the current user (we run as root like in GitHub)
#	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:nightly \
#		/bin/bash -c "flake8 . --count --statistics ; KIAUS_USE_NIGHTLY=6.0 $(PYTEST) --log-cli-level debug -k '$(SINGLE_TEST)' --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage"
	docker run --rm -v $(CWD):$(CWD) --workdir="$(CWD)" setsoft/kicad_auto_test:nightly \
		/bin/bash -c "flake8 . --count --statistics ; KIAUS_USE_NIGHTLY=7.0 $(PYTEST) --log-cli-level debug --test_dir output ; chown -R $(USER_ID):$(GROUP_ID) output/ tests/ .coverage"
	$(PY_COV) report
	$(PY_COV) html
	x-www-browser htmlcov/index.html
	-@rm -rf tests/kicad6/kicad4-project/kicad4-project-rescue.lib tests/kicad6/kicad4-project/kicad4-project.kicad_prl \
		tests/kicad6/kicad4-project/kicad4-project.kicad_pro tests/kicad6/kicad4-project/kicad4-project.kicad_sch \
		tests/kicad6/kicad4-project/kicad4-project.pro-bak tests/kicad6/kicad4-project/rescue-backup/ \
		tests/kicad6/kicad4-project/sym-lib-table

docker_shell:
	docker run  -it --rm -v $(CWD):$(CWD) --workdir="$(CWD)" \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$(DISPLAY) \
	--user $(USER_ID):$(GROUP_ID) \
	--volume="/etc/group:/etc/group:ro" \
	--volume="/etc/passwd:/etc/passwd:ro" \
	--volume="/etc/shadow:/etc/shadow:ro" \
	--volume="/home/$(USER):/home/$(USER):rw" \
	setsoft/kicad_auto_test:latest /bin/bash

docker_shell_ng:
	docker run  -it --rm -v $(CWD):$(CWD) --workdir="$(CWD)" \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$(DISPLAY) \
	--user $(USER_ID):$(GROUP_ID) \
	--volume="/etc/group:/etc/group:ro" \
	--volume="/etc/passwd:/etc/passwd:ro" \
	--volume="/etc/shadow:/etc/shadow:ro" \
	--volume="/home/$(USER):/home/$(USER):rw" \
	setsoft/kicad_auto_test:nightly /bin/bash

docker_deb_shell:
	docker run  -it --rm -v $(CWD):$(CWD) --workdir="$(CWD)" \
	-v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$(DISPLAY) \
	--user $(USER_ID):$(GROUP_ID) \
	--volume="/etc/group:/etc/group:ro" \
	--volume="/etc/passwd:/etc/passwd:ro" \
	--volume="/etc/shadow:/etc/shadow:ro" \
	--volume="/home/$(USER):/home/$(USER):rw" \
	setsoft/kicad_pybuild:latest /bin/bash

gen1_ref:
	src/eeschema_do export --file_format ps --all $(GOOD_SCH) $(REFDIR)
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project.ps > $(REFDIR)good-project.ps.new
	mv $(REFDIR)good-project.ps.new $(REFDIR)good-project.ps
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project-logic.ps > $(REFDIR)good-project-logic.ps.new
	mv $(REFDIR)good-project-logic.ps.new $(REFDIR)good-project-logic.ps
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project-Power.ps > $(REFDIR)good-project-Power.ps.new
	mv $(REFDIR)good-project-Power.ps.new $(REFDIR)good-project-Power.ps

gen_ref:
	# Force using the default color scheme
	if [ -e $(HOME)/.config/kicad/7.0/colors ] && [ -e output $(HOME)/.config/kicad/7.0/colors.ok ] ; then rm -rf $(HOME)/.config/kicad/7.0/colors.ok; fi
	if [ -e $(HOME)/.config/kicad/7.0/colors ] ; then mv $(HOME)/.config/kicad/7.0/colors $(HOME)/.config/kicad/7.0/colors.ok; fi
	# Reference outputs, must be manually inspected if regenerated
	cp -a $(REFILL).refill $(REFILL)
	src/pcbnew_do export --output_name zone-refill.pdf $(REFILL) $(REFDIR) F.Cu B.Cu Edge.Cuts
	cp -a $(REFILL).ok $(REFILL)
	src/pcbnew_do export --output_name good_pcb_with_dwg.pdf $(GOOD) $(REFDIR) F.Cu F.SilkS Dwgs.User Edge.Cuts
	src/pcbnew_do export --output_name good_pcb_inners.pdf   $(GOOD) $(REFDIR) F.Cu F.SilkS GND.Cu Signal1.Cu Signal2.Cu Power.Cu Edge.Cuts
	src/pcbnew_do export --list $(GOOD) > $(REFDIR)good_pcb_layers.txt
	src/pcbnew_do export --mirror --scaling 4 --pads 0 --no-title --monochrome --separate --output_name good_pcb_sep_bn.pdf $(GOOD) $(REFDIR) F.Cu F.SilkS Dwgs.User Edge.Cuts
	src/pcbnew_do export --mirror --scaling 0 --pads 0 --no-title --monochrome --separate --output_name good_pcb_sep_bn_fit.pdf $(GOOD) $(REFDIR) F.Cu F.SilkS Dwgs.User Edge.Cuts
	src/eeschema_do export --file_format pdf --all $(GOOD_SCH) $(REFDIR)
	mv $(REFDIR)good-project.pdf $(REFDIR)good_sch_all.pdf
	src/eeschema_do export --file_format pdf $(GOOD_SCH) $(REFDIR)
	mv $(REFDIR)good-project.pdf $(REFDIR)good_sch_top.pdf
	src/eeschema_do export --file_format svg --all $(GOOD_SCH) $(REFDIR)
	# I really hate this, files has time stamps, 3 of them in fact, WHY ANOTHER INSIDE!!!
	sed -E 's/date .* <\/title>/DATE <\/title>/' $(REFDIR)good-project.svg > $(REFDIR)good-project.svg.new
	mv $(REFDIR)good-project.svg.new $(REFDIR)good-project.svg
	sed -E 's/date .* <\/title>/DATE <\/title>/' $(REFDIR)good-project-logic.svg > $(REFDIR)good-project-logic.svg.new
	mv $(REFDIR)good-project-logic.svg.new $(REFDIR)good-project-logic.svg
	sed -E 's/date .* <\/title>/DATE <\/title>/' $(REFDIR)good-project-Power.svg > $(REFDIR)good-project-Power.svg.new
	mv $(REFDIR)good-project-Power.svg.new $(REFDIR)good-project-Power.svg
	src/eeschema_do export --file_format ps --all $(GOOD_SCH) $(REFDIR)
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project.ps > $(REFDIR)good-project.ps.new
	mv $(REFDIR)good-project.ps.new $(REFDIR)good-project.ps
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project-logic.ps > $(REFDIR)good-project-logic.ps.new
	mv $(REFDIR)good-project-logic.ps.new $(REFDIR)good-project-logic.ps
	sed -E -e 's/^%%CreationDate: .*/%%CreationDate: DATE/' -e 's/^%%Title: .*/%%Title: TITLE/' $(REFDIR)good-project-Power.ps > $(REFDIR)good-project-Power.ps.new
	mv $(REFDIR)good-project-Power.ps.new $(REFDIR)good-project-Power.ps
	# Restore the colors scheme
	mv $(HOME)/.config/kicad/7.0/colors.ok $(HOME)/.config/kicad/7.0/colors

t1k8: single_test

single_test:
	-@rm .coverage
	rm -rf pp
	-$(PYTEST) --log-cli-level debug -k "$(SINGLE_TEST)" --test_dir pp
	@echo "********************" Output
	@cat pp/*/output.txt
	@echo "********************" Error
	@tail -n 30 pp/*/error.txt
	-@rm -rf tests/kicad6/kicad4-project/kicad4-project-rescue.lib tests/kicad6/kicad4-project/kicad4-project.kicad_prl \
		tests/kicad6/kicad4-project/kicad4-project.kicad_pro tests/kicad6/kicad4-project/kicad4-project.kicad_sch \
		tests/kicad6/kicad4-project/kicad4-project.pro-bak tests/kicad6/kicad4-project/rescue-backup/ \
		tests/kicad6/kicad4-project/sym-lib-table

.PHONY: deb deb_clean test lint test_local gen_ref test_docker_local single_test

