WORKSPACE?=${shell pwd}
PYEXE?=python3

.PHONY: mod_deployable
mod_deployable:
	zip -r deployables/osiris_namelists.zip src/namelist_mod_gen/generated_mods/osiris_namelists -x "*.DS_Store"

.PHONY: build_osiris
build_osiris:
	${PYEXE} src/namelist_mod_gen/namelist_mod_gen.py -c examples/osiris_namelists/input_csvs -m osiris_namelists -a osiris