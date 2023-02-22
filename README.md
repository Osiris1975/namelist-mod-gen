# Osiris's Namelist Mod Generator and Osiris's Namelist Mod

This repository encompasses work to create a Stellaris namelist mod generator tool to facilitate the creation of 
Stellaris namelists and includes the first mod created with this too, Osiris's Namelist Mod.

The generator is a Python-based command line tool. It requires a csv file of names which it translates into the txt
and yml files in the proper directory structure. It doesn't completely generate the mod for you, but does the heavy 
lifting. See the Issues and Limitations section below for what it can't do for you. 

## Contributing Namelists to Osiris's Mod

The easiest way to contribute a namelist to the mod is to fill out the github issues for submitting namelists here:

[Osiris's Namelist Mod Contribution](https://github.com/Osiris1975/namelist-mod-gen/issues/new?assignees=Osiris1975&labels=contribution&template=osiris-s-namelist-contribution.md&title=)

## Creating Your Own Namelist Mod With the Generator Tool

Disclaimer: This tool is still under active development and extremely raw. The pace of development and improvements
will be dictated by interest outside of the author's usage.

## Installing Python

The tool is written in Python and therefore requires Python on your computer. See the [Python Getting Started Page](https://www.python.org/about/gettingstarted/).

## Running the Tool

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

## Issues and Limitations

For issues, visit the [issues page](https://github.com/Osiris1975/namelist-mod-gen/issues) in this repository.


## Getting Help 

The best way is to [create an issue](https://github.com/Osiris1975/namelist-mod-gen/issues). You can also reach out
to the author on Steam. 

