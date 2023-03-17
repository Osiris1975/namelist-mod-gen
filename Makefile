WORKSPACE?=${shell pwd}
PYEXE?=python3

.PHONY: mod_deployable
mod_deployable: clean
	zip -r deployables/osiris_namelists_v4.0.0.zip src/namelist_mod_gen/generated_mods/osiris_namelists -x "*.DS_Store"

.PHONY: build_osiris
build_osiris:
	${PYEXE} src/namelist_mod_gen/namelist_mod_gen.py -n examples/input_csvs/osiris_namelists  -m osiris_namelists -a osiris

.PHONY: clean
clean:
	rm -f deployables/osiris_namelists.zip
	rm -rf src/namelist_mod_gen/generated_mods/osiris_namelists

build:
	python3 build
release: clean build_osiris mod_deployable