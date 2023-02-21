# Documentation TBD pending interest


## Namelist Tips

Hypothesese:
1. All sequential names in the namelist file must reference a localization file. 

2. %SEQ% Error occurs when stellaris is unable to reference a localization file. The symptom of this is that 
the namelist in the picker will be the namelist ID in the namelist file and not the namelist title in the loc file. 

So if your namelist id is `jimbob_mynamelist` in the namelist file, then the key in the `namelist_l_english.yml` file 
should be `name_list_jimbob_mynamelist:0 "Jim Bob's Name List"` 


3. %SEQ% Errors can still occur even if the loc file is found. You will see %SEQ% for fleet names but the proper namelist title will show in the picker.
-changing the number after the : didn't fix it
-changing the order in the file didn't fix it
-removing the one that works and leaving the ones that didn't work in the master loc file didn't fix it, but i learned
that even though the title dissappeared as expected, the namelist's loc file was still found as the fleet names were still 
correct in the control case.

-saving as 8-bit with bom encoding fixed the egyptian namelist

Does it matter if loc namelist files are in loc/english vs loc/english/name_lists

## Namelist File Rules (apparently):
### namelist TXT files:
namelist txt file must go in `<mod dir>/common/namelists`. Example:
`<mod dir>/common/namelists/arabian.txt`
`<mod dir>/common/namelists/ancientegypt.txt`
`<mod dir>/common/namelists/astrosci.txt`

### localized namelist titles file:
file namelist title files must go in `<mod_dir>/localization/english/namelist` for titles to show up. Example:
`<mod dir>/localization/english/osiris_namelist_l_english.yml`

### localized objects namelist files:
these files must go in 
