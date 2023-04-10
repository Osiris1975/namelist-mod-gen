# Osiris's Namelist Mod Generator & Osiris's Namelist Mod

NOTE: DOCUMENTATION IS OUT OF DATE AS OF 4/10/2023! WILL BE UPDATED SOON WITH TRANSLATION INSTRUCTIONS!

This repository encompasses work to create a Stellaris namelist mod generator tool to facilitate the creation of 
Stellaris namelists and includes the first mod created with this too, Osiris's Namelist Mod.

For information on the mod itself, check out the listings on Steam or Paradox Plaza (this version is only updated on major releases):

[Osiris's Namelists for Stellaris @ Steam](https://steamcommunity.com/sharedfiles/filedetails/?id=2936596940)

[Osiris's Namelists for Stellaris @ Paradox Plaza](https://forum.paradoxplaza.com/forum/threads/osiriss-namelists-for-stellaris.1570100/)

For information on the generator tool that made this mod, keep reading.

## Contributing Namelists to Osiris's Mod

The easiest way to contribute a namelist to the mod is to fill out the github issue for submitting namelists here:

[Osiris's Namelist Mod Contribution](https://github.com/Osiris1975/namelist-mod-gen/issues/new?assignees=Osiris1975&labels=contribution&template=osiris-s-namelist-contribution.md&title=)



## Namelist Generator Tool

The generator is a Python-based command line tool. It requires a csv file of names which it translates into the txt
and yml files in the proper directory structure. It doesn't completely generate the mod for you, but does the heavy 
lifting. See the Issues and Limitations section below for what it can't do for you. 

## Features

* Creates namelists from one or more CSV files and produces a single mod for all the namelists. 
* Has resolved the %SEQ% issue introduced with Stellaris 3.6.0
* Write a blank csv template to fill out.
* Basic localization.
* Optional translation of localization. 

## Planned Features

* Write a CSV from a given namelist text file to allow other existing mods to update to the most recent format and perform either basic or translated localization on their mods automatically.

## Getting Started with Creating your own Namelist Mod 

Follow the steps below to create your own namelist mod.

### Installing Python

The tool is written in Python and therefore requires Python on your computer. See the [Python Getting Started Page](https://www.python.org/about/gettingstarted/).

### Installing Poetry

This tool uses [Poetry](https://python-poetry.org/docs/) for dependency management and packaging. See these [installation instructions](https://python-poetry.org/docs/#installation).

### Setting up Namelist Mod Gen

Once Poetry is installed, namelist-mod-gen can bet setup with the following command:

`poetry install`

This will install any dependencies and setup a virtual environment to run the tool.

### Running the Tool

To print the basic usage, execute the following:

`./namelist_mod_gen.py --help`

or 

`poetry run python src/namelist_mod_gen/namelist_mod_gen.py --help`

#### Generating a CSV Template

The tool will generate a new CSV template that can be loaded into Google Sheets or Excel to populate a namelist with the following command:

`./namelist_mod_gen.py -d <your_csv_template.csv>`

or 

`poetry run python src/namelist_mod_gen/namelist_mod_gen.py -d  <your_csv_template.csv>`

#### Generating the Namelist Mod Files

To generate namelist mod files, execute the following:

`./namelist_mod_gen.py -c </path/to/csv/directory> -m <mod_name> -a <author_name>`

`-n/--namelists`: This specifies the full path to the directory that contains the CSV files to convert into namelists.
There are some CSV example files in `examples/input_csvs/osiris_namelists`

`-m/--mod_name`: This specifies the mod name that will be used in naming files.

`-M/--multiprocess`: Run in multiprocessing mode. This is experimental.

`-a/--author`: This specifies the creator of the namelist and is also used in specifying file names.  

`-t/--translate`: Runs the translation algorithm. See the next section below.

### Getting a DeepL Auth Key for DeepL Translation

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

When specifying `-t`, namelist-mod-gen will translate all the names provided in the CSV file to the languages supported
by Stellaris. Depending on the size and number of namelists used, this can take a very long time (many hours) 
the first time the words are translated.

One reason this takes as long as it does is because of the number of API requests to various translation services 
that are made, and in some cases the tool will generate a list of translations for a single word and pick the most common one
to get better accuracy. It does use a multi-threaded approach to try and improve translation time. If a word fails
to be translated, the tool will use the original english version for the localization file.

Once words are translated, they are stored in an SQLite database so subsequent runs will only translate new words and
phrases. 

In the future I hope to streamline the translation process and make it faster. 

## Current Limitations and Issues

These are the known limitations and issues. Some may be addressed in the future.

* Does not currently create mod descriptor files.
* Translation is still developmental. 
* Sometimes translators, especially machine learning ones, return nonsensical translations.

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
