# Versioning

The generator and namelists follow semantic versioning. Read on to see how this applies to both.

## Generator 

Versioning follows <major>.<minor>.<patch> conventions. For the generator tool that means:

**major** Changes that impact the command-line execution of the tool, either by changing, adding, or removing flags or 
options. If these changes would require a change to the makefile, they are a major version.

**minor** Changes that add or remove output but don't change the command line arguments.

**patch** Changes that fix bugs but don't change output or input into the tool.

## Osiris's Namelist Mod

**major** Adding or removing columns to the csv file that generates the namelist.
**minor** Adding or removing data to existing columns in the csv file.
**patch** Fixing data in existing columns but not adding or removing data. 

