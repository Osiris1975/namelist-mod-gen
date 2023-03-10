# Osiris's Namelist Mod Generator & Osiris's Namelist Mod

This repository encompasses work to create a Stellaris namelist mod generator tool to facilitate the creation of 
Stellaris namelists and includes the first mod created with this too, Osiris's Namelist Mod.

The generator is a Python-based command line tool. It requires a csv file of names which it translates into the txt
and yml files in the proper directory structure. It doesn't completely generate the mod for you, but does the heavy 
lifting. See the Issues and Limitations section below for what it can't do for you. 

## Contributing Namelists to Osiris's Mod

The easiest way to contribute a namelist to the mod is to fill out the github issue for submitting namelists here:

[Osiris's Namelist Mod Contribution](https://github.com/Osiris1975/namelist-mod-gen/issues/new?assignees=Osiris1975&labels=contribution&template=osiris-s-namelist-contribution.md&title=)

## Creating Your Own Namelist Mod With the Generator Tool

Disclaimer: This tool is still under active development and extremely raw. The pace of development and improvements
will be dictated by interest outside of the author's usage.

### Features

* Creates namelists from one or more CSV files and produces a single mod for all the namelists. 
* Has resolved the %SEQ% issue introduced with Stellaris 3.6.0
* Write a blank csv template to fill out.

### Planned Features

* NSC Support
* Write a CSV from a given namelist text file. 

### Installing Python

The tool is written in Python and therefore requires Python on your computer. See the [Python Getting Started Page](https://www.python.org/about/gettingstarted/).

### Running the Tool

``` 
usage: namelist_generator.py -c [NAMELIST_FILE]

A tool for creating Stellaris namelist mods from a CSV file

options:
  -h, --help            show this help message and exit
  -c NAMELISTS, --namelists NAMELISTS
                        path to the directory with namelist csv files (default: None)
  -a AUTHOR, --author AUTHOR
                        mod author (default: None)
  -m MOD_NAME, --mod_name MOD_NAME
                        name to use for the generated mod (default: None)
  -d DUMP_CSV_TEMPLATE, --dump_csv_template DUMP_CSV_TEMPLATE
                        dump a blank csv with namelist headers with the specified name (default: None)

```

## Current Limitations and Issues

These are the known limitations and issues. Some may be addressed in the future.

* Does not create .mod files, you will have to do this yourself.
* Only creates English localization files.
* Hasn't been tested with sequential names other than $ORD$ yet. 


For issues, visit the [issues page](https://github.com/Osiris1975/namelist-mod-gen/issues) in this repository.



## Getting Help 

The best way is to [create an issue](https://github.com/Osiris1975/namelist-mod-gen/issues). You can also reach out
to [Osiris on Steam](https://steamcommunity.com/profiles/76561198007264573/). 

## Troubleshooting Tips for Name Lists

***Q: %SEQ Is showing up in my fleet and/or army names when I provide sequential names.*** 

A: Stellaris now expects namelists to use key value pairs that connect tne namelist in the `common` directory with
the associated yml file in the `localization` directory. If it fails to find the value associated with the key, it will display %SEQ%. This can happen for multiple reasons:
- The localization file with the key value pairs doesn't exist.
- The localization file is not in the correct directory (`<mod_root>/localisation/english/name_lists`).
- The keys in the namelist txt file don't match the keys in the localization file.
- The values in the localization file don't use supported sequence keys.
- The namelist and namelist localization file were NOT saved as UTF with BOM-8 encoding 
(Osiris's Namelist Mod Generator does this for you, but it can be done with Notepad++ as well from the encoding menu)

For a working example see the [Osiris's namelist mod files]().

***Q: My namelist title doesn't show up in the namelist picker when creating my empire, but instead shows up as `namelist_XXXX`***

A: This can also happen for multiple reasons related to Stellaris not finding or processing the file:
- The localization file isn't in the correct directory.
- You HAVE saved the file as UTF with BOM-8 encoding. Apparently the namelist picker in Stellaris does not like BOM-8.
