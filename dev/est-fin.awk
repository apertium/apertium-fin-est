BEGIN { FS="\t"; }
$3 == "V" { printf("    <e><p><l>%s<s n=\"vblex\"/><r>%s<s n=\"vblex\"/></r></p></e>\n", $2, $4); }
$3 == "D" { printf("    <e><p><l>%s<s n=\"part\"/><r>%s<s n=\"part\"/></r></p></e>\n", $2, $4); }
$3 == "A" { printf("    <e><p><l>%s<s n=\"adj\"/><r>%s<s n=\"adj\"/></r></p></e>\n", $2, $4); }
$3 == "P" { printf("    <e><p><l>%s<s n=\"pron\"/><r>%s<s n=\"pron\"/></r></p></e>\n", $2, $4); }
$3 == "S" { printf("    <e><p><l>%s<s n=\"n\"/><r>%s<s n=\"n\"/></r></p></e>\n", $2, $4); }

