# Osiris's Namelist Mod Generator (namelist-mod-gen)

This repository encompasses work to create a Stellaris namelist mod generator tool to facilitate the creation of 
Stellaris namelists. 

For an example of a namelist mod created with this tool see the following links:

[Osiris's Namelists for Stellaris @ GitHub](https://steamcommunity.com/sharedfiles/filedetails/?id=2936596940)

[Osiris's Namelists for Stellaris @ Steam](https://steamcommunity.com/sharedfiles/filedetails/?id=2936596940)

[Osiris's Namelists for Stellaris @ Paradox Plaza](https://forum.paradoxplaza.com/forum/threads/osiriss-namelists-for-stellaris.1570100/)

For information on the generator tool that made this mod, keep reading.


## Namelist Generator Tool

The generator is a Python-based command line tool. It requires a csv file of names which it converts into the txt
and yml files in the proper directory structure. It doesn't completely generate the mod for you, but does the heavy 
lifting. See the Issues and Limitations section below for what it can't do for you. 

## Features

* Creates namelists from one or more CSV files and produces a single mod for all the namelists. 
* Has resolved the %SEQ% issue introduced with Stellaris 3.6.0
* Write a blank csv template to fill out.
* Basic localization.
* Optional translation of localization. 




## Getting Started with Creating your own Namelist Mod 

Follow the steps below to create your own namelist mod.

### Installing Python

The tool is written in Python and therefore requires Python on your computer. See the [Python Getting Started Page](https://www.python.org/about/gettingstarted/).

### Installing Poetry

This tool uses [Poetry](https://python-poetry.org/docs/) for dependency management and packaging. See these [installation instructions](https://python-poetry.org/docs/#installation).

### Setting up Namelist Mod Gen

Once Poetry is installed, namelist-mod-gen(NMG) can bet setup with the following command:

`poetry install`

This will install any dependencies and setup a virtual environment to run the tool.

### Running the Tool

To print the basic usage, execute the following:

`./namelist_mod_gen.py --help`

or 

`poetry run python src/namelist_mod_gen/namelist_mod_gen.py --help`

#### Generating a CSV Template

The tool will generate a new CSV template that can be loaded into Google Sheets or Excel to populate a namelist with the following command:

```text
<root_directory>/namelist_mod_gen/namelist_mod_gen.py csv -d <desired_template_name.csv>
```

or 

```
poetry run python namelist_mod_gen/namelist_mod_gen.py csv -d  <desired_template_name.csv>
``` 

#### Generating Untranslated Namelist Mod Files

The fastest and most basic usage of NMG is to generate a mod from a directory of CSV files without translation. This can be done with the following command:

```text
<root_directory>/namelist_mod_gen/namelist_mod_gen.py mod -n </path/to/namelist/csv/dir/> -a <author_name> -m <mod_name>
```

or 

```text
poetry run python namelist_mod_gen/namelist_mod_gen.py mod -n </path/to/namelist/csv/dir/> -a <author_name> -m <mod_name>
``` 

This will build the mod directory structure, convert the CSV file into namelist files for each localisation, creating 
all files in the original english language for all language directories. This is the basic requirement for namelists
to appear for users of the mod from non-English locales. 

### Generating Translated Namelists

In order to translate namelists at no cost, NMG uses a multi-tiered cascading strategy with steps that 
execute in order as follows:

1. First, it checks a database for previously translated names to use for a given namelist.
2. Any remaining untranslated names for a particular namelist are then translated using Google's API. Most often this is enough to translate an entire namelist.
3. Should there be any more untranslated names, it then uses [MyMemory's API](https://mymemory.translated.net/). This service's free tier is capped at 5000 characters per day.
4. If any names still remain, the [Deepl Translation API](https://www.deepl.com/translator) is used. This service is capped at 500,000 characters per month and requires registration. Note you DO NOT have to use this. If the API key isn't present in the environment, this mode of translation will be skipped.
5. Any remaining untranslated texts are translated using [EasyNMT](https://github.com/UKPLab/EasyNMT), a machine-learning based translation tool. 

There are future plans to allow the order of these translations to be fully customizable as well as allow custom translators to be used. This work
is already in the design stage and will be created as a separate module from NMG that it will import.

### Translation Database Setup

NMG stores translated names in a postgres database in order to cache them for future use. If you do not have postgres
installed, see the following links for help:

[MacOS Homebrew Postgres Install Tutorial](https://wiki.postgresql.org/wiki/Homebrew) - Recommended method.
[MacOS Install Tutorial](https://www.postgresqltutorial.com/postgresql-getting-started/install-postgresql-macos/)
[Windows Install Tutorial](https://www.postgresqltutorial.com/postgresql-getting-started/install-postgresql/)

Once postgres is installed, we need to create a user and initialize a database. Run the following commands:

```text
>createuser nmg
>createdb translations -O nmg
```
This will create the user NMG uses as well as the database to store translations.


### Getting a DeepL Auth Key for DeepL Translation (optional)

In order for the tool to perform translations using DeepL, you will have to get an authentication key from their website.
A free option is available that allows 500,000 characters per month to be translated. 

Visit this link to sign up for an account:
[Deepl Website](https://www.deepl.com/translator)

Once you have an account you can find the authentication key at the bottom of the account summary page:
[Account Summary Page](https://www.deepl.com/account/summary)

The mod-gen tool expects to find this as an environment variable named `DEEPL_AUTH_KEY`. To set the environment variable, follow the links
below for your operating system:

[MacOS/Linux Environment Variable Instructions](https://tecadmin.net/setting-up-the-environment-variables-in-macos/)
[Windows Environment Variable Instructions](https://docs.oracle.com/en/database/oracle/machine-learning/oml4r/1.5.1/oread/creating-and-modifying-environment-variables-on-windows.html)

If this variable is not set, translation will still work, but it won't use DeepL as one of the sources for translation.

### Translation Mode

To generate translated namelists, run NMG as follows, adding `-t` or `--translate` to the earlier command:

```text
<root_directory>/namelist_mod_gen/namelist_mod_gen.py mod -n </path/to/namelist/csv/dir/> -a <author_name> -m <mod_name> -t
```

or 

```text
poetry run python namelist_mod_gen/namelist_mod_gen.py mod -n </path/to/namelist/csv/dir/> -a <author_name> -m <mod_name> -t
``` 

For an example of output generated by NMG using translation, visit the [Github repo for Osiris's Namelists for Stellaris](https://github.com/Osiris1975/osiris-namelists).


### NMG Command Line Options

There are a number of other command line options not explicitly introduced so far in this README. The full list of options can be seen with the following command:
```text
<root_directory>/namelist_mod_gen/namelist_mod_gen.py --help
```

or 

```text
poetry run python namelist_mod_gen/namelist_mod_gen.py --help
``` 
This will list the modes that NMG can run in. To get options for each mode, invoke the mode with a `--help` command, for example:
```text
<root_directory>/namelist_mod_gen/namelist_mod_gen.py mod --help
```

Details regarding the usage of each option will be printed.





## Current Limitations and Issues

These are the known limitations and issues. Some may be addressed in the future.

* Does not currently create mod descriptor files.
* Translation is still developmental. 
* Sometimes translators, especially machine learning ones, return nonsensical translations.

For issues, visit the [issues page](https://github.com/Osiris1975/namelist-mod-gen/issues) in this repository.

## Contributing Namelists to Osiris's Mod

The easiest way to contribute a namelist to the mod is to fill out the github issue for submitting namelists here:

[Osiris's Namelist Mod Contribution](https://github.com/Osiris1975/namelist-mod-gen/issues/new?assignees=Osiris1975&labels=contribution&template=osiris-s-namelist-contribution.md&title=)


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
