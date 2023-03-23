WORKSPACE?=${shell pwd}
PYEXE?=python3

.PHONY: mod_deployable
mod_deployable:
	zip -r deployables/osiris_namelists_v5.0.0.zip generated_mods/osiris_namelists -x "*.DS_Store"

.PHONY: build_osiris
build_osiris:
	${PYEXE} src/namelist_mod_gen/namelist_mod_gen.py -c examples/input_csvs/osiris_namelists  -m osiris_namelists -a osiris

.PHONY: clean
clean:
	rm -f deployables/osiris_namelists.zip
	rm -rf generated_mods/osiris_namelists

release: build_osiris mod_deployable